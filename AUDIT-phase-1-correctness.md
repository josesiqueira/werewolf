# Audit — Phase 1 — Correctness

## Verdict: FIX REQUIRED

---

## Issues Found

### CRITICAL

**1. `game_loop.py:401` — Mayor succession triggered incorrectly when `mayor_id is None`**

```python
if killed_pid == game_state.mayor_id or game_state.mayor_id is None:
```

The condition `or game_state.mayor_id is None` fires succession logic every night as long as no mayor is set, even when the killed player was NOT the mayor. After `eliminate_player()` runs inside `resolve_night()`, it clears `mayor_id` (game_state.py:192-193) when the killed player IS the mayor. So the correct check after elimination is simply `game_state.mayor_id is None`. But the current code also triggers succession when `mayor_id` was already `None` before the kill (e.g., in a hypothetical state where mayor was never set). More concretely: this condition is fine in isolation, but the semantics are misleading — `game_state.mayor_id` is always set after the election, so after a non-mayor kill it will still be non-None, making the `or` branch dead. However, this creates a latent bug if `mayor_id` is ever None at night-kill time for any reason: it would trigger an unintended succession. **Severity: MEDIUM in practice, CRITICAL in principle.**

---

**2. `game_loop.py:317` — Two werewolves overwrite each other's target; last writer wins, no consensus**

```python
wolf_target = target  # last wolf target wins (or consensus)
```

Both werewolves choose targets independently. The loop iterates over all alive players and whichever wolf runs last overwrites `wolf_target`. This means wolf 1's choice is silently discarded. The comment says "or consensus" but no consensus logic is implemented. This is a design-level gap: the two wolves may have chosen different targets, but only the last-iterated wolf's choice is used. This is not documented as intended behavior anywhere in PLAN.md or SPEC.md.

- **File**: `backend/app/engine/game_loop.py`, line 317
- **Severity**: MEDIUM

---

**3. `game_loop.py` — GameStateMachine's `transition_to_next_phase()` is never called; state machine is partially bypassed**

`GameStateMachine` is initialized and used for player tracking, but `transition_to_next_phase()` is never invoked from `game_loop.py`. The game loop manually sets `game_state.current_round` (line 299) but never updates `game_state.current_phase`. The `current_phase` stays at `INIT` throughout the entire game loop. Consequently:
- `game_state.current_phase` is always `INIT` in agent-visible state (returned from `_build_game_state`)
- `game_state.debate_turn_count` is never updated via the state machine
- Win conditions are checked correctly via the external `check_win_condition()` function, but the state machine's own phase tracking is dormant

The acceptance criterion "State machine transitions through all phases in correct order" is **not met** — the state machine transitions never fire.

- **File**: `backend/app/engine/game_loop.py`, lines 298-620
- **Severity**: CRITICAL

---

**4. `game_loop.py` — Seer investigation result never stored in `game_state.seer_results`**

`resolve_night()` returns a `NightResult` with a `seer_result` field. The game loop correctly persists the seer result to `NightAction.seer_result` (line 376), but never calls `game_state.seer_results.append(SeerResult(...))`. Consequently, when the seer agent calls `get_state_for_agent()` (game_state.py:240), it always receives an empty `seer_results` list — it cannot use past investigation results to make informed decisions. While this affects mock agents less, it is a correctness bug: the seer's private state is incorrect.

- **File**: `backend/app/engine/game_loop.py` — missing `game_state.seer_results.append(...)` after `resolve_night()`
- **Severity**: CRITICAL (acceptance criterion: "Seer receives correct role of investigated player" — the seer agent never sees this information in its game state)

---

**5. `vote.py` — Re-vote logic missing from the spec**

PLAN.md Task 9 states: "If no majority and no tie (3+ way split), re-vote once then no elimination." The `tally_votes()` function correctly identifies 3+ way splits and returns `eliminated_player=None`, but the game loop (`game_loop.py:527`) simply accepts the result and moves on with no re-vote attempt. There is no second-vote round implemented.

