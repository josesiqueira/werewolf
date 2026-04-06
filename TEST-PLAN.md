# TEST-PLAN.md — Werewolf AI Agents (Phase 1)

**Stack**: Python 3.12 · FastAPI · SQLAlchemy 2.0 async · Pydantic 2.x · pytest · pytest-asyncio  
**Date**: 2026-04-03  
**Scope**: All engine modules, models, schemas, and API endpoints created in Phase 1.

---

## Fixture conventions

```python
# Canonical 7-player ID set reused across tests
P = [str(uuid.uuid4()) for _ in range(7)]
# P[0]=wolf1, P[1]=wolf2, P[2]=seer, P[3]=doctor, P[4]=villager1, P[5]=villager2, P[6]=villager3
FIXED_ROLES = {
    P[0]: "werewolf", P[1]: "werewolf",
    P[2]: "seer",     P[3]: "doctor",
    P[4]: "villager", P[5]: "villager", P[6]: "villager",
}
```

All pure-logic tests (game_state, roles, night, mayor, day, vote) require **no database**. Integration tests use an async SQLite in-memory session via `pytest-asyncio` + `aiosqlite`.

---

## 1. Game State Machine — `engine/game_state.py`

### UT-001
**Name**: Linear phase progression from INIT to NIGHT  
**Module**: `GameStateMachine.transition_to_next_phase`  
**Description**: Starting from INIT, three successive calls should visit MAYOR_CAMPAIGN → MAYOR_VOTE → NIGHT in that order.  
**Input**: Fresh `GameStateMachine` with 7 players (2 wolves, 1 seer, 1 doctor, 3 villagers), no eliminations.  
**Expected outputs**:
- Call 1 → `GamePhase.MAYOR_CAMPAIGN`
- Call 2 → `GamePhase.MAYOR_VOTE`
- Call 3 → `GamePhase.NIGHT`
- `game_state.current_round == 1` throughout  
**Priority**: HIGH

---

### UT-002
**Name**: NIGHT → DAY_BID resets `debate_turn_count`  
**Module**: `GameStateMachine.transition_to_next_phase`  
**Description**: After the NIGHT phase, transitioning must set `debate_turn_count` to 0 regardless of its previous value.  
**Input**: State in NIGHT phase; manually set `debate_turn_count = 7` before transitioning.  
**Expected output**: `current_phase == GamePhase.DAY_BID` and `debate_turn_count == 0`  
**Priority**: HIGH

---

### UT-003
**Name**: DAY_SPEECH increments debate counter and loops back to DAY_BID  
**Module**: `GameStateMachine.transition_to_next_phase`  
**Description**: Each DAY_SPEECH → DAY_BID cycle should increment `debate_turn_count` by 1 until it hits `MAX_DEBATE_TURNS` (10), then flip to VOTE.  
**Input**: State in DAY_BID, no eliminations. Call DAY_BID → DAY_SPEECH 9 times.  
**Expected outputs**:
- After 9 DAY_SPEECH transitions: `current_phase == DAY_BID`, `debate_turn_count == 9`
- After 10th DAY_SPEECH transition: `current_phase == GamePhase.VOTE`  
**Priority**: HIGH

---

### UT-004
**Name**: VOTE advances round counter and returns to NIGHT  
**Module**: `GameStateMachine.transition_to_next_phase`  
**Description**: After a VOTE with no win condition, the machine increments `current_round` and enters NIGHT.  
**Input**: State in VOTE phase, `current_round = 1`, alive roster still has >2 wolves-vs-villager imbalance resolved (no win).  
**Expected output**: `current_phase == GamePhase.NIGHT`, `current_round == 2`  
**Priority**: HIGH

---

### UT-005
**Name**: Max rounds cap sets status to "discarded"  
**Module**: `GameStateMachine.transition_to_next_phase`  
**Description**: If `current_round >= max_rounds` and win condition is still None after VOTE, the game must enter GAME_OVER with `winner == "discarded"`.  
**Input**: `max_rounds=3`; state in VOTE phase with `current_round = 3`; alive roster = [wolf1, villager1, villager2] (no win condition).  
**Expected output**: `current_phase == GamePhase.GAME_OVER`, `game_state.winner == "discarded"`  
**Priority**: HIGH

---

### UT-006
**Name**: Win condition detected before phase transition halts game immediately  
**Module**: `GameStateMachine.transition_to_next_phase`  
**Description**: If `check_win_condition` returns a winner, the very next call to `transition_to_next_phase` (from any phase) should bypass normal phase logic and return GAME_OVER.  
**Input**: State in DAY_BID; eliminate all wolves so only [seer, doctor, villager] remain, then call transition.  
**Expected output**: `current_phase == GamePhase.GAME_OVER`, `game_state.winner == "villagers"`  
**Priority**: HIGH

---

### UT-007
**Name**: `eliminate_player` removes player from alive list and clears mayor  
**Module**: `GameStateMachine.eliminate_player`  
**Description**: Eliminating the current mayor should set `mayor_id` to None in addition to removing the player.  
**Input**: `alive_players = [P[0], P[1], P[2]]`; `mayor_id = P[1]`; call `eliminate_player(P[1])`.  
**Expected output**: `P[1] not in alive_players`, `mayor_id is None`, `eliminated_players[0].player_id == P[1]`, `eliminated_players[0].eliminated_round == current_round`  
**Priority**: HIGH

---

### UT-008
**Name**: `eliminate_player` is idempotent — duplicate call does nothing  
**Module**: `GameStateMachine.eliminate_player`  
**Description**: Calling `eliminate_player` with a player ID that is already eliminated must not raise an exception or double-append to `eliminated_players`.  
**Input**: Eliminate P[4] once; call `eliminate_player(P[4])` a second time.  
**Expected output**: `len(eliminated_players) == 1`; no exception raised  
**Priority**: MEDIUM

---

### UT-009
**Name**: `get_state_for_agent` — werewolf sees teammates, not role of others  
**Module**: `GameStateMachine.get_state_for_agent`  
**Description**: When called for wolf P[0], the returned dict must contain `werewolf_teammates == [P[1]]` and must NOT include a `seer_results` key.  
**Input**: 7-player state, P[0] and P[1] are wolves.  
**Expected output**: `state["werewolf_teammates"] == [P[1]]`; `"seer_results" not in state`  
**Priority**: MEDIUM

---

### UT-010
**Name**: `get_state_for_agent` — seer sees investigation history  
**Module**: `GameStateMachine.get_state_for_agent`  
**Description**: After appending a `SeerResult` to `game_state.seer_results`, the seer's agent state must expose it; a villager's state must not.  
**Input**: Append `SeerResult(target_id=P[1], role="werewolf", round_number=1)` to `game_state.seer_results`; query state for P[2] (seer) and P[4] (villager).  
**Expected outputs**:
- P[2] state: `seer_results == [{"target_id": P[1], "role": "werewolf", "round_number": 1}]`
- P[4] state: `"seer_results" not in state`  
**Priority**: MEDIUM

---

### UT-011
**Name**: `check_win_condition` — wolves win at parity  
**Module**: `GameStateMachine.check_win_condition`  
**Description**: When alive wolves == alive non-wolves, return "werewolves".  
**Input**: `alive_players = [P[0], P[1], P[4]]`; roles — P[0]=wolf, P[1]=wolf, P[4]=villager.  
**Expected output**: `"werewolves"`  
**Priority**: HIGH

---

### UT-012
**Name**: `check_win_condition` — villagers win when all wolves eliminated  
**Module**: `GameStateMachine.check_win_condition`  
**Description**: With zero wolves alive, return "villagers".  
**Input**: `alive_players = [P[2], P[3], P[4], P[5]]`; all are seer/doctor/villager roles.  
**Expected output**: `"villagers"`  
**Priority**: HIGH

---

### UT-013
**Name**: `check_win_condition` — game continues when wolves are minority  
**Module**: `GameStateMachine.check_win_condition`  
**Description**: With 1 wolf vs 3 non-wolves, return None.  
**Input**: `alive_players = [P[0], P[2], P[3], P[4]]`; P[0] is wolf.  
**Expected output**: `None`  
**Priority**: HIGH

---

## 2. Role Assignment — `engine/roles.py`

