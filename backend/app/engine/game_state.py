"""Game state machine for Werewolf AI Agents.

Pure logic — no database calls, no LLM calls.
Deterministic transitions between game phases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GamePhase(str, Enum):
    INIT = "INIT"
    MAYOR_CAMPAIGN = "MAYOR_CAMPAIGN"
    MAYOR_VOTE = "MAYOR_VOTE"
    NIGHT = "NIGHT"
    DAY_BID = "DAY_BID"
    DAY_SPEECH = "DAY_SPEECH"
    VOTE = "VOTE"
    GAME_OVER = "GAME_OVER"


# Deterministic phase ordering. After VOTE we loop back to NIGHT
# unless the game is over.
_PHASE_ORDER: list[GamePhase] = [
    GamePhase.INIT,
    GamePhase.MAYOR_CAMPAIGN,
    GamePhase.MAYOR_VOTE,
    GamePhase.NIGHT,
    GamePhase.DAY_BID,
    GamePhase.DAY_SPEECH,
    GamePhase.VOTE,
    # After VOTE -> either NIGHT (loop) or GAME_OVER
]

MAX_ROUNDS = 10
MAX_DEBATE_TURNS = 10


@dataclass
class PlayerInfo:
    """Minimal player record tracked by the state machine."""
    player_id: str
    role: str


@dataclass
class EliminatedPlayer:
    """Record of an eliminated player."""
    player_id: str
    role: str
    eliminated_round: int


@dataclass
class SeerResult:
    """A single seer investigation result."""
    target_id: str
    role: str
    round_number: int


class GameStateMachine:
    """Tracks and transitions the game through its phases.

    All data is kept in-memory — the caller is responsible for
    persisting to the database.
    """

    def __init__(
        self,
        players: list[PlayerInfo],
        max_rounds: int = MAX_ROUNDS,
    ) -> None:
        self.alive_players: list[str] = [p.player_id for p in players]
        self._player_roles: dict[str, str] = {
            p.player_id: p.role for p in players
        }
        self.current_round: int = 1
        self.current_phase: GamePhase = GamePhase.INIT
        self.mayor_id: str | None = None
        self.eliminated_players: list[EliminatedPlayer] = []
        self.debate_turn_count: int = 0
        self.winner: str | None = None
        self.max_rounds: int = max_rounds

        # Seer investigation history (populated externally after each night)
        self.seer_results: list[SeerResult] = []

    # ------------------------------------------------------------------
    # Phase transitions
    # ------------------------------------------------------------------

    def transition_to_next_phase(self) -> GamePhase:
        """Advance to the next phase following deterministic rules.

        Returns the new phase.
        """
        if self.current_phase == GamePhase.GAME_OVER:
            return GamePhase.GAME_OVER

        # Check win condition before every transition
        win = self.check_win_condition()
        if win is not None:
            self.winner = win
            self.current_phase = GamePhase.GAME_OVER
            return GamePhase.GAME_OVER

        phase = self.current_phase

        if phase == GamePhase.INIT:
            self.current_phase = GamePhase.MAYOR_CAMPAIGN

        elif phase == GamePhase.MAYOR_CAMPAIGN:
            self.current_phase = GamePhase.MAYOR_VOTE

        elif phase == GamePhase.MAYOR_VOTE:
            self.current_phase = GamePhase.NIGHT

        elif phase == GamePhase.NIGHT:
            self.current_phase = GamePhase.DAY_BID
            self.debate_turn_count = 0

        elif phase == GamePhase.DAY_BID:
            self.current_phase = GamePhase.DAY_SPEECH

        elif phase == GamePhase.DAY_SPEECH:
            self.debate_turn_count += 1
            if self.debate_turn_count >= MAX_DEBATE_TURNS:
                self.current_phase = GamePhase.VOTE
            else:
                # Loop back to bidding for the next speech
                self.current_phase = GamePhase.DAY_BID

        elif phase == GamePhase.VOTE:
            # After a vote round, check win condition again
            win = self.check_win_condition()
            if win is not None:
                self.winner = win
                self.current_phase = GamePhase.GAME_OVER
            elif self.current_round >= self.max_rounds:
                # BUG 6: Max rounds reached — mark as discarded, not
                # a default villager win.
                self.winner = self.check_win_condition() or "discarded"
                self.current_phase = GamePhase.GAME_OVER
            else:
                self.current_round += 1
                self.current_phase = GamePhase.NIGHT

        return self.current_phase

    # ------------------------------------------------------------------
    # Win / game-over checks
    # ------------------------------------------------------------------

    def is_game_over(self) -> bool:
        return self.current_phase == GamePhase.GAME_OVER

    def check_win_condition(self) -> str | None:
        """Return 'villagers', 'werewolves', or None."""
        alive_roles = [
            self._player_roles[pid]
            for pid in self.alive_players
            if pid in self._player_roles
        ]
        wolf_count = sum(1 for r in alive_roles if r == "werewolf")
        non_wolf_count = len(alive_roles) - wolf_count

        if wolf_count == 0:
            return "villagers"
        if wolf_count >= non_wolf_count:
            return "werewolves"
        return None

    # ------------------------------------------------------------------
    # Player elimination (called externally after night / vote)
    # ------------------------------------------------------------------

    def eliminate_player(self, player_id: str) -> None:
        """Remove a player from the alive list."""
        if player_id in self.alive_players:
            role = self._player_roles.get(player_id, "unknown")
            self.alive_players.remove(player_id)
            self.eliminated_players.append(
                EliminatedPlayer(
                    player_id=player_id,
                    role=role,
                    eliminated_round=self.current_round,
                )
            )
            # If the eliminated player was the mayor, clear mayor_id
            if self.mayor_id == player_id:
                self.mayor_id = None

    # ------------------------------------------------------------------
    # Agent-visible state
    # ------------------------------------------------------------------

    def get_state_for_agent(self, player_id: str) -> dict:
        """Return the game state visible to a specific player.

        - Werewolves see each other.
        - Seer sees past investigation results.
        - Everyone sees alive players, round, phase, mayor, eliminated
          (with roles revealed on elimination).
        """
        role = self._player_roles.get(player_id, "unknown")

        # Base state visible to everyone
        state: dict = {
            "player_id": player_id,
            "role": role,
            "current_round": self.current_round,
            "current_phase": self.current_phase.value,
            "alive_players": list(self.alive_players),
            "mayor_id": self.mayor_id,
            "eliminated_players": [
                {
                    "player_id": ep.player_id,
                    "role": ep.role,
                    "eliminated_round": ep.eliminated_round,
                }
                for ep in self.eliminated_players
            ],
            "debate_turn_count": self.debate_turn_count,
            "winner": self.winner,
        }

        # Role-specific private info
        if role == "werewolf":
            # Werewolves see their teammates
            teammates = [
                pid
                for pid, r in self._player_roles.items()
                if r == "werewolf" and pid != player_id and pid in self.alive_players
            ]
            state["werewolf_teammates"] = teammates

        elif role == "seer":
            # Seer sees all past investigation results
            state["seer_results"] = [
                {
                    "target_id": sr.target_id,
                    "role": sr.role,
                    "round_number": sr.round_number,
                }
                for sr in self.seer_results
            ]

        return state
