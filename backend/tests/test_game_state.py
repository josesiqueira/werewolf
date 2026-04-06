"""Tests UT-001 to UT-013 — Game State Machine."""

import pytest

from app.engine.game_state import (
    GamePhase,
    GameStateMachine,
    PlayerInfo,
    SeerResult,
)
from tests.conftest import P, FIXED_ROLES, make_players


# UT-001: Linear phase progression from INIT to NIGHT
class TestUT001:
    def test_linear_phase_progression(self, game_state):
        assert game_state.current_phase == GamePhase.INIT

        phase1 = game_state.transition_to_next_phase()
        assert phase1 == GamePhase.MAYOR_CAMPAIGN

        phase2 = game_state.transition_to_next_phase()
        assert phase2 == GamePhase.MAYOR_VOTE

        phase3 = game_state.transition_to_next_phase()
        assert phase3 == GamePhase.NIGHT

        assert game_state.current_round == 1


# UT-002: NIGHT -> DAY_BID resets debate_turn_count
class TestUT002:
    def test_night_to_day_bid_resets_debate_count(self, game_state):
        # Advance to NIGHT
        game_state.current_phase = GamePhase.NIGHT
        game_state.debate_turn_count = 7

        phase = game_state.transition_to_next_phase()
        assert phase == GamePhase.DAY_BID
        assert game_state.debate_turn_count == 0


# UT-003: DAY_SPEECH increments debate counter and loops back to DAY_BID
class TestUT003:
    def test_debate_loop_and_vote_at_max(self, game_state):
        game_state.current_phase = GamePhase.DAY_BID

        # Do 9 DAY_BID -> DAY_SPEECH -> DAY_BID cycles
        for i in range(9):
            game_state.transition_to_next_phase()  # DAY_BID -> DAY_SPEECH
            game_state.transition_to_next_phase()  # DAY_SPEECH -> DAY_BID

        assert game_state.current_phase == GamePhase.DAY_BID
        assert game_state.debate_turn_count == 9

        # 10th cycle: DAY_BID -> DAY_SPEECH
        game_state.transition_to_next_phase()
        assert game_state.current_phase == GamePhase.DAY_SPEECH

        # DAY_SPEECH -> VOTE (debate_turn_count reaches 10)
        phase = game_state.transition_to_next_phase()
        assert phase == GamePhase.VOTE


# UT-004: VOTE advances round counter and returns to NIGHT
class TestUT004:
    def test_vote_to_night_increments_round(self, game_state):
        game_state.current_phase = GamePhase.VOTE
        game_state.current_round = 1

        phase = game_state.transition_to_next_phase()
        assert phase == GamePhase.NIGHT
        assert game_state.current_round == 2


# UT-005: Max rounds cap sets status to "discarded"
class TestUT005:
    def test_max_rounds_discarded(self):
        # Use only players that keep the game going (1 wolf vs 2 villagers)
        players = [
            PlayerInfo(player_id=P[0], role="werewolf"),
            PlayerInfo(player_id=P[4], role="villager"),
            PlayerInfo(player_id=P[5], role="villager"),
        ]
        gs = GameStateMachine(players=players, max_rounds=3)
        gs.current_phase = GamePhase.VOTE
        gs.current_round = 3

        phase = gs.transition_to_next_phase()
        assert phase == GamePhase.GAME_OVER
        assert gs.winner == "discarded"


# UT-006: Win condition detected before phase transition halts game
class TestUT006:
    def test_win_condition_halts_game(self, game_state):
        game_state.current_phase = GamePhase.DAY_BID

        # Eliminate all wolves
        game_state.eliminate_player(P[0])
        game_state.eliminate_player(P[1])

        phase = game_state.transition_to_next_phase()
        assert phase == GamePhase.GAME_OVER
        assert game_state.winner == "villagers"


# UT-007: eliminate_player removes player and clears mayor
class TestUT007:
    def test_eliminate_player_clears_mayor(self, game_state):
        game_state.alive_players = [P[0], P[1], P[2]]
        game_state.mayor_id = P[1]

        game_state.eliminate_player(P[1])

        assert P[1] not in game_state.alive_players
        assert game_state.mayor_id is None
        assert game_state.eliminated_players[0].player_id == P[1]
        assert game_state.eliminated_players[0].eliminated_round == game_state.current_round


# UT-008: eliminate_player is idempotent
class TestUT008:
    def test_eliminate_player_idempotent(self, game_state):
        game_state.eliminate_player(P[4])
        game_state.eliminate_player(P[4])  # second call
        assert len(game_state.eliminated_players) == 1


# UT-009: get_state_for_agent — werewolf sees teammates
class TestUT009:
    def test_werewolf_sees_teammates(self, game_state):
        state = game_state.get_state_for_agent(P[0])
        assert state["werewolf_teammates"] == [P[1]]
        assert "seer_results" not in state


# UT-010: get_state_for_agent — seer sees investigation history
class TestUT010:
    def test_seer_sees_results(self, game_state):
        game_state.seer_results.append(
            SeerResult(target_id=P[1], role="werewolf", round_number=1)
        )

        seer_state = game_state.get_state_for_agent(P[2])
        assert seer_state["seer_results"] == [
            {"target_id": P[1], "role": "werewolf", "round_number": 1}
        ]

        villager_state = game_state.get_state_for_agent(P[4])
        assert "seer_results" not in villager_state


# UT-011: check_win_condition — wolves win at parity
class TestUT011:
    def test_wolves_win_at_parity(self):
        players = [
            PlayerInfo(player_id=P[0], role="werewolf"),
            PlayerInfo(player_id=P[1], role="werewolf"),
            PlayerInfo(player_id=P[4], role="villager"),
        ]
        gs = GameStateMachine(players=players)
        assert gs.check_win_condition() == "werewolves"


# UT-012: check_win_condition — villagers win when all wolves eliminated
class TestUT012:
    def test_villagers_win_no_wolves(self):
        players = [
            PlayerInfo(player_id=P[2], role="seer"),
            PlayerInfo(player_id=P[3], role="doctor"),
            PlayerInfo(player_id=P[4], role="villager"),
            PlayerInfo(player_id=P[5], role="villager"),
        ]
        gs = GameStateMachine(players=players)
        assert gs.check_win_condition() == "villagers"


# UT-013: check_win_condition — game continues when wolves are minority
class TestUT013:
    def test_game_continues_wolves_minority(self):
        players = [
            PlayerInfo(player_id=P[0], role="werewolf"),
            PlayerInfo(player_id=P[2], role="seer"),
            PlayerInfo(player_id=P[3], role="doctor"),
            PlayerInfo(player_id=P[4], role="villager"),
        ]
        gs = GameStateMachine(players=players)
        assert gs.check_win_condition() is None