### UT-014
**Name**: `assign_roles` produces exactly the fixed distribution for 7 players  
**Module**: `assign_roles`  
**Description**: Over a single call, the returned mapping must contain exactly 2 werewolves, 1 seer, 1 doctor, and 3 villagers.  
**Input**: `player_ids = [f"p{i}" for i in range(7)]`  
**Expected output**: `Counter(result.values()) == {"werewolf": 2, "seer": 1, "doctor": 1, "villager": 3}`  
**Priority**: HIGH

---

### UT-015
**Name**: `assign_roles` raises `ValueError` for wrong player count  
**Module**: `assign_roles`  
**Description**: Passing 6 or 8 player IDs must raise `ValueError` with a message mentioning "7".  
**Inputs**: `player_ids` of length 6; separately of length 8.  
**Expected output**: `pytest.raises(ValueError)` in both cases; message contains "Expected 7 players"  
**Priority**: HIGH

---

### UT-016
**Name**: `get_private_info` — werewolf receives teammate list  
**Module**: `get_private_info`  
**Description**: A werewolf player should see the other wolf's ID in `info["teammates"]`.  
**Input**: `player_id=P[0]`, `role="werewolf"`, `all_assignments=FIXED_ROLES`.  
**Expected output**: `{"role": "werewolf", "teammates": [P[1]]}`  
**Priority**: MEDIUM

---

### UT-017
**Name**: `get_private_info` — non-werewolf roles receive only their own role  
**Module**: `get_private_info`  
**Description**: Seer, doctor, and villager must NOT receive a `teammates` key.  
**Inputs**: `(P[2], "seer", FIXED_ROLES)`, `(P[3], "doctor", FIXED_ROLES)`, `(P[4], "villager", FIXED_ROLES)`.  
**Expected output**: Each returns `{"role": <role>}` with no `"teammates"` key  
**Priority**: MEDIUM

---

## 3. Night Phase Resolution — `engine/night.py`

### UT-018
**Name**: Wolf kill succeeds when doctor protects a different player  
**Module**: `resolve_night`  
**Description**: Wolf targets P[4]; doctor protects P[3]. The kill should go through.  
**Input**: `wolf_target=P[4]`, `seer_target=None`, `doctor_target=P[3]`, state with P[4] alive.  
**Expected output**: `result.kill_successful == True`, `result.killed_player == P[4]`, `P[4] not in game_state.alive_players`  
**Priority**: HIGH

---

### UT-019
**Name**: Doctor save blocks wolf kill when targets match  
**Module**: `resolve_night`  
**Description**: Wolf and doctor both target the same player — kill must be blocked.  
**Input**: `wolf_target=P[4]`, `seer_target=None`, `doctor_target=P[4]`.  
**Expected output**: `result.kill_successful == False`, `result.killed_player is None`, `P[4] in game_state.alive_players`  
**Priority**: HIGH

---

### UT-020
**Name**: Seer investigation returns correct role regardless of kill outcome  
**Module**: `resolve_night`  
**Description**: Seer investigates P[1] (a werewolf). Whether or not a kill happens, `seer_result` must correctly identify P[1] as "werewolf".  
**Input**: `wolf_target=P[4]`, `seer_target=P[1]`, `doctor_target=P[3]`; `FIXED_ROLES[P[1]] == "werewolf"`.  
**Expected output**: `result.seer_result == {"target_id": P[1], "role": "werewolf"}`  
**Priority**: HIGH

---

### UT-021
**Name**: No wolf target produces no kill and `kill_successful == False`  
**Module**: `resolve_night`  
**Description**: When wolves pass (wolf_target=None), nobody dies.  
**Input**: `wolf_target=None`, `seer_target=P[2]`, `doctor_target=P[4]`.  
**Expected output**: `result.killed_player is None`, `result.kill_successful == False`, alive list unchanged  
**Priority**: MEDIUM

---

### UT-022
**Name**: Seer investigates a villager — result role is "villager"  
**Module**: `resolve_night`  
**Description**: Confirm the seer gets an accurate non-wolf result.  
**Input**: `wolf_target=None`, `seer_target=P[4]`, `doctor_target=None`; `FIXED_ROLES[P[4]] == "villager"`.  
**Expected output**: `result.seer_result == {"target_id": P[4], "role": "villager"}`  
**Priority**: MEDIUM

---

## 4. Mayor Election — `engine/mayor.py`

### UT-023
**Name**: Plurality winner with no tie  
**Module**: `run_mayor_election`  
**Description**: Three candidates; two voters pick P[2], one picks P[0]. P[2] must win without a tiebreak.  
**Input**: `candidates=[P[0], P[2], P[4]]`, `votes={P[0]: P[2], P[4]: P[2], P[3]: P[0]}`.  
**Expected output**: `result.winner == P[2]`, `result.was_tiebreak == False`, `result.vote_counts == {P[0]: 1, P[2]: 2, P[4]: 0}`  
**Priority**: HIGH

---

### UT-024
**Name**: Two-way tie resolved by random selection, `was_tiebreak == True`  
**Module**: `run_mayor_election`  
**Description**: Two candidates each receive 2 votes. Result winner must be one of the tied candidates and `was_tiebreak` must be True.  
**Input**: `candidates=[P[0], P[2]]`, `votes={P[0]: P[2], P[1]: P[2], P[3]: P[0], P[4]: P[0]}`.  
**Expected output**: `result.winner in [P[0], P[2]]`, `result.was_tiebreak == True`  
**Priority**: HIGH

---

### UT-025
**Name**: Candidate with zero votes still appears in `vote_counts`  
**Module**: `run_mayor_election`  
**Description**: A candidate nobody voted for must still appear with a count of 0.  
**Input**: `candidates=[P[0], P[2], P[4]]`, `votes={P[3]: P[0], P[5]: P[0]}`.  
**Expected output**: `result.vote_counts[P[4]] == 0`, `result.winner == P[0]`  
**Priority**: MEDIUM

---

### UT-026
**Name**: `run_mayor_election` raises `ValueError` for empty candidates  
**Module**: `run_mayor_election`  
**Description**: Passing an empty candidate list must raise.  
**Input**: `candidates=[]`, `votes={}`.  
**Expected output**: `pytest.raises(ValueError)`  
**Priority**: MEDIUM

---

### UT-027
**Name**: `handle_mayor_succession` — valid successor choice is honoured  
**Module**: `handle_mayor_succession`  
**Description**: When the dead mayor nominates a valid alive player as successor, that player must become mayor.  
**Input**: `dead_mayor=P[0]`, `alive_players=[P[2], P[3], P[4]]`, `successor_choice=P[3]`.  
**Expected output**: returns `P[3]`  
**Priority**: MEDIUM

---

### UT-028
**Name**: `handle_mayor_succession` — invalid successor falls back to random  
**Module**: `handle_mayor_succession`  
**Description**: If the nominated successor is not in the alive list, the function must still return a valid alive player (random fallback).  
**Input**: `dead_mayor=P[0]`, `alive_players=[P[2], P[3]]`, `successor_choice=P[6]` (dead/not in alive).  
**Expected output**: `result in [P[2], P[3]]`  
**Priority**: MEDIUM

---

### UT-029
**Name**: `handle_mayor_succession` raises `ValueError` with no alive players  
**Module**: `handle_mayor_succession`  
**Description**: Empty alive list must raise rather than return silently.  
**Input**: `dead_mayor=P[0]`, `alive_players=[]`, `successor_choice=None`.  
**Expected output**: `pytest.raises(ValueError)`  
**Priority**: MEDIUM

---

## 5. Day Bidding — `engine/day.py`

### UT-030
**Name**: Highest unique bidder wins outright  
**Module**: `select_speaker`  
**Description**: One player bids 4, all others bid 0–3. That player should be selected without any tiebreak.  
**Input**: `bids={P[0]: 4, P[1]: 2, P[2]: 1, P[3]: 0}`, `previous_mentions=[]`.  
**Expected output**: `select_speaker(...) == P[0]`  
**Priority**: HIGH

---

### UT-031
**Name**: Mention priority breaks bid tie  
**Module**: `select_speaker`  
**Description**: Two players tie with bid=3; the one mentioned first in the previous turn's statement wins.  
**Input**: `bids={P[0]: 3, P[1]: 3, P[2]: 1}`, `previous_mentions=[P[1], P[0]]`.  
**Expected output**: `select_speaker(...) == P[1]`  
**Priority**: HIGH

---

