"""Game loop orchestrator — ties all engine modules together.

Task 10 — ``run_game`` executes a complete Werewolf game:
  1. Initialise game, assign roles, persist Player rows.
  2. Mayor election (campaign + vote).
  3. Loop up to 10 rounds: night -> day (bidding debate) -> vote.
  4. Track win conditions; mark game discarded after 10 rounds.
"""

from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.agent_interface import AgentInterface, AgentResponse
from app.engine.day import extract_mentions, select_speaker
from app.engine.game_state import GamePhase, GameStateMachine, PlayerInfo, SeerResult
from app.engine.mayor import handle_mayor_succession, run_mayor_election
from app.engine.night import resolve_night
from app.engine.roles import assign_roles, get_private_info
from app.engine.vote import check_win_condition, tally_votes

# Models — created by Agent A
from app.models.game import Game
from app.models.game_event import GameEvent
from app.models.night_action import NightAction
from app.models.player import Player
from app.models.turn import Turn
from app.models.vote import Vote

logger = logging.getLogger(__name__)

MAX_ROUNDS = 10
MAX_DEBATE_TURNS = 10
DEFAULT_PLAYER_COUNT = 7

# Character image pool — agents cycle through these
_CHARACTER_IMAGES = [f"portrait_{i}.png" for i in range(1, 11)]


# ---------------------------------------------------------------------------
# Helper: build alive-players list for check_win_condition
# ---------------------------------------------------------------------------

def _alive_player_dicts(
    alive_ids: list[str],
    role_assignments: dict[str, str],
) -> list[dict[str, str]]:
    """Return list of dicts with ``role`` key, as expected by
    ``check_win_condition``."""
    return [{"role": role_assignments[pid]} for pid in alive_ids]


# ---------------------------------------------------------------------------
# Helper: build the public game-state dict consumed by agents
# ---------------------------------------------------------------------------