- **File**: `backend/app/engine/game_loop.py`, line 527 (vote tallying section)
- **Severity**: MEDIUM

---

**6. `game_loop.py:522` — `is_mayor_tiebreak` is always `False` in `Vote` records**

```python
db_session.add(Vote(
    ...
    is_mayor_tiebreak=False,
    ...
))
```

Individual vote records are written before `tally_votes()` is called. After tallying, if the mayor broke a tie, the corresponding vote record's `is_mayor_tiebreak` is never updated to `True`. The `VoteResult.was_tiebreak` field is computed and available but ignored for DB persistence.

- **File**: `backend/app/engine/game_loop.py`, lines 515-524
- **Severity**: MEDIUM

---

**7. `game_state.py:142-144` — Max-rounds fallback defaults to villagers win, spec says "discarded"**

```python
elif self.current_round >= self.max_rounds:
    self.winner = self.check_win_condition() or "villagers"
    self.current_phase = GamePhase.GAME_OVER
```

When the state machine's `transition_to_next_phase()` is called after round 10, it defaults the winner to `"villagers"` if `check_win_condition()` returns `None`. But PLAN.md acceptance criterion states: "Game marked as **discarded** after 10 rounds without resolution." SPEC.md similarly says "unresolved games marked as discarded." The game loop correctly sets `status="discarded"` and `winner=None` (line 602-603), but the state machine's own fallback logic is wrong — it would set a winner when there is none. Since the state machine's `transition_to_next_phase()` is never called from the game loop (Issue #3), this bug is currently dormant but would trigger if the state machine is ever used directly.