### UT-032
**Name**: All-zero bids falls through to random selection  
**Module**: `select_speaker`  
**Description**: When every player bids 0 and no mentions exist, any player can be returned (must be one of the bidders, not None/crash).  
**Input**: `bids={P[0]: 0, P[1]: 0, P[2]: 0}`, `previous_mentions=[]`.  
**Expected output**: `result in [P[0], P[1], P[2]]`; no exception  
**Priority**: MEDIUM

---

### UT-033
**Name**: `extract_mentions` finds player names case-insensitively  
**Module**: `extract_mentions`  
**Description**: Statement contains "ALICE" and "bob"; player_names contains "Alice" and "Bob". Both should be returned in mention order.  
**Input**: `statement="ALICE thinks BOB is suspicious."`, `player_names=["Alice", "Bob", "Carol"]`.  
**Expected output**: `["Alice", "Bob"]`  
**Priority**: MEDIUM

---

### UT-034
**Name**: `extract_mentions` does not partial-match substrings  
**Module**: `extract_mentions`  
**Description**: A name that appears as a substring of a longer word must NOT be reported as a mention.  
**Input**: `statement="I think we should also consider."`, `player_names=["Al"]`.  
**Expected output**: `[]` (word-boundary prevents "Al" matching inside "also")  
**Priority**: MEDIUM

---

### UT-035
**Name**: `select_speaker` raises `ValueError` for empty bids  
**Module**: `select_speaker`  
**Description**: Empty bids dict must raise rather than produce an undefined result.  
**Input**: `bids={}`, `previous_mentions=[]`.  
**Expected output**: `pytest.raises(ValueError)`  
**Priority**: LOW

---

## 6. Vote Tallying — `engine/vote.py`

### UT-036
**Name**: Clear plurality eliminates single target  
**Module**: `tally_votes`  
**Description**: Four players vote for P[1]; one votes for P[2]. P[1] must be eliminated.  
**Input**: `votes={P[0]: P[1], P[2]: P[1], P[3]: P[1], P[4]: P[1], P[5]: P[2]}`.  
**Expected output**: `result.eliminated_player == P[1]`, `result.was_tiebreak == False`, `result.vote_counts[P[1]] == 4`  
**Priority**: HIGH

---

### UT-037
**Name**: Two-way tie broken by mayor's vote  
**Module**: `tally_votes`  
**Description**: P[0] and P[1] each receive 2 votes; mayor P[5] voted for P[0]. Mayor's vote must resolve the tie in favour of P[0].  
**Input**: `votes={P[2]: P[0], P[3]: P[0], P[4]: P[1], P[5]: P[0]}`, `mayor_id=P[5]`.  
**Expected output**: `result.eliminated_player == P[0]`, `result.was_tiebreak == True`  
**Priority**: HIGH

---

### UT-038
**Name**: Two-way tie where mayor voted for neither — no elimination  
**Module**: `tally_votes`  
**Description**: P[0] and P[1] tied; mayor voted for P[2] who has 0 votes. No mayor tiebreak can apply.  
**Input**: `votes={P[2]: P[0], P[3]: P[0], P[4]: P[1], P[5]: P[1]}`, `mayor_id=P[6]`; `votes[P[6]] = P[2]`.  
**Expected output**: `result.eliminated_player is None`, `result.was_tiebreak == False`  
**Priority**: HIGH

---

### UT-039
**Name**: Three-way split results in no elimination  
**Module**: `tally_votes`  
**Description**: Three targets each get exactly 2 votes; no one has plurality.  
**Input**: `votes={P[0]: P[4], P[1]: P[4], P[2]: P[5], P[3]: P[5], P[5]: P[6], P[6]: P[6]}`, `mayor_id=None`.  
**Expected output**: `result.eliminated_player is None`, `result.was_tiebreak == False`  
**Priority**: HIGH

---

### UT-040
**Name**: Empty vote dict returns no elimination without error  
**Module**: `tally_votes`  
**Description**: An empty votes dict (degenerate case) must return a safe VoteResult.  
**Input**: `votes={}`, `mayor_id=None`.  
**Expected output**: `result.eliminated_player is None`, `result.vote_counts == {}`  
**Priority**: LOW

---