def _build_game_state(
    game_state: GameStateMachine,
    players: dict[str, Player],
    role_assignments: dict[str, str],
    night_results: str = "No night results yet.",
    voting_history: dict[int, dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Return the game state visible to agents (public info only)."""
    alive_ids = game_state.alive_players
    eliminated = [
        {
            "player_id": str(p.id),
            "agent_name": p.agent_name,
            "role": p.role,
            "round": p.eliminated_round,
        }
        for p in players.values()
        if not p.survived and p.eliminated_round is not None
    ]
    return {
        "alive_players": [str(pid) for pid in alive_ids],
        "eliminated_players": eliminated,
        "mayor": str(game_state.mayor_id) if game_state.mayor_id else None,
        "current_round": game_state.current_round,
        "current_phase": (
            game_state.current_phase.value
            if hasattr(game_state.current_phase, "value")
            else str(game_state.current_phase)
        ),
        "night_results": night_results,
        "voting_history": voting_history or {},
    }


def _build_agent_state(
    base_state: dict[str, Any],
    player_id: str,
    role: str,
    role_assignments: dict[str, str],
) -> dict[str, Any]:
    """Augment the base game state with role-specific private info."""
    state = dict(base_state)
    state["private_info"] = get_private_info(player_id, role, role_assignments)
    return state


# ---------------------------------------------------------------------------
# Turn-record helper
# ---------------------------------------------------------------------------

async def _record_turn(
    db: AsyncSession,
    game_id: uuid.UUID,
    player_id: uuid.UUID,
    round_number: int,
    phase: str,
    response: AgentResponse,
    *,
    vote_target_id: uuid.UUID | None = None,
    is_default_response: bool = False,
    token_count_input: int = 0,
    token_count_output: int = 0,
    latency_ms: int = 0,
) -> Turn:
    turn = Turn(
        id=uuid.uuid4(),
        game_id=game_id,
        player_id=player_id,
        round_number=round_number,
        phase=phase,
        prompt_sent="",
        completion_received="",
        private_reasoning=response.private_reasoning or "",
        public_statement=response.public_statement or "",
        vote_target=vote_target_id,
        bid_level=response.bid_level,
        technique_self_label=response.technique_self_label,
        deception_self_label=response.deception_self_label,
        confidence=response.confidence,
        is_default_response=is_default_response,
        token_count_input=token_count_input,
        token_count_output=token_count_output,
        latency_ms=latency_ms,
        created_at=datetime.now(timezone.utc),
    )
    db.add(turn)
    return turn


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run_game(
    db_session: AsyncSession,
    agents: list[AgentInterface],
    config: dict[str, Any] | None = None,
) -> Game:
    """Execute a full Werewolf game and persist all data.

    Parameters
    ----------
    db_session:
        An async SQLAlchemy session.  The caller is responsible for
        committing / rolling back after this coroutine returns.
    agents:
        Exactly 7 ``AgentInterface`` instances.
    config:
        Optional game configuration overrides.

    Returns
    -------
    Game
        The completed (or discarded) Game model instance.
    """

    config = config or {}
    player_count = config.get("player_count", DEFAULT_PLAYER_COUNT)
    debate_cap = config.get("debate_cap", MAX_DEBATE_TURNS)
    max_rounds = config.get("max_rounds", MAX_ROUNDS)

    if len(agents) != player_count:
        raise ValueError(
            f"Expected {player_count} agents, got {len(agents)}"
        )

    # ------------------------------------------------------------------
    # 1. Initialise game, assign roles, create DB records
    # ------------------------------------------------------------------
    game = Game(
        id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        status="running",
        winner=None,
        rounds_played=0,
        total_turns=0,
        is_degraded=False,
        config=config,
    )
    db_session.add(game)

    # Assign roles
    agent_ids = [a.player_id for a in agents]
    role_assignments = assign_roles(agent_ids)

    # Build Player rows and a lookup dict
    players: dict[str, Player] = {}
    agent_map: dict[str, AgentInterface] = {}
    for idx, agent in enumerate(agents):
        role = role_assignments[agent.player_id]
        agent.role = role  # make the agent aware of its role
        player = Player(
            id=uuid.UUID(agent.player_id),
            game_id=game.id,
            agent_name=agent.agent_name,
            role=role,
            persona=config.get("personas", {}).get(agent.player_id, "default"),
            persuasion_profile=config.get("profiles", {}).get(
                agent.player_id, "baseline"
            ),
            is_mayor=False,
            eliminated_round=None,
            survived=True,
            character_image=_CHARACTER_IMAGES[idx % len(_CHARACTER_IMAGES)],
        )
        db_session.add(player)
        players[agent.player_id] = player
        agent_map[agent.player_id] = agent

    # Initialise the state machine
    player_infos = [
        PlayerInfo(player_id=pid, role=role_assignments[pid])
        for pid in agent_ids
    ]
    game_state = GameStateMachine(players=player_infos, max_rounds=max_rounds)

    # Game-start event
    db_session.add(GameEvent(
        id=uuid.uuid4(),
        game_id=game.id,
        round_number=0,
        event_type="game_start",
        details={"player_count": player_count},
        created_at=datetime.now(timezone.utc),
    ))

    total_turn_count = 0

    # ------------------------------------------------------------------
    # 2. Mayor election
    # ------------------------------------------------------------------
    game_state.transition_to_next_phase()  # INIT -> MAYOR_CAMPAIGN
    base_state = _build_game_state(game_state, players, role_assignments)

    # Campaign speeches
    for pid in list(game_state.alive_players):
        agent = agent_map[pid]
        state = _build_agent_state(base_state, pid, role_assignments[pid], role_assignments)
        resp = await agent.campaign(state)
        _meta = getattr(agent, "last_turn_metadata", None)
        await _record_turn(
            db_session, game.id, uuid.UUID(pid), 0, "mayor_campaign", resp,
            is_default_response=getattr(_meta, "is_default_response", False),
            token_count_input=getattr(_meta, "token_count_input", 0),
            token_count_output=getattr(_meta, "token_count_output", 0),
            latency_ms=getattr(_meta, "latency_ms", 0),
        )
        total_turn_count += 1

    # Mayor votes
    game_state.transition_to_next_phase()  # MAYOR_CAMPAIGN -> MAYOR_VOTE
    candidates = list(game_state.alive_players)
    mayor_votes: dict[str, str] = {}
    for pid in list(game_state.alive_players):
        agent = agent_map[pid]
        state = _build_agent_state(base_state, pid, role_assignments[pid], role_assignments)
        chosen = await agent.vote_for_mayor(state, candidates)
        mayor_votes[pid] = chosen
        resp = AgentResponse(
            private_reasoning=f"Voted for {chosen} as mayor.",
            public_statement="",
            vote_target=chosen,
            deception_self_label="truthful",
            confidence=3,
        )
        await _record_turn(
            db_session, game.id, uuid.UUID(pid), 0, "mayor_vote", resp,
            vote_target_id=uuid.UUID(chosen),
        )
        total_turn_count += 1

    # Determine mayor
    mayor_result = run_mayor_election(candidates, mayor_votes)
    mayor_id = mayor_result.winner
    game_state.mayor_id = mayor_id
    players[mayor_id].is_mayor = True

    db_session.add(GameEvent(
        id=uuid.uuid4(),
        game_id=game.id,
        round_number=0,
        event_type="mayor_elected",
        details={"mayor_id": mayor_id},
        created_at=datetime.now(timezone.utc),
    ))

    # ------------------------------------------------------------------
    # 3. Main game loop (up to max_rounds rounds)
    # ------------------------------------------------------------------
    winner: str | None = None
    voting_history: dict[int, dict[str, str]] = {}
    last_night_result: str = "No night results yet."

    for round_num in range(1, max_rounds + 1):
        game_state.current_round = round_num

        # ==============================================================
        # 3a. NIGHT PHASE
        # ==============================================================
        game_state.transition_to_next_phase()  # -> NIGHT
        base_state = _build_game_state(
            game_state, players, role_assignments,
            night_results=last_night_result,
            voting_history=voting_history,
        )

        wolf_targets: list[str] = []  # BUG 3: collect all wolf choices
        seer_target: str | None = None
        doctor_target: str | None = None

        # Identify wolf player IDs for wolf-on-wolf validation (BUG 9)
        wolf_player_ids = [
            pid for pid in game_state.alive_players
            if role_assignments[pid] == "werewolf"
        ]

        for pid in list(game_state.alive_players):
            role = role_assignments[pid]
            agent = agent_map[pid]
            state = _build_agent_state(base_state, pid, role, role_assignments)

            if role == "werewolf":
                target = await agent.night_action(state, "werewolf")
                # BUG 9: Validate wolf target is not a wolf teammate
                if target in wolf_player_ids:
                    non_wolf_alive = [
                        p for p in game_state.alive_players
                        if role_assignments[p] != "werewolf"
                    ]
                    if non_wolf_alive:
                        target = random.choice(non_wolf_alive)
                        logger.warning(
                            "Wolf %s targeted a teammate; reassigned to %s",
                            pid, target,
                        )
                wolf_targets.append(target)
                resp = AgentResponse(
                    private_reasoning=f"Targeting {target} for kill.",
                    vote_target=target,
                    deception_self_label="truthful",
                    confidence=3,
                )
                await _record_turn(
                    db_session, game.id, uuid.UUID(pid), round_num,
                    "night_kill", resp, vote_target_id=uuid.UUID(target),
                )
                total_turn_count += 1

            elif role == "seer":
                target = await agent.night_action(state, "seer")
                # BUG 10: Validate seer target is alive
                if target not in game_state.alive_players:
                    valid_targets = [
                        p for p in game_state.alive_players if p != pid
                    ]
                    if valid_targets:
                        target = random.choice(valid_targets)
                        logger.warning(
                            "Seer %s investigated dead player; reassigned to %s",
                            pid, target,
                        )
                seer_target = target
                resp = AgentResponse(
                    private_reasoning=f"Investigating {target}.",
                    deception_self_label="truthful",
                    confidence=3,
                )
                await _record_turn(
                    db_session, game.id, uuid.UUID(pid), round_num,
                    "night_investigate", resp,
                )
                total_turn_count += 1

            elif role == "doctor":
                target = await agent.night_action(state, "doctor")
                doctor_target = target
                resp = AgentResponse(
                    private_reasoning=f"Protecting {target}.",
                    deception_self_label="truthful",
                    confidence=3,
                )
                await _record_turn(
                    db_session, game.id, uuid.UUID(pid), round_num,
                    "night_protect", resp,
                )
                total_turn_count += 1

        # BUG 3: Wolf consensus — if both agree use that target,
        # otherwise pick randomly between the two choices. Log both.
        wolf_target: str | None = None
        if wolf_targets:
            if len(wolf_targets) == 1:
                wolf_target = wolf_targets[0]
            else:
                logger.info("Wolf targets: %s", wolf_targets)
                if len(set(wolf_targets)) == 1:
                    wolf_target = wolf_targets[0]
                    logger.info("Wolves agreed on target %s", wolf_target)
                else:
                    wolf_target = random.choice(wolf_targets)
                    logger.info(
                        "Wolves disagreed (%s); randomly chose %s",
                        wolf_targets, wolf_target,
                    )

        # resolve_night handles elimination on the game_state internally
        night_result = resolve_night(
            wolf_target, seer_target, doctor_target, game_state,
        )

        # Track night results for game state
        if night_result.kill_successful and night_result.killed_player:
            killed_name = players[night_result.killed_player].agent_name
            last_night_result = f"{killed_name} (Player {night_result.killed_player}) was killed during the night."
        else:
            last_night_result = "Nobody died last night."

        # BUG 2: Store seer results in game_state for agent visibility
        if night_result.seer_result and seer_target:
            game_state.seer_results.append(SeerResult(
                target_id=night_result.seer_result["target_id"],
                role=night_result.seer_result["role"],
                round_number=round_num,
            ))

        # Persist NightAction
        seer_result_role = (
            role_assignments.get(seer_target, "unknown")
            if seer_target
            else "unknown"
        )
        na = NightAction(
            id=uuid.uuid4(),
            game_id=game.id,
            round_number=round_num,
            wolf_target=uuid.UUID(wolf_target) if wolf_target else None,
            doctor_target=uuid.UUID(doctor_target) if doctor_target else None,
            seer_target=uuid.UUID(seer_target) if seer_target else None,
            seer_result=seer_result_role,
            kill_successful=night_result.kill_successful,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(na)

        # Sync Player DB records with state machine after night kill
        if night_result.kill_successful and night_result.killed_player:
            killed_pid = night_result.killed_player
            players[killed_pid].survived = False
            players[killed_pid].eliminated_round = round_num
            db_session.add(GameEvent(
                id=uuid.uuid4(),
                game_id=game.id,
                round_number=round_num,
                event_type="death",
                details={
                    "player_id": killed_pid,
                    "role": role_assignments[killed_pid],
                    "cause": "werewolf_kill",
                },
                created_at=datetime.now(timezone.utc),
            ))

            # Mayor succession if the killed player was mayor
            if killed_pid == game_state.mayor_id or game_state.mayor_id is None:
                if game_state.alive_players:
                    new_mayor = handle_mayor_succession(
                        killed_pid,
                        game_state.alive_players,
                        None,  # mock agents don't choose successor
                    )
                    game_state.mayor_id = new_mayor
                    players[killed_pid].is_mayor = False
                    players[new_mayor].is_mayor = True
                    db_session.add(GameEvent(
                        id=uuid.uuid4(),
                        game_id=game.id,
                        round_number=round_num,
                        event_type="mayor_succession",
                        details={
                            "old_mayor": killed_pid,
                            "new_mayor": new_mayor,
                        },
                        created_at=datetime.now(timezone.utc),
                    ))

        # Check win condition after night
        win = check_win_condition(
            _alive_player_dicts(game_state.alive_players, role_assignments),
        )
        if win:
            winner = win
            break

        # ==============================================================
        # 3b. DAY PHASE — bidding debate
        # ==============================================================
        game_state.transition_to_next_phase()  # NIGHT -> DAY_BID
        debate_history: list[str] = []
        previous_mentions: list[str] = []

        for turn_idx in range(debate_cap):
            base_state = _build_game_state(
                game_state, players, role_assignments,
                night_results=last_night_result,
                voting_history=voting_history,
            )

            # Collect bids
            bids: dict[str, int] = {}
            for pid in list(game_state.alive_players):
                agent = agent_map[pid]
                state = _build_agent_state(
                    base_state, pid, role_assignments[pid], role_assignments,
                )
                bid_val = await agent.bid(state, debate_history)
                bids[pid] = max(0, min(4, bid_val))  # clamp
                resp = AgentResponse(
                    private_reasoning=f"Bidding {bids[pid]}.",
                    bid_level=bids[pid],
                    deception_self_label="truthful",
                    confidence=3,
                )
                await _record_turn(
                    db_session, game.id, uuid.UUID(pid), round_num,
                    "day_bid", resp,
                )
                total_turn_count += 1

            # Select speaker
            speaker_id = select_speaker(bids, previous_mentions)

            # Get speech
            agent = agent_map[speaker_id]
            state = _build_agent_state(
                base_state, speaker_id,
                role_assignments[speaker_id], role_assignments,
            )
            speech = await agent.speak(state, debate_history)
            _meta = getattr(agent, "last_turn_metadata", None)
            await _record_turn(
                db_session, game.id, uuid.UUID(speaker_id), round_num,
                "day_speech", speech,
                is_default_response=getattr(_meta, "is_default_response", False),
                token_count_input=getattr(_meta, "token_count_input", 0),
                token_count_output=getattr(_meta, "token_count_output", 0),
                latency_ms=getattr(_meta, "latency_ms", 0),
            )
            total_turn_count += 1

            public_text = speech.public_statement or ""
            debate_history.append(public_text)

            # BUG 7: extract_mentions expects agent names, not UUIDs.
            # Build name list for alive players and map mentions back to IDs.
            alive_names = [
                players[pid].agent_name for pid in game_state.alive_players
            ]
            name_to_id = {
                players[pid].agent_name: pid
                for pid in game_state.alive_players
            }
            mentioned_names = extract_mentions(public_text, alive_names)
            previous_mentions = [
                name_to_id[name] for name in mentioned_names
                if name in name_to_id
            ]

        # ==============================================================
        # 3c. VOTE PHASE
        # ==============================================================
        # Set phase directly — the debate loop managed bid/speech turns
        # internally without using the state machine's micro-transitions,
        # so transition_to_next_phase() would land on the wrong state.
        game_state.current_phase = GamePhase.VOTE
        base_state = _build_game_state(
            game_state, players, role_assignments,
            night_results=last_night_result,
            voting_history=voting_history,
        )

        vote_map: dict[str, str] = {}
        for pid in list(game_state.alive_players):
            agent = agent_map[pid]
            state = _build_agent_state(
                base_state, pid, role_assignments[pid], role_assignments,
            )
            vote_resp = await agent.vote(state, debate_history)
            target = vote_resp.vote_target
            # Validate target
            if (
                target is None
                or target not in game_state.alive_players
                or target == pid
            ):
                valid = [p for p in game_state.alive_players if p != pid]
                target = valid[0] if valid else pid
            vote_map[pid] = target

            _meta = getattr(agent, "last_turn_metadata", None)
            await _record_turn(
                db_session, game.id, uuid.UUID(pid), round_num,
                "vote", vote_resp, vote_target_id=uuid.UUID(target),
                is_default_response=getattr(_meta, "is_default_response", False),
                token_count_input=getattr(_meta, "token_count_input", 0),
                token_count_output=getattr(_meta, "token_count_output", 0),
                latency_ms=getattr(_meta, "latency_ms", 0),
            )
            total_turn_count += 1

        # Tally votes
        vote_result = tally_votes(vote_map, game_state.mayor_id)

        # Record voting history for this round
        voting_history[round_num] = dict(vote_map)

        # BUG 5: Use was_tiebreak from VoteResult for mayor's vote record
        for voter_id, target_id in vote_map.items():
            db_session.add(Vote(
                id=uuid.uuid4(),
                game_id=game.id,
                round_number=round_num,
                voter=uuid.UUID(voter_id),
                target=uuid.UUID(target_id),
                is_mayor_tiebreak=(
                    vote_result.was_tiebreak and voter_id == game_state.mayor_id
                ),
                created_at=datetime.now(timezone.utc),
            ))

        eliminated_id = vote_result.eliminated_player

        # BUG 4: Re-vote once on 3+ way split (no elimination)
        if eliminated_id is None:
            logger.info("No elimination in round %d; conducting re-vote", round_num)
            revote_map: dict[str, str] = {}
            for pid in list(game_state.alive_players):
                agent = agent_map[pid]
                state = _build_agent_state(
                    base_state, pid, role_assignments[pid], role_assignments,
                )
                vote_resp = await agent.vote(state, debate_history)
                target = vote_resp.vote_target
                if (
                    target is None
                    or target not in game_state.alive_players
                    or target == pid
                ):
                    valid = [p for p in game_state.alive_players if p != pid]
                    target = valid[0] if valid else pid
                revote_map[pid] = target

                _meta = getattr(agent, "last_turn_metadata", None)
                await _record_turn(
                    db_session, game.id, uuid.UUID(pid), round_num,
                    "revote", vote_resp, vote_target_id=uuid.UUID(target),
                    is_default_response=getattr(_meta, "is_default_response", False),
                    token_count_input=getattr(_meta, "token_count_input", 0),
                    token_count_output=getattr(_meta, "token_count_output", 0),
                    latency_ms=getattr(_meta, "latency_ms", 0),
                )
                total_turn_count += 1

            vote_result = tally_votes(revote_map, game_state.mayor_id)

            for voter_id, target_id in revote_map.items():
                db_session.add(Vote(
                    id=uuid.uuid4(),
                    game_id=game.id,
                    round_number=round_num,
                    voter=uuid.UUID(voter_id),
                    target=uuid.UUID(target_id),
                    is_mayor_tiebreak=(
                        vote_result.was_tiebreak
                        and voter_id == game_state.mayor_id
                    ),
                    created_at=datetime.now(timezone.utc),
                ))

            eliminated_id = vote_result.eliminated_player
            if eliminated_id is None:
                logger.info(
                    "Re-vote also failed in round %d; skipping elimination",
                    round_num,
                )

        if eliminated_id and eliminated_id in game_state.alive_players:
            # Use state machine's eliminate_player to keep state consistent
            game_state.eliminate_player(eliminated_id)
            players[eliminated_id].survived = False
            players[eliminated_id].eliminated_round = round_num

            db_session.add(GameEvent(
                id=uuid.uuid4(),
                game_id=game.id,
                round_number=round_num,
                event_type="elimination",
                details={
                    "player_id": eliminated_id,
                    "role": role_assignments[eliminated_id],
                },
                created_at=datetime.now(timezone.utc),
            ))
            db_session.add(GameEvent(
                id=uuid.uuid4(),
                game_id=game.id,
                round_number=round_num,
                event_type="role_reveal",
                details={
                    "player_id": eliminated_id,
                    "role": role_assignments[eliminated_id],
                },
                created_at=datetime.now(timezone.utc),
            ))

            # Mayor succession on vote elimination
            if game_state.mayor_id is None:
                # eliminate_player clears mayor_id when mayor is eliminated
                if game_state.alive_players:
                    new_mayor = handle_mayor_succession(
                        eliminated_id,
                        game_state.alive_players,
                        None,
                    )
                    game_state.mayor_id = new_mayor
                    players[eliminated_id].is_mayor = False
                    players[new_mayor].is_mayor = True
                    db_session.add(GameEvent(
                        id=uuid.uuid4(),
                        game_id=game.id,
                        round_number=round_num,
                        event_type="mayor_succession",
                        details={
                            "old_mayor": eliminated_id,
                            "new_mayor": new_mayor,
                        },
                        created_at=datetime.now(timezone.utc),
                    ))

        # Check win condition after vote
        win = check_win_condition(
            _alive_player_dicts(game_state.alive_players, role_assignments),
        )
        if win:
            winner = win
            # Still update round history before breaking
            for pid in list(agent_map):
                ag = agent_map[pid]
                if hasattr(ag, "update_round_history"):
                    ag.update_round_history(
                        round_statements=debate_history,
                        vote_result=str(vote_result),
                        eliminated=eliminated_id,
                    )
            break

        # Feed debate history into each LLM agent's memory manager
        for pid in list(agent_map):
            ag = agent_map[pid]
            if hasattr(ag, "update_round_history"):
                ag.update_round_history(
                    round_statements=debate_history,
                    vote_result=str(vote_result),
                    eliminated=eliminated_id,
                )

        game.rounds_played = round_num

    # ------------------------------------------------------------------
    # 4. Finalise game
    # ------------------------------------------------------------------
    if winner:
        game.status = "completed"
        game.winner = winner
        game.rounds_played = game_state.current_round
    else:
        # 10 rounds elapsed without resolution
        game.status = "discarded"
        game.winner = None
        game.rounds_played = max_rounds

    game.total_turns = total_turn_count

    # ------------------------------------------------------------------
    # Task 11: Game degradation tracking
    # Count turns where is_default_response=True.  If >30% of total
    # turns used defaults, mark the game as degraded.
    # ------------------------------------------------------------------
    await db_session.flush()  # ensure turns are visible for counting

    from sqlalchemy import select as sa_select, func as sa_func

    default_count_result = await db_session.execute(
        sa_select(sa_func.count())
        .select_from(Turn)
        .where(Turn.game_id == game.id, Turn.is_default_response.is_(True))
    )
    default_count: int = default_count_result.scalar() or 0

    if total_turn_count > 0:
        default_rate = default_count / total_turn_count
        if default_rate > 0.30:
            game.is_degraded = True
            logger.warning(
                "Game %s degraded: %d/%d turns (%.1f%%) used default responses",
                game.id, default_count, total_turn_count, default_rate * 100,
            )
        elif default_count > 0:
            logger.info(
                "Game %s: %d/%d turns (%.1f%%) used default responses (below threshold)",
                game.id, default_count, total_turn_count, default_rate * 100,
            )

    db_session.add(GameEvent(
        id=uuid.uuid4(),
        game_id=game.id,
        round_number=game.rounds_played,
        event_type="game_end",
        details={
            "winner": game.winner,
            "status": game.status,
            "default_response_count": default_count,
            "total_turns": total_turn_count,
            "is_degraded": game.is_degraded,
        },
        created_at=datetime.now(timezone.utc),
    ))

    # Final flush so that the game object is fully populated before return
    await db_session.flush()

    return game