- **File**: `backend/app/engine/game_state.py`, line 144
- **Severity**: MEDIUM (dormant due to Issue #3, but incorrect)

---

**8. `game_loop.py:591` — `rounds_played` written mid-loop but overwritten in finalise block; off-by-one possible**

`game.rounds_played = round_num` is written at line 591 (end of each iteration), then overwritten at line 599 (`game.rounds_played = game_state.current_round`). Since `game_state.current_round` is set to `round_num` at line 299, and `game_state.current_round` is never incremented by the game loop (the state machine is not used), the final value will equal whatever the last `round_num` was when the winner was found — which is correct. However, if the game ends by night-kill (via `break` at line 429), then `game.rounds_played = round_num` at line 591 is never reached for that round, and the finalise block sets it from `game_state.current_round` which IS `round_num` (set at line 299 before the night phase). This is actually correct. No off-by-one, but the redundant write at line 591 is misleading and `rounds_played` is not updated after a night-kill break (line 429) before the finalise block — the finally block at line 599 corrects it. **No functional bug here, but code clarity issue.**

- **Severity**: LOW

---

### MEDIUM

**9. No pytest test suite — `tests/` directory does not exist**

PLAN.md lists 7 test files that must be created (`tests/test_game_state.py`, `test_night.py`, `test_mayor.py`, `test_day.py`, `test_vote.py`, `test_game_loop.py`, and `tests/conftest.py`). None of these files exist. The first acceptance criterion is "pytest passes" — this cannot be verified because there are no tests. The game logic can only be audited by code review, not executed tests.

- **File**: `backend/tests/` — missing entirely
- **Severity**: CRITICAL (acceptance criterion explicitly requires `pytest` to pass)

---

**10. `schemas/` — Missing `NightActionResponse`, `VoteResponse`, `GameEventResponse` schemas**

PLAN.md Task 3 specifies these response schemas must exist. The schemas directory only contains `game.py`, `player.py`, `turn.py`, `agent.py`. There are no schemas for `NightAction`, `Vote`, or `GameEvent`. API endpoints for `GET /api/games/:id/turns` returns turns correctly, but if any endpoint were to return night actions or votes, it would use raw dicts without Pydantic validation.

- **File**: `backend/app/schemas/` — missing `night_action.py`, `vote.py`, `game_event.py`
- **Severity**: MEDIUM

---

**11. `game_loop.py` — State machine's `current_phase` not updated; agents always see `INIT` as current phase**

When `_build_game_state()` returns the phase (line 84-88), it reads `game_state.current_phase.value`. Since the state machine phase is never advanced (Issue #3), every agent turn receives `"INIT"` as the current phase regardless of whether it's night, day, or vote. This corrupts agent decision-making context (for LLM agents in Phase 2).

- **File**: `backend/app/engine/game_loop.py`, line 84-88
- **Severity**: MEDIUM (low impact on mock agents, high impact on LLM agents)

---

**12. `mayor.py:47` — Tiebreak considers only `candidates` list, not actual vote-recipients**

```python
top_candidates = [c for c in candidates if counts[c] == max_votes]
```

If a voter votes for someone not in `candidates`, that vote is counted by `Counter(votes.values())` but the `top_candidates` filter only considers players in the `candidates` list. This means write-in votes are silently counted but the write-in winner could be excluded from consideration. In practice, mock agents vote from `candidates`, so this is low risk now but a latent bug.

- **File**: `backend/app/engine/mayor.py`, line 47
- **Severity**: LOW

---

### LOW

**13. `game_loop.py:254-256` — Mayor campaign turns recorded with `round_number=0`**

Campaign turns use `round_number=0`. The SPEC.md schema does not reserve `0` for pre-game rounds. This is a minor design choice deviation but may complicate analytics queries that filter by `round_number >= 1`.

- **File**: `backend/app/engine/game_loop.py`, lines 254, 287
- **Severity**: LOW

---

**14. `night_action.py:39` — `kill_successful` defaults to `True` (server_default)**

```python
kill_successful: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

The ORM column and migration (line 148-150 of migration) both default `kill_successful` to `true`. If a row were ever inserted without explicitly setting this field, it would record a false "successful kill." The game loop always provides the correct value, so no actual bug fires — but the safer default would be `False`.

- **File**: `backend/app/models/night_action.py`, line 39; `backend/alembic/versions/001_initial_schema.py`, line 149
- **Severity**: LOW

---

**15. `game_loop.py` — `GameStateMachine.debate_turn_count` not updated by game loop**

The state machine has `debate_turn_count` and increments it in `transition_to_next_phase()` (game_state.py:129), but since the game loop never calls `transition_to_next_phase()`, `debate_turn_count` stays 0. The game loop correctly uses its own `turn_idx` variable to cap the debate at `debate_cap` turns. This means `get_state_for_agent()` always returns `"debate_turn_count": 0` to agents.

- **File**: `backend/app/engine/game_loop.py` — missing state machine sync for `debate_turn_count`
- **Severity**: LOW (does not affect game play with mock agents, affects LLM agents)

---

## Verified Criteria

- **Role distribution (2W, 1S, 1D, 3V)**: PASS — `roles.py` defines exactly `["werewolf", "werewolf", "seer", "doctor", "villager", "villager", "villager"]` and enforces 7-player count with a `ValueError`.

- **Night resolution: doctor save prevents kill**: PASS — `night.py:58-64` correctly returns `kill_successful=False` when `doctor_target == wolf_target`.

- **Night resolution: unprotected target eliminated**: PASS — `night.py:67-72` eliminates the wolf target and returns `kill_successful=True`.

- **Mayor election produces exactly one mayor via plurality**: PASS — `mayor.py:run_mayor_election()` correctly uses `Counter`, finds max votes, and random-breaks ties from the `candidates` list. One winner always returned.

- **Mayor succession assigns new mayor when eliminated**: PASS — `mayor.py:handle_mayor_succession()` correctly finds eligible successors and falls back to random choice. The game loop invokes it correctly on both night kills (line 403) and vote eliminations (line 563).

- **Day bidding: highest bidder selected, ties by mention priority**: PASS — `day.py:select_speaker()` correctly implements: max bid → mention priority (ordered list) → random. Logic is sound.

- **Debate capped at 10 turns**: PASS — `game_loop.py:437` uses `for turn_idx in range(debate_cap)` where `debate_cap` defaults to `MAX_DEBATE_TURNS = 10`. Hard cap enforced correctly.

- **Vote elimination: majority eliminates; mayor breaks 2-way tie**: PASS — `vote.py:tally_votes()` correctly handles plurality, 2-way tie with mayor tiebreak, and 3+-way split → no elimination.

- **Win condition: all wolves dead → villagers win**: PASS — `vote.py:check_win_condition()` returns `"villagers"` when `wolf_count == 0`. Game loop checks after both night and vote phases.

- **Win condition: wolves >= villagers → wolves win**: PASS — `vote.py:check_win_condition()` returns `"werewolves"` when `wolf_count >= non_wolf_count`.

- **Game cap at 10 rounds → discarded**: PASS — `game_loop.py:601-604` correctly sets `status="discarded"` and `winner=None` when the loop completes without a winner.

- **NDJSON export produces valid output**: PASS — `export.py:export_game_ndjson()` queries turns ordered by round/created_at, builds a complete record dict per turn, and joins with `json.dumps()` + `"\n"`. Output is valid NDJSON.

- **Database models match SPEC.md schema**: PASS — All 6 tables (`games`, `players`, `turns`, `night_actions`, `votes`, `game_events`) are implemented with correct column names, types, nullability, and UUID primary keys. JSONB used for `config` and `details`. Alembic migration matches the ORM models.

- **API endpoints implemented**: PASS (with caveats) — All required endpoints exist:
  - `POST /api/games` ✓
  - `GET /api/games` ✓ (with status, winner, is_degraded filters)
  - `GET /api/games/:id` ✓
  - `GET /api/games/:id/turns` ✓
  - `GET /api/export/:format` ✓ (ndjson only)
  - `GET /api/games/:id/replay` ✓ (bonus endpoint, not in original PLAN but in SPEC)

- **Pydantic schemas validate correctly**: PASS — `GameCreate`, `GameResponse`, `GameStateResponse`, `PlayerResponse`, `TurnResponse`, `AgentResponse` (with `DeceptionLabel` enum) are all present and correctly typed. `AgentResponse` properly enforces `bid_level` 0-4 and `confidence` 1-5 ranges.

- **Async SQLAlchemy 2.0 pattern used correctly**: PASS — `async_sessionmaker`, `AsyncSession`, `await session.execute(select(...))`, `session.add()`, `await session.flush()` all used correctly. Session dependency in `database.py` auto-commits on success.

---

## Summary Table

| # | Issue | File | Severity |
|---|-------|------|----------|
| 1 | Mayor succession condition also fires when `mayor_id is None` for unrelated reasons | `game_loop.py:401` | MEDIUM |
| 2 | Two wolves overwrite each other's target silently | `game_loop.py:317` | MEDIUM |
| 3 | `transition_to_next_phase()` never called; state machine phase always `INIT` | `game_loop.py` | CRITICAL |
| 4 | Seer results never added to `game_state.seer_results` | `game_loop.py` | CRITICAL |
| 5 | Re-vote on 3-way split not implemented | `game_loop.py` | MEDIUM |
| 6 | `is_mayor_tiebreak` always `False` in vote records | `game_loop.py:522` | MEDIUM |
| 7 | State machine max-round fallback assigns villager win instead of discard | `game_state.py:144` | MEDIUM |
| 8 | `rounds_played` redundant write; no functional bug | `game_loop.py:591` | LOW |
| 9 | `tests/` directory missing — no pytest suite | `backend/tests/` | CRITICAL |
| 10 | Missing `NightActionResponse`, `VoteResponse`, `GameEventResponse` schemas | `backend/app/schemas/` | MEDIUM |
| 11 | Agents always see phase `"INIT"` in game state | `game_loop.py:84` | MEDIUM |
| 12 | Mayor election ignores write-in votes outside candidates list | `mayor.py:47` | LOW |
| 13 | Mayor campaign turns use `round_number=0` | `game_loop.py:254` | LOW |
| 14 | `kill_successful` defaults to `True` in model/migration | `night_action.py:39` | LOW |
| 15 | `debate_turn_count` always 0 in agent state | `game_loop.py` | LOW |