### UT-041
**Name**: `check_win_condition` (vote.py) — wolf parity wins  
**Module**: `vote.check_win_condition`  
**Description**: Verify the standalone win-check function (separate from the state machine's copy) handles parity correctly.  
**Input**: `alive_players=[{"role": "werewolf"}, {"role": "werewolf"}, {"role": "villager"}, {"role": "villager"}]`  
**Expected output**: `"werewolves"`  
**Priority**: HIGH

---

### UT-042
**Name**: `check_win_condition` (vote.py) — all wolves dead  
**Module**: `vote.check_win_condition`  
**Description**: Standalone function must return "villagers" when wolf_count == 0.  
**Input**: `alive_players=[{"role": "seer"}, {"role": "doctor"}, {"role": "villager"}]`  
**Expected output**: `"villagers"`  
**Priority**: HIGH

---

## 7. Agent Interface — `engine/agent_interface.py`

### UT-043
**Name**: `MockAgent` campaign always returns a non-empty `public_statement`  
**Module**: `MockAgent.campaign`  
**Description**: The campaign method must never produce an empty or None public statement, as blank speeches would corrupt the debate transcript.  
**Input**: Call `await mock_agent.campaign({"alive_players": [P[0]], ...})`.  
**Expected output**: `isinstance(result.public_statement, str)` and `len(result.public_statement) > 0`  
**Priority**: MEDIUM

---

### UT-044
**Name**: `MockAgent.vote_for_mayor` never returns agent's own ID when other candidates exist  
**Module**: `MockAgent.vote_for_mayor`  
**Description**: The mock agent filters itself from candidates. Result should be one of the other candidates.  
**Input**: `candidates=[P[0], P[1], P[2]]`; agent's `player_id = P[0]`.  
**Expected output**: `result in [P[1], P[2]]`; never `P[0]`  
**Priority**: MEDIUM

---

### UT-045
**Name**: `MockAgent.bid` always returns a value in [0, 4]  
**Module**: `MockAgent.bid`  
**Description**: The random bid must remain within the allowed clamping range that the game loop enforces.  
**Input**: Call `await mock_agent.bid({}, [])` 50 times.  
**Expected output**: All results `>= 0` and `<= 4`  
**Priority**: MEDIUM

---

### UT-046
**Name**: `MockAgent.vote` sets a non-None `vote_target` pointing to an alive opponent  
**Module**: `MockAgent.vote`  
**Description**: The vote response must always include a valid `vote_target` that is not the agent itself.  
**Input**: `game_state={"alive_players": [P[0], P[1], P[2]]}`, agent `player_id = P[0]`.  
**Expected output**: `result.vote_target in [P[1], P[2]]`; not None, not P[0]  
**Priority**: MEDIUM

---

## 8. NDJSON Export — `engine/export.py`

### UT-047
**Name**: `export_game_ndjson` produces one JSON object per turn, no trailing newline  
**Module**: `export_game_ndjson`  
**Description**: Each line of the output must parse as valid JSON; the output must not end with a blank line.  
**Setup**: Insert 3 Turn rows for a known game_id, 2 Player rows.  
**Expected output**: `len(output.splitlines()) == 3`; `json.loads(line)` succeeds for each line; `not output.endswith("\n")`  
**Priority**: HIGH

---

### UT-048
**Name**: Each NDJSON record contains all required fields with correct types  
**Module**: `export_game_ndjson`  
**Description**: Required keys: `game_id`, `round_number`, `phase`, `player_id`, `agent_name`, `role`, `turn_id`, `prompt_sent`, `completion_received`, `private_reasoning`, `public_statement`, `vote_target`, `bid_level`, `technique_self_label`, `deception_self_label`, `confidence`, `is_default_response`, `token_count_input`, `token_count_output`, `latency_ms`, `created_at`.  
**Setup**: Insert one Turn with `bid_level=2`, `confidence=4`, `deception_self_label="truthful"`, `vote_target=<uuid>`, player with `agent_name="Agent_1"`, `role="werewolf"`.  
**Expected output**: Record has all 22 keys; `record["agent_name"] == "Agent_1"`; `record["role"] == "werewolf"`; `record["bid_level"] == 2`; `record["vote_target"]` is a UUID string  
**Priority**: HIGH

---

### UT-049
**Name**: Turns are ordered by `round_number` then `created_at`  
**Module**: `export_game_ndjson`  
**Description**: Three turns inserted in reverse round order must appear in ascending round order in the NDJSON output.  
**Setup**: Insert Turn(round=3), Turn(round=1), Turn(round=2) for same game.  
**Expected output**: `[record["round_number"] for record in parsed_lines] == [1, 2, 3]`  
**Priority**: MEDIUM

---

### UT-050
**Name**: `export_game_ndjson` returns empty string for game with no turns  
**Module**: `export_game_ndjson`  
**Description**: A game with no associated Turn rows must return an empty string, not crash or return `"null"`.  
**Input**: Valid game_id for a game that has no Turn rows.  
**Expected output**: `result == ""`  
**Priority**: MEDIUM

---

### UT-051
**Name**: `export_batch_ndjson` concatenates multiple games with no blank separator lines  
**Module**: `export_batch_ndjson`  
**Description**: Two games each with 2 turns should produce exactly 4 lines with no blank intermediate lines.  
**Setup**: Two game_ids, each with 2 Turn rows.  
**Expected output**: `len(result.splitlines()) == 4`; all lines parse as JSON  
**Priority**: MEDIUM

---

### UT-052
**Name**: `export_batch_ndjson` with empty game_ids list returns empty string  
**Module**: `export_batch_ndjson`  
**Description**: Passing an empty list must not crash and must return empty string.  
**Input**: `game_ids=[]`.  
**Expected output**: `result == ""`  
**Priority**: LOW

---

## 9. API Endpoints — `api/games.py` and `api/export.py`

### UT-053
**Name**: `POST /api/games` creates a completed or discarded game and returns 201  
**Module**: `api/games.create_game`  
**Description**: Using the async test client with MockAgents (via `max_rounds=1` config to keep tests fast), the endpoint must return HTTP 201 with `status in ["completed", "discarded"]` and exactly 7 players.  
**Input**: `POST /api/games` with body `{"config": {"max_rounds": 1}}`.  
**Expected output**: HTTP 201; `response.json()["status"] in ["completed", "discarded"]`; `len(response.json()["players"]) == 7`; `response.json()["total_turns"] > 0`  
**Priority**: HIGH

---

### UT-054
**Name**: `GET /api/games/{game_id}` returns 404 for unknown ID  
**Module**: `api/games.get_game`  
**Description**: A randomly generated UUID that was never persisted must return 404 with a descriptive message.  
**Input**: `GET /api/games/<random-uuid>`.  
**Expected output**: HTTP 404; `response.json()["detail"] == "Game not found"`  
**Priority**: HIGH

---

### UT-055
**Name**: `GET /api/games` with `status` filter returns only matching games  
**Module**: `api/games.list_games`  
**Description**: Insert two games with status="completed" and one with status="discarded". Filtering by `?status=completed` must return exactly 2.  
**Input**: `GET /api/games?status=completed`.  
**Expected output**: HTTP 200; `len(response.json()) == 2`; all items have `"status": "completed"`  
**Priority**: MEDIUM

---

### UT-056
**Name**: `GET /api/games/{game_id}/turns` returns turns in round-then-time order  
**Module**: `api/games.get_game_turns`  
**Description**: After running a game, turn records must be returned in ascending round_number order.  
**Input**: Run a game; `GET /api/games/{game_id}/turns`.  
**Expected output**: HTTP 200; `turns[i]["round_number"] <= turns[i+1]["round_number"]` for all consecutive pairs  
**Priority**: MEDIUM

---

### UT-057
**Name**: `GET /api/games/{game_id}/replay` includes game, players, turns, and events  
**Module**: `api/games.get_game_replay`  
**Description**: The replay endpoint must return all four top-level keys with non-empty lists for turns and events.  
**Input**: Run a game (max_rounds=1); `GET /api/games/{game_id}/replay`.  
**Expected output**: Response has keys `["game", "players", "turns", "events"]`; `len(response["players"]) == 7`; `len(response["events"]) >= 2` (game_start + game_end at minimum)  
**Priority**: MEDIUM

---

### UT-058
**Name**: `GET /api/export/ndjson?game_id=<uuid>` returns NDJSON with correct content-type  
**Module**: `api/export.export_data`  
**Description**: Export for a specific game must respond with `Content-Type: application/x-ndjson` and each line must be valid JSON.  
**Input**: Run a game (max_rounds=1); `GET /api/export/ndjson?game_id={game.id}`.  
**Expected output**: HTTP 200; `Content-Type: application/x-ndjson`; every line parses as JSON; all records share the same `game_id`  
**Priority**: HIGH

---

### UT-059
**Name**: `GET /api/export/csv` returns 400 unsupported format  
**Module**: `api/export.export_data`  
**Description**: Only "ndjson" is a supported format; anything else must return 400.  
**Input**: `GET /api/export/csv`.  
**Expected output**: HTTP 400; `"Unsupported export format" in response.json()["detail"]`  
**Priority**: MEDIUM

---

### UT-060
**Name**: `GET /api/export/ndjson?game_id=<nonexistent>` returns 404  
**Module**: `api/export.export_data`  
**Description**: A valid UUID that doesn't correspond to any game must return 404.  
**Input**: `GET /api/export/ndjson?game_id=<random-uuid>`.  
**Expected output**: HTTP 404; `response.json()["detail"] == "Game not found"`  
**Priority**: MEDIUM

---

## 10. Game Loop Integration — `engine/game_loop.py`

### UT-061
**Name**: Wolf targeting a teammate is silently reassigned to a non-wolf  
**Module**: `run_game` (BUG-9 guard)  
**Description**: Create a custom MockAgent that always returns a wolf teammate's ID as its `night_action`. The game loop must reassign the target to a non-wolf rather than letting wolves kill each other.  
**Setup**: Patch MockAgent.night_action to return wolf teammate ID; run one-round game.  
**Expected output**: `NightAction.wolf_target != wolf_teammate_id` (or kill_successful on a non-wolf) in the persisted NightAction row  
**Priority**: HIGH

---

### UT-062
**Name**: Seer targeting a dead player is reassigned to an alive player  
**Module**: `run_game` (BUG-10 guard)  
**Description**: Patch seer's night_action to return a player_id that was eliminated in an earlier round. The loop must reroute the investigation.  
**Setup**: Eliminate one player; patch seer to target eliminated player_id; run one round.  
**Expected output**: `NightAction.seer_target != eliminated_player_id` in persisted row  
**Priority**: HIGH

---

### UT-063
**Name**: Wolf consensus logic — two wolves agree on same target  
**Module**: `run_game` (`wolf_targets` aggregation)  
**Description**: Both wolves target the same player. Exactly one kill should resolve; `kill_successful = True` and `NightAction.wolf_target` equals the agreed target.  
**Setup**: Patch both wolf MockAgents to return the same villager ID.  
**Expected output**: `night_action.kill_successful == True`; `str(night_action.wolf_target) == villager_id`  
**Priority**: HIGH

---

### UT-064
**Name**: Re-vote triggered on first-round tie with no elimination  
**Module**: `run_game` (BUG-4 re-vote)  
**Description**: Force a 3-way vote split on the first vote. The loop must issue a re-vote (extra Turn rows with phase="revote") before proceeding to the next round.  
**Setup**: Patch all agent.vote to distribute equally across 3 targets (e.g. 2 votes each when 6 alive).  
**Expected output**: Turn rows with `phase="revote"` exist for the round; total vote-phase turns > alive_count  
**Priority**: MEDIUM

---

### UT-065
**Name**: Mayor succession recorded when mayor is killed at night  
**Module**: `run_game` (night mayor succession)  
**Description**: Arrange for the mayor to be the wolf's target with doctor protecting nobody. After the night, a `mayor_succession` GameEvent should be persisted and a new player should be marked `is_mayor=True`.  
**Setup**: Elect P[0] as mayor; force wolf_target=P[0]; doctor_target=P[3] (different player).  
**Expected output**: `GameEvent(event_type="mayor_succession", details={"old_mayor": P[0], ...})` exists; exactly one Player row has `is_mayor=True` after the round  
**Priority**: HIGH

---

## 11. Schema Validation — `schemas/`

### UT-066
**Name**: `AgentResponse` schema rejects `bid_level` outside 0–4  
**Module**: `schemas/agent.AgentResponse`  
**Description**: Pydantic must raise `ValidationError` when `bid_level` is 5 or -1.  
**Inputs**: `AgentResponse(private_reasoning="x", public_statement="y", bid_level=5, ...)` and `bid_level=-1`.  
**Expected output**: `pydantic.ValidationError` raised in both cases  
**Priority**: MEDIUM

---

### UT-067
**Name**: `AgentResponse` schema rejects invalid `deception_self_label`  
**Module**: `schemas/agent.AgentResponse`  
**Description**: `deception_self_label` must be one of the `DeceptionLabel` enum values; an arbitrary string must fail.  
**Input**: `AgentResponse(private_reasoning="x", public_statement="y", deception_self_label="lying", ...)`.  
**Expected output**: `pydantic.ValidationError`  
**Priority**: MEDIUM

---

### UT-068
**Name**: `AgentResponse` schema rejects `confidence` outside 1–5  
**Module**: `schemas/agent.AgentResponse`  
**Description**: `confidence=0` and `confidence=6` must both fail Pydantic validation.  
**Inputs**: `confidence=0`, `confidence=6`.  
**Expected output**: `pydantic.ValidationError` in both cases  
**Priority**: MEDIUM

---

### UT-069
**Name**: `GameCreate` accepts None config gracefully  
**Module**: `schemas/game.GameCreate`  
**Description**: An empty POST body (config=None) must parse to a valid `GameCreate` object without error.  
**Input**: `GameCreate.model_validate({})`.  
**Expected output**: `obj.config is None`; no ValidationError  
**Priority**: LOW

---

### UT-070
**Name**: `PlayerResponse` serialises `is_mayor` and `survived` as booleans  
**Module**: `schemas/player.PlayerResponse`  
**Description**: ORM-mode serialisation must correctly map SQLAlchemy boolean columns to Python bool.  
**Input**: Player ORM object with `is_mayor=False`, `survived=True`.  
**Expected output**: `PlayerResponse.from_orm(player).is_mayor == False`, `survived == True`; types are `bool`, not int  
**Priority**: LOW

---

## Test execution notes

1. **Pure-logic tests** (UT-001 through UT-046, UT-066 through UT-070) require only standard `pytest` — no database, no async. Use `pytest -m "not integration"`.

2. **Export and loop tests** (UT-047 through UT-065) require an async SQLite in-memory database. Use:
   ```
   pytest -m integration --asyncio-mode=auto
   ```
   Configure `pytest-asyncio` in `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   ```

3. **API endpoint tests** (UT-053 through UT-060) use `httpx.AsyncClient` against the FastAPI app with a test database override via `app.dependency_overrides[get_session]`.

4. **Randomised tests** (UT-024, UT-028, UT-032, UT-045): pin `random.seed(42)` where a deterministic assertion is needed; otherwise assert the result is in the valid set.

5. **Performance budget**: all pure-logic tests must complete in < 1 s each; integration tests in < 5 s each (no LLM calls are made, so this is achievable).

---

# Phase 2 — Agent System Tests

**Scope**: `backend/app/agent/` — output parser, leak detection, personas, technique loader, memory manager, system/user message builders, retry/fallback logic.  
**Stack additions**: `pytest-asyncio`, `unittest.mock` (no real OpenAI calls; all LLM interactions are patched).

## Phase 2 fixture conventions

```python
# Re-use the same 7-player ID set from Phase 1
P = [str(uuid.uuid4()) for _ in range(7)]
SELF_ID = P[0]
ALIVE_OTHERS = P[1:]   # 6 other alive players

# Canonical valid AgentResponse JSON payload
VALID_JSON = json.dumps({
    "private_reasoning": "I think P[2] is the seer.",
    "public_statement": "I have no information to share yet.",
    "vote_target": P[2],
    "bid_level": 2,
    "technique_self_label": "Core Principle",
    "deception_self_label": "truthful",
    "confidence": 4,
})
```

All Phase 2 tests are **pure-logic** (no database, no network). Run with `pytest -m "not integration"`.

---

## 12. Output Parser — `agent/output_parser.py`

### UT-071
**Name**: Valid JSON parses to correct `AgentResponse` fields  
**Module**: `parse_agent_response`  
**Description**: A clean, well-formed JSON string with all seven required fields must produce an `AgentResponse` whose attributes match the input exactly, with no auto-correction applied.  
**Input**:
```python
raw = json.dumps({
    "private_reasoning": "I suspect P[1].",
    "public_statement": "Let's vote carefully.",
    "vote_target": P[2],          # P[2] is alive, not self
    "bid_level": 3,
    "technique_self_label": "Core Principle",
    "deception_self_label": "omission",
    "confidence": 5,
})
parse_agent_response(raw, alive_players=P, self_id=P[0], technique_sections=["Core Principle"])
```
**Expected outputs**:
- `result.public_statement == "Let's vote carefully."`
- `result.bid_level == 3`
- `result.deception_self_label == "omission"`
- `result.confidence == 5`
- `result.vote_target == P[2]`  
**Priority**: HIGH

---

### UT-072
**Name**: Markdown-fenced JSON is stripped and parsed successfully  
**Module**: `parse_agent_response` → `_strip_markdown_fences`  
**Description**: LLMs often wrap output in ` ```json … ``` ` fences. The parser must strip them and still produce a valid `AgentResponse`.  
**Input**:
```python
raw = "```json\n" + json.dumps({
    "private_reasoning": "hidden",
    "public_statement": "Hello village.",
    "vote_target": None,
    "bid_level": 1,
    "technique_self_label": "none",
    "deception_self_label": "truthful",
    "confidence": 3,
}) + "\n```"
parse_agent_response(raw, alive_players=P, self_id=P[0], technique_sections=[])
```
**Expected output**: `result.public_statement == "Hello village."` — no `ValueError` or `JSONDecodeError` raised  
**Priority**: HIGH

---

### UT-073
**Name**: Trailing-comma JSON is repaired and parsed  
**Module**: `parse_agent_response` → `_fix_trailing_commas`  
**Description**: A JSON object with a trailing comma before the closing brace (a common LLM error) must be repaired and produce a valid response rather than falling back to defaults.  
**Input**:
```python
raw = """{
  "private_reasoning": "thinking",
  "public_statement": "I agree.",
  "vote_target": null,
  "bid_level": 1,
  "technique_self_label": "none",
  "deception_self_label": "truthful",
  "confidence": 3,
}"""
parse_agent_response(raw, alive_players=P, self_id=P[0], technique_sections=[])
```
**Expected output**: `result.public_statement == "I agree."` — not the parse-failure default `"I need more time to think about this."`  
**Priority**: HIGH

---

### UT-074
**Name**: Completely invalid text falls back to conservative defaults  
**Module**: `parse_agent_response` → `_get_conservative_defaults`  
**Description**: When the LLM returns plain prose instead of JSON, the parser must silently return a safe default `AgentResponse` rather than raising.  
**Input**:
```python
raw = "Sorry, I cannot assist with that request."
result = parse_agent_response(raw, alive_players=P, self_id=P[0], technique_sections=[])
```
**Expected outputs**:
- `result.private_reasoning == "[parse failure — using defaults]"`
- `result.public_statement == "I need more time to think about this."`
- `result.bid_level == 1`
- `result.deception_self_label == "truthful"`
- `result.confidence == 3`
- `result.vote_target in P[1:]` (a valid alive player that is not self)  
**Priority**: HIGH

---

### UT-075
**Name**: `vote_target` pointing to self is auto-corrected to a valid target  
**Module**: `parse_agent_response` — vote_target validation  
**Description**: If an LLM votes for its own player_id, the parser must silently reassign to one of the other alive players.  
**Input**:
```python
raw = json.dumps({..., "vote_target": P[0]})   # self_id == P[0]
result = parse_agent_response(raw, alive_players=P, self_id=P[0], technique_sections=[])
```
**Expected output**: `result.vote_target != P[0]` and `result.vote_target in P[1:]`  
**Priority**: HIGH

---

### UT-076
**Name**: `vote_target` for an eliminated (not alive) player is auto-corrected  
**Module**: `parse_agent_response` — vote_target validation  
**Description**: A player not in `alive_players` must not survive as the vote target.  
**Input**:
```python
dead_player = str(uuid.uuid4())   # not in alive_players
raw = json.dumps({..., "vote_target": dead_player})
result = parse_agent_response(raw, alive_players=P, self_id=P[0], technique_sections=[])
```
**Expected output**: `result.vote_target in P[1:]` (one of the actual alive players, not `dead_player`)  
**Priority**: HIGH

---

### UT-077
**Name**: `bid_level` above 4 is clamped to 4  
**Module**: `parse_agent_response` — bid clamping  
**Description**: An out-of-range high bid must be silently clamped, never rejected outright.  
**Input**: `raw = json.dumps({..., "bid_level": 99})`  
**Expected output**: `result.bid_level == 4`  
**Priority**: MEDIUM

---

### UT-078
**Name**: Negative `bid_level` is clamped to 0  
**Module**: `parse_agent_response` — bid clamping  
**Description**: A negative bid must be clamped to 0, not raise or become a default of 1.  
**Input**: `raw = json.dumps({..., "bid_level": -5})`  
**Expected output**: `result.bid_level == 0`  
**Priority**: MEDIUM

---

### UT-079
**Name**: Unrecognised `deception_self_label` is auto-corrected to "truthful"  
**Module**: `parse_agent_response` — deception label validation  
**Description**: Any value not in `{"truthful", "omission", "distortion", "fabrication", "misdirection"}` must be replaced with `"truthful"`.  
**Inputs**: `"lying"`, `"honest"`, `"DECEIVING"`, `""`.  
**Expected output**: `result.deception_self_label == "truthful"` for every input  
**Priority**: MEDIUM

---

### UT-080
**Name**: Valid `deception_self_label` values are preserved exactly  
**Module**: `parse_agent_response` — deception label validation  
**Description**: All five valid labels must pass through unchanged.  
**Inputs**: `"truthful"`, `"omission"`, `"distortion"`, `"fabrication"`, `"misdirection"` (sent lowercase).  
**Expected outputs**: Each `result.deception_self_label` equals the input value exactly  
**Priority**: MEDIUM

---

### UT-081
**Name**: Missing `bid_level` key defaults to 1  
**Module**: `parse_agent_response` — bid default  
**Description**: When the JSON omits `bid_level` entirely, the default must be 1 (conservative), not 0 or None.  
**Input**: `raw = json.dumps({..., "public_statement": "hi"})` with no `bid_level` key  
**Expected output**: `result.bid_level == 1`  
**Priority**: LOW

---

### UT-082
**Name**: Missing `confidence` key defaults to 3  
**Module**: `parse_agent_response` — confidence default  
**Description**: Absent `confidence` must produce the mid-range default of 3.  
**Input**: JSON object without a `confidence` key  
**Expected output**: `result.confidence == 3`  
**Priority**: LOW

---

## 13. Werewolf Leak Detection — `agent/output_parser.py`

### UT-083
**Name**: Explicit role admission triggers leak detection  
**Module**: `check_werewolf_leaks`  
**Description**: A statement containing `"I'm a werewolf"` must be flagged and replaced with generic text drawn from `_GENERIC_REPLACEMENTS`.  
**Input**: `statement = "Trust me everyone — I'm a werewolf and I chose to save you."`  
**Expected outputs**:
- `has_leak == True`
- `cleaned != statement`
- `cleaned in _GENERIC_REPLACEMENTS`  
**Priority**: HIGH

---

### UT-084
**Name**: Direct night-kill admission triggers leak detection  
**Module**: `check_werewolf_leaks`  
**Description**: A statement matching the pattern `"we killed … last night"` must be caught.  
**Input**: `statement = "We killed Alice last night to protect ourselves."`  
**Expected outputs**: `has_leak == True`, `cleaned != statement`  
**Priority**: HIGH

---

### UT-085
**Name**: Wolf teammate reference triggers leak detection  
**Module**: `check_werewolf_leaks`  
**Description**: The phrase `"my wolf partner"` must match pattern `r"\bwolf\s+partner\b"` and be redacted.  
**Input**: `statement = "My wolf partner and I discussed this."`  
**Expected outputs**: `has_leak == True`, `cleaned in _GENERIC_REPLACEMENTS`  
**Priority**: HIGH

---

### UT-086
**Name**: Innocent wolf-themed language does NOT trigger leak detection  
**Module**: `check_werewolf_leaks`  
**Description**: Game-legal statements that merely discuss wolves as game concepts (not first-person admissions) must not be flagged.  
**Inputs** (each must return `has_leak == False`):
- `"I think there's a wolf among us, let's be careful."`
- `"The wolves will win if we don't vote correctly."`
- `"We should hunt the wolf down."`  
**Expected output**: `has_leak == False` and `cleaned == statement` for every input  
**Priority**: HIGH

---

### UT-087
**Name**: Empty statement is returned unchanged with `has_leak == False`  
**Module**: `check_werewolf_leaks`  
**Description**: Edge case — empty string must not raise and must not be misidentified as a leak.  
**Input**: `statement = ""`  
**Expected outputs**: `has_leak == False`, `cleaned == ""`  
**Priority**: LOW

---

### UT-088
**Name**: "Our kill" phrase triggers leak detection  
**Module**: `check_werewolf_leaks`  
**Description**: The short phrase `"our kill"` matches the dedicated pattern and must be replaced.  
**Input**: `statement = "We need to be careful — our kill last night raised suspicion."`  
**Expected output**: `has_leak == True`  
**Priority**: MEDIUM

---

### UT-089
**Name**: "As a werewolf" phrase triggers leak detection  
**Module**: `check_werewolf_leaks`  
**Description**: Confession mid-speech using `"as a werewolf"` must be caught.  
**Input**: `statement = "As a werewolf, I obviously want to mislead you."`  
**Expected output**: `has_leak == True`, `cleaned in _GENERIC_REPLACEMENTS`  
**Priority**: MEDIUM

---

## 14. Personas — `agent/personas.py`

### UT-090
**Name**: `PERSONAS` dict contains exactly 7 entries with distinct keys  
**Module**: `personas.PERSONAS`  
**Description**: The persona catalogue must have exactly the 7 documented keys. No duplicates are possible in a dict, but the count must be exact.  
**Input**: `PERSONAS` (module-level constant)  
**Expected outputs**:
- `len(PERSONAS) == 7`
- `set(PERSONAS.keys()) == {"analytical", "aggressive", "quiet", "warm", "suspicious", "diplomatic", "blunt"}`  
**Priority**: HIGH

---

### UT-091
**Name**: Every persona description is a non-empty string  
**Module**: `personas.PERSONAS`  
**Description**: Each of the 7 descriptions must be a `str` with `len > 0`. An empty or None description would produce a broken system message.  
**Input**: iterate `PERSONAS.values()`  
**Expected output**: all values satisfy `isinstance(v, str) and len(v) > 0`  
**Priority**: HIGH

---

### UT-092
**Name**: `assign_personas` for 7 players produces all-unique assignments  
**Module**: `assign_personas`  
**Description**: Sampling 7 personas for 7 players must produce a bijection — every player gets a different persona.  
**Input**: `player_ids = [f"p{i}" for i in range(7)]`  
**Expected outputs**:
- `len(result) == 7`
- `len(set(result.values())) == 7` (all 7 distinct persona names used)  
**Priority**: HIGH

---

### UT-093
**Name**: `assign_personas` raises `ValueError` when called with more than 7 players  
**Module**: `assign_personas`  
**Description**: With 8 or more player IDs there are not enough unique personas; a `ValueError` must be raised.  
**Input**: `player_ids = [f"p{i}" for i in range(8)]`  
**Expected output**: `pytest.raises(ValueError)` with a message mentioning how many are available  
**Priority**: MEDIUM

---

### UT-094
**Name**: `get_persona_description` returns the correct description for each persona key  
**Module**: `get_persona_description`  
**Description**: Spot-check three persona lookups to confirm the function returns the same text as the dict directly.  
**Inputs**: `"analytical"`, `"blunt"`, `"warm"`  
**Expected outputs**:
- `get_persona_description("analytical") == PERSONAS["analytical"]`
- `get_persona_description("blunt") == PERSONAS["blunt"]`
- `get_persona_description("warm") == PERSONAS["warm"]`  
**Priority**: MEDIUM

---

### UT-095
**Name**: `get_persona_description` raises `KeyError` for an unknown persona  
**Module**: `get_persona_description`  
**Description**: An invalid persona name must raise `KeyError` (not return None or empty string).  
**Input**: `get_persona_description("stoic")`  
**Expected output**: `pytest.raises(KeyError)`  
**Priority**: LOW

---

## 15. Technique Loader — `agent/techniques.py`

### UT-096
**Name**: All 6 non-baseline technique files load without error  
**Module**: `preload_all` / `load_technique`  
**Description**: After calling `preload_all()`, every profile in `PROFILE_FILE_MAP` must be present in the cache and return a non-empty string from `load_technique`.  
**Setup**: `clear_cache()` before test to guarantee a cold cache; then `preload_all()`.  
**Expected output**: for each profile in `["ethos", "pathos", "logos", "authority_socialproof", "reciprocity_liking", "scarcity_commitment"]`, `load_technique(profile)` returns a `str` with `len > 0`  
**Priority**: HIGH

---

### UT-097
**Name**: `load_technique("baseline")` returns `None`  
**Module**: `load_technique`  
**Description**: The baseline profile explicitly has no technique document; the function must return `None`, not raise and not return an empty string.  
**Input**: `load_technique("baseline")`  
**Expected output**: `result is None`  
**Priority**: HIGH

---

### UT-098
**Name**: `get_technique_sections("ethos")` returns the expected section headings  
**Module**: `get_technique_sections`  
**Description**: The ETHOS file's `## `-level headings are known; verify the loader extracts them correctly.  
**Setup**: `clear_cache()` then call `get_technique_sections("ethos")`.  
**Expected outputs**:
- `result` is a `list` with `len >= 1`
- `"Core Principle" in result`
- `"When Accusing" in result`
- `"When Defending" in result`  
**Priority**: HIGH

---

### UT-099
**Name**: `get_technique_sections("baseline")` returns an empty list  
**Module**: `get_technique_sections`  
**Description**: Baseline agents have no technique sections; the function must return `[]`, not `None` or raise.  
**Input**: `get_technique_sections("baseline")`  
**Expected output**: `result == []`  
**Priority**: MEDIUM

---

### UT-100
**Name**: Technique loader is idempotent — second load hits cache  
**Module**: `load_technique` caching behaviour  
**Description**: The file should be read from disk only once. Calling `load_technique("pathos")` twice must return the same object (or at least the same content) without error, confirming the `_cache` guard works.  
**Setup**: `clear_cache()`, call `load_technique("pathos")` twice.  
**Expected outputs**:
- Both calls return identical strings (`first == second`)
- No exception on either call  
**Priority**: LOW

---

## 16. Memory Manager — `agent/memory.py`

### UT-101
**Name**: `summarize_round` includes vote result and elimination in output  
**Module**: `MemoryManager.summarize_round`  
**Description**: The summary string must contain the exact vote_result text and the eliminated player description when provided.  
**Input**:
```python
mm = MemoryManager()
summary = mm.summarize_round(
    round_statements=["I trust Alice.", "Bob is suspicious."],
    vote_result="Bob eliminated with 4 votes",
    eliminated="Bob (villager)",
)
```
**Expected outputs**:
- `"Bob eliminated with 4 votes" in summary`
- `"Bob (villager)" in summary`  
**Priority**: HIGH

---

### UT-102
**Name**: Accusation keywords in statements appear in the summary  
**Module**: `MemoryManager.summarize_round`  
**Description**: Statements containing accusation keywords (`"suspect"`, `"werewolf"`, `"lying"`, etc.) must contribute to the `"Key accusations:"` section of the summary.  
**Input**:
```python
statements = [
    "I suspect Carol is lying about her role.",
    "Carol seems totally fine to me.",
]
summary = mm.summarize_round(statements, vote_result="Carol eliminated", eliminated=None)
```
**Expected output**: `"Key accusations:" in summary` and `"Carol" in summary`  
**Priority**: MEDIUM

---

### UT-103
**Name**: `get_context` returns empty string when history is empty  
**Module**: `MemoryManager.get_context`  
**Description**: With no prior rounds, calling `get_context` must return `""` rather than headers-only or crash.  
**Input**: `mm.get_context(current_round=1, full_history=[])`  
**Expected output**: `result == ""`  
**Priority**: MEDIUM

---

### UT-104
**Name**: Rounds beyond `FULL_TRANSCRIPT_ROUNDS` (3) appear as summaries, not full transcripts  
**Module**: `MemoryManager.get_context`  
**Description**: With 5 rounds of history, rounds 1 and 2 must appear as `[Round N summary]` blocks (not full transcripts), while rounds 3–5 appear as `[Round N - full transcript]` blocks.  
**Input**:
```python
history = [[f"Statement R{r+1} S{s}" for s in range(2)] for r in range(5)]
mm = MemoryManager(max_tokens=10000)  # generous budget so nothing is dropped
context = mm.get_context(current_round=5, full_history=history)
```
**Expected outputs**:
- `"[Round 1 summary]" in context`
- `"[Round 2 summary]" in context`
- `"[Round 3 - full transcript]" in context`
- `"[Round 5 - full transcript]" in context`  
**Priority**: HIGH

---

### UT-105
**Name**: `get_context` respects the token budget and truncates older rounds first  
**Module**: `MemoryManager.get_context`  
**Description**: With a very tight token budget (50 tokens), the context must stay under the limit and must not raise. Older rounds should be omitted before newer ones.  
**Input**:
```python
history = [["A " * 200] for _ in range(6)]   # each round ~267 estimated tokens
mm = MemoryManager(max_tokens=50)
context = mm.get_context(current_round=6, full_history=history)
```
**Expected outputs**:
- `_estimate_tokens(context) <= 50` (using the same word-count approximation)
- No exception raised  
**Priority**: MEDIUM

---

### UT-106
**Name**: `store_round_summary` pre-populates cache so `get_context` uses stored summary  
**Module**: `MemoryManager.store_round_summary` + `get_context`  
**Description**: After pre-storing a custom summary for round 1, `get_context` with 4+ rounds of history must use the stored summary string verbatim (not re-summarize from statements).  
**Input**:
```python
mm = MemoryManager(max_tokens=5000)
mm.store_round_summary(1, ["ignored statement"], "custom vote result", "custom elimination")
history = [["ignored statement"]] + [[f"R{r}" for r in range(2)] for _ in range(3)]
context = mm.get_context(current_round=4, full_history=history)
```
**Expected output**: `"custom vote result" in context`  
**Priority**: MEDIUM

---

## 17. System Message Builder — `agent/prompts/system_message.py`

### UT-107
**Name**: System message for a villager contains all five required sections  
**Module**: `build_system_message`  
**Description**: The assembled system message must include the game rules section, role assignment line, persona header, JSON format instructions, and behavioral instructions — all as non-empty content.  
**Input**:
```python
msg = build_system_message(
    role="villager",
    player_id=P[0],
    persona_description="You are reserved and careful.",
)
```
**Expected outputs** (all `in msg`):
- `"Werewolf"` (game rules section)
- `f"Player {P[0]}"` (role section)
- `"Villager"` (role capitalised)
- `"Your Persona:"` (persona section header)
- `"private_reasoning"` (JSON format instructions)
- `"Never reveal private information"` (behavioral instructions)  
**Priority**: HIGH

---

### UT-108
**Name**: Werewolf system message includes teammate IDs  
**Module**: `build_system_message`  
**Description**: When building a message for a werewolf with teammates, the teammate player IDs must appear in the role section.  
**Input**:
```python
msg = build_system_message(
    role="werewolf",
    player_id=P[0],
    persona_description="Bold and aggressive.",
    teammates=[P[1], P[2]],
)
```
**Expected outputs**:
- `f"Player {P[1]}" in msg`
- `f"Player {P[2]}" in msg`
- `"werewolf teammate" in msg.lower()`  
**Priority**: HIGH

---

### UT-109
**Name**: Seer system message references nightly investigation ability  
**Module**: `build_system_message`  
**Description**: The seer role section must mention the investigation mechanic so the agent understands its night action.  
**Input**: `build_system_message(role="seer", player_id=P[2], persona_description="Quiet observer.")`  
**Expected output**: `"investigate" in msg.lower()`  
**Priority**: MEDIUM

---

### UT-110
**Name**: `get_or_build_system_message` returns identical string on second call (cache hit)  
**Module**: `get_or_build_system_message` caching  
**Description**: Two calls with the same `(game_id, player_id)` pair must return the exact same string object (or at least equal strings), confirming the cache is working.  
**Input**:
```python
from app.agent.prompts.system_message import get_or_build_system_message, clear_cache
clear_cache()
game_id = "test-game-1"
first  = get_or_build_system_message(game_id, P[0], "villager", "Careful thinker.")
second = get_or_build_system_message(game_id, P[0], "villager", "Careful thinker.")
```
**Expected output**: `first == second`  
**Priority**: LOW

---

## 18. User Message Builder — `agent/prompts/user_message.py`

### UT-111
**Name**: Non-baseline agent user message includes the persuasion technique section  
**Module**: `build_user_message`  
**Description**: When `technique_text` is non-None, the user message must wrap it with the `=== PERSUASION TECHNIQUE GUIDE ===` header and footer.  
**Input**:
```python
msg = build_user_message(
    phase="day_speech",
    game_state={"current_round": 1, "current_phase": "DAY_SPEECH", "alive_players": P},
    technique_text="Ethos content here.",
)
```
**Expected outputs**:
- `"=== PERSUASION TECHNIQUE GUIDE ===" in msg`
- `"Ethos content here." in msg`
- `"=== END PERSUASION TECHNIQUE GUIDE ===" in msg`  
**Priority**: HIGH

---

### UT-112
**Name**: Baseline agent user message omits the persuasion technique section  
**Module**: `build_user_message`  
**Description**: When `technique_text=None`, the technique section headers must not appear in the output at all.  
**Input**:
```python
msg = build_user_message(
    phase="vote",
    game_state={"current_round": 2, "current_phase": "VOTE", "alive_players": P},
    technique_text=None,
)
```
**Expected outputs**:
- `"PERSUASION TECHNIQUE GUIDE" not in msg`
- `"=== CURRENT GAME STATE ===" in msg`  
**Priority**: HIGH

---

### UT-113
**Name**: Game state section lists all alive players  
**Module**: `build_user_message` → `_format_game_state`  
**Description**: The formatted game state must include every player ID in `alive_players`.  
**Input**:
```python
msg = build_user_message(
    phase="day_bid",
    game_state={
        "current_round": 1,
        "current_phase": "DAY_BID",
        "alive_players": [P[0], P[1], P[2]],
    },
)
```
**Expected outputs**: `P[0] in msg`, `P[1] in msg`, `P[2] in msg`  
**Priority**: MEDIUM

---

### UT-114
**Name**: Debate history appears in user message with turn numbers  
**Module**: `build_user_message` → `_format_conversation_history`  
**Description**: Each statement in `debate_history` must appear labelled with its turn index.  
**Input**:
```python
msg = build_user_message(
    phase="day_speech",
    game_state={"current_round": 1, "current_phase": "DAY_SPEECH", "alive_players": P},
    debate_history=["Alice said something.", "Bob replied."],
)
```
**Expected outputs**:
- `"=== CONVERSATION HISTORY ===" in msg`
- `"[Turn 1] Alice said something." in msg`
- `"[Turn 2] Bob replied." in msg`  
**Priority**: MEDIUM

---

### UT-115
**Name**: Correct phase instruction is injected for each of the 8 phases  
**Module**: `build_user_message` — `_TURN_INSTRUCTIONS` mapping  
**Description**: Each recognised phase must produce a message containing the phase-specific instruction keyword. Verify all 8 phases: `mayor_campaign`, `mayor_vote`, `night_kill`, `night_investigate`, `night_protect`, `day_bid`, `day_speech`, `vote`.  
**Input**: Call `build_user_message(phase=p, game_state={...}, ...)` for each phase `p`.  
**Expected outputs** (phrase must appear in corresponding message):
- `mayor_campaign` → `"Campaign for mayor"` in msg
- `mayor_vote` → `"Vote for mayor"` in msg
- `night_kill` → `"eliminate tonight"` in msg
- `night_investigate` → `"investigate tonight"` in msg
- `night_protect` → `"protect tonight"` in msg
- `day_bid` → `"bid"` in msg (lowercase)
- `day_speech` → `"persuade"` in msg
- `vote` → `"Vote to eliminate"` in msg  
**Priority**: MEDIUM

---

## 19. Retry and Fallback — `agent/retry.py`

### UT-116
**Name**: Successful LLM call on first attempt returns result with `is_default == False`  
**Module**: `call_with_retry_and_fallback`  
**Description**: When the coroutine succeeds immediately, the function must return `(result, False)` — the real result with no default flag set.  
**Setup**:
```python
import asyncio
from unittest.mock import AsyncMock
from app.agent.retry import call_with_retry_and_fallback

mock_result = object()   # any sentinel
coro = AsyncMock(return_value=mock_result)
result, is_default = asyncio.run(
    call_with_retry_and_fallback(coro, alive_players=P, player_id=P[0])
)
```
**Expected outputs**: `result is mock_result`, `is_default == False`, `coro.call_count == 1`  
**Priority**: HIGH

---

### UT-117
**Name**: Transient failure followed by success returns real result on retry  
**Module**: `call_with_retry_and_fallback`  
**Description**: When the coroutine raises on the first call then succeeds on the second, the function must ultimately return `(real_result, False)`.  
**Setup**:
```python
mock_result = object()
call_count = 0

async def flaky():
    nonlocal call_count
    call_count += 1
    if call_count == 1:
        raise RuntimeError("timeout")
    return mock_result

# Patch tenacity wait to zero to avoid sleeping in tests
from unittest.mock import patch
with patch("app.agent.retry.retry_llm_call.wait", return_value=0):
    result, is_default = asyncio.run(
        call_with_retry_and_fallback(lambda: flaky(), alive_players=P, player_id=P[0])
    )
```
**Expected outputs**: `result is mock_result`, `is_default == False`, `call_count == 2`  
**Priority**: HIGH

---

### UT-118
**Name**: All attempts fail — fallback `AgentResponse` is returned with `is_default == True`  
**Module**: `call_with_retry_and_fallback` + `build_default_response`  
**Description**: When the coroutine always raises, after exhausting all retries the function must return `(AgentResponse, True)` with the sentinel private_reasoning.  
**Setup**:
```python
async def always_fails():
    raise RuntimeError("LLM down")

with patch("app.agent.retry.retry_llm_call", side_effect=RuntimeError("LLM down")):
    # or set stop=stop_after_attempt(1) to speed up
    result, is_default = asyncio.run(
        call_with_retry_and_fallback(always_fails, alive_players=P, player_id=P[0])
    )
```
**Expected outputs**:
- `is_default == True`
- `result.private_reasoning == "[DEFAULT] All LLM retries exhausted."`
- `result.public_statement == "I need more time to think about this."`
- `result.bid_level == 1`
- `result.vote_target in P[1:]` (not self, not None)  
**Priority**: HIGH

---

### UT-119
**Name**: `build_default_response` vote_target excludes the requesting player  
**Module**: `build_default_response`  
**Description**: The fallback helper must never include the player's own ID as a vote target, even if it appears in `alive_players`.  
**Input**:
```python
from app.agent.retry import build_default_response
response = build_default_response(alive_players=P, player_id=P[0])
```
**Expected output**: `response.vote_target != P[0]` and `response.vote_target in P[1:]`  
**Priority**: MEDIUM

---

### UT-120
**Name**: `build_default_response` with no other alive players sets `vote_target` to `None`  
**Module**: `build_default_response`  
**Description**: If the requesting player is the only survivor, there are no valid targets — the fallback must return `vote_target=None` rather than crashing.  
**Input**: `build_default_response(alive_players=[P[0]], player_id=P[0])`  
**Expected output**: `response.vote_target is None`  
**Priority**: MEDIUM

---

## Updated test execution notes

6. **Phase 2 tests** (UT-071 through UT-120) are all pure-logic — no database, no network. Run with `pytest -m "not integration"`.

7. **Retry tests** (UT-116 through UT-118) use `unittest.mock.AsyncMock` and `unittest.mock.patch`. To avoid tenacity's real exponential sleep, patch `wait` to `wait_none()` or configure `stop=stop_after_attempt(1)` in a test-only decorator.  
   ```python
   from tenacity import wait_none
   from unittest.mock import patch
   with patch.object(retry_llm_call, "wait", wait_none()):
       ...
   ```

8. **Technique file tests** (UT-096 through UT-100) require the `persuasion-techniques/` directory to be present at project root (already committed). Always call `clear_cache()` in the test fixture `setup`/`teardown` to avoid cross-test pollution from the module-level `_cache` dict.
