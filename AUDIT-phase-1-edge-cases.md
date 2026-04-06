# Audit — Phase 1 — Edge Cases

**Audited by**: Tester Agent
**Date**: 2026-04-03
**Scope**: backend/app/engine/, backend/app/api/, backend/app/models/, backend/app/schemas/

---

## Verdict: FIX REQUIRED

Several medium and low severity issues found. No single issue is catastrophic, but two of them (re-vote missing, wolf-on-wolf target silent, mayor succession ordering) can silently produce wrong game outcomes.

---

## Issues Found

### CRITICAL

- **None found.**

---

### MEDIUM

#### ISSUE-1 — Re-vote not implemented (spec divergence)
**File**: `backend/app/engine/game_loop.py` (vote phase, ~line 526) and `backend/app/engine/vote.py`
**Description**: PLAN.md Task 9 states: *"If no majority and no tie (3+ way split), re-vote once then no elimination."* The implementation skips the re-vote entirely — a 3+ way split immediately results in no elimination with no second vote. The comment in `vote.py:69` says "3+ way split or unresolvable tie — no elimination" without any re-vote logic, and `game_loop.py` calls `tally_votes()` only once.
**Impact**: Game outcome differs from spec. In a 3-way split among 6 or 7 players, a round passes with no elimination when the spec requires one re-vote attempt first.
**Severity**: MEDIUM

#### ISSUE-2 — Wolf targeting another wolf: no validation or warning
**File**: `backend/app/engine/game_loop.py` lines 315–328; `backend/app/engine/night.py` lines 51–72
**Description**: When a wolf submits a `night_action` targeting another wolf (or even themselves), the code accepts it silently. There is no validation that `wolf_target` is a non-wolf player. `resolve_night()` will happily eliminate a wolf teammate if the doctor does not protect them. The `MockAgent` in `agent_interface.py:95–104` does exclude self from targets (`if pid != self.player_id`), but it does not exclude wolf teammates. A real LLM agent could accidentally or intentionally target a teammate.
**Impact**: A wolf-on-wolf kill is valid in some Werewolf variants but this project's PLAN and SPEC do not mention it. If it happens, the game could end in an unexpected villager win mid-round, and the event log would record a `werewolf_kill` on a werewolf with no special notation. The seer would also be able to investigate a dead player without error (see ISSUE-4).
**Severity**: MEDIUM

#### ISSUE-3 — Last-wolf-target-wins logic races silently with 2 wolves
**File**: `backend/app/engine/game_loop.py` lines 315–317
**Description**: With 2 wolves alive, both submit `night_action`. The code sets `wolf_target = target` for each wolf in iteration order — the *last* wolf's choice always wins. This means the first wolf's decision is silently discarded with no record. The `NightAction` DB record stores only one `wolf_target`. There is no coordination or consensus mechanism, and the discarded wolf choice is never logged. If wolves disagree (which LLM agents will), this produces confusing data: one wolf's Turn record shows `vote_target=X`, but the NightAction shows `wolf_target=Y`.
**Severity**: MEDIUM

#### ISSUE-4 — Seer can investigate dead players without error
**File**: `backend/app/engine/night.py` lines 45–48
**Description**: `resolve_night()` does not validate that `seer_target` is in `game_state.alive_players`. If the seer targets a player who is already dead (e.g., eliminated last round), the code still looks up their role via `game_state._player_roles.get(seer_target, "unknown")` and returns a valid `seer_result`. This silently accepts an illegal action. The result is a correct role but an invalid investigation target. No error is raised and no warning is logged.
**Impact**: Seer can "investigate" eliminated players (a logical error), which will silently produce misleading investigation records in the DB.
**Severity**: MEDIUM

---

### LOW

#### ISSUE-5 — Mayor succession before win condition check: ordering gap on night kill
**File**: `backend/app/engine/game_loop.py` lines 400–429
**Description**: After a night kill, the code checks `if killed_pid == game_state.mayor_id or game_state.mayor_id is None` and performs mayor succession **before** the win condition check at line 423. This ordering is correct for the night path. However, the condition on line 401 has a subtle bug: `game_state.mayor_id is None` is true not only when the killed player was mayor, but also hypothetically if the mayor was never set. In practice the mayor is always set before the first night, so this branch is unreachable — but the `or game_state.mayor_id is None` guard is confusing and could trigger in unexpected initialization states.
**For the vote path** (lines 559–581): succession is correctly triggered by checking `game_state.mayor_id is None` (the state machine clears `mayor_id` in `eliminate_player`), so succession happens after elimination and before the win condition check at line 583. This order is correct.
**Severity**: LOW (potential confusion / maintenance risk, not a runtime bug in the common path)

#### ISSUE-6 — Doctor self-protection: allowed with no validation
**File**: `backend/app/engine/night.py` lines 44–72; `backend/app/engine/game_loop.py` lines 344–356
**Description**: The doctor can target themselves (`doctor_target == doctor's own player_id`). The night resolution code checks `if doctor_target == wolf_target`, so a self-protecting doctor works correctly if wolves also target the doctor. Nothing in PLAN.md or the code forbids self-protection. This is a design question, not a bug, but it is undocumented and could be unintentional. PLAN.md Task 6 does not state whether self-protection is permitted.
**Severity**: LOW (design ambiguity, not a bug)

#### ISSUE-7 — All bids = 0: select_speaker still picks a speaker (correct), but no "pass" semantics
**File**: `backend/app/engine/day.py` lines 59–74; `backend/app/engine/game_loop.py` lines 447–448
**Description**: When all players bid 0, `select_speaker()` computes `max_bid = 0` and `top_bidders = [all alive players]`. It then falls through mention-priority and random selection — a speaker is always chosen. This is functionally correct (the loop always runs `debate_cap` turns), but PLAN.md Task 8 says "bid 0 = pass". If a bid of 0 means "I explicitly pass", a speaker should theoretically not speak when all have passed. The current implementation forces a speech regardless, which may be intentional (to prevent silent rounds) but diverges from the "pass" semantics implied by the PLAN.
**Severity**: LOW (design divergence, not a crash)

#### ISSUE-8 — `rounds_played` off by one when game ends after night kill
**File**: `backend/app/engine/game_loop.py` lines 591, 599
**Description**: When a win condition is detected after the night phase (before the vote), the loop `break`s without executing `game.rounds_played = round_num` (line 591). At finalization, line 599 sets `game.rounds_played = game_state.current_round` which is correct. However, when the win is detected after the **vote** phase (line 587–589), the `break` skips line 591 as well. In this case, `game_state.current_round` still equals `round_num` because line 299 assigns it at the top of the loop, so line 599 gives the correct value. Both paths are correct but the logic is non-obvious and the `game.rounds_played = round_num` at line 591 inside the loop serves no purpose if a win condition always leads to a `break` before reaching it — it only records progress for non-terminal rounds. This is low-risk but slightly redundant.
**Severity**: LOW (no functional bug, just confusing logic)

#### ISSUE-9 — NDJSON export of a game with 0 turns returns empty string (not valid NDJSON)
**File**: `backend/app/engine/export.py` lines 45–72
**Description**: If a game exists but has no Turn records (edge case: game crashed before turns were persisted, or a future game type), `export_game_ndjson()` returns `""` (empty string from `"\n".join([])`). The API endpoint in `export.py:57` returns `PlainTextResponse("")` for an empty batch. For a single-game export with no turns, it returns `PlainTextResponse("")` as well. An empty NDJSON file is technically valid (0 records), but callers expecting at least a newline or a header line may fail silently. This is a minor issue.
**Severity**: LOW

#### ISSUE-10 — `AgentResponse` dataclass vs Pydantic schema mismatch: `private_reasoning`/`public_statement` default
**File**: `backend/app/engine/agent_interface.py` lines 15–26 vs `backend/app/schemas/agent.py` lines 20–44
**Description**: The engine's `AgentResponse` dataclass has `private_reasoning: str = ""` and `public_statement: str = ""` (both default to empty string). The Pydantic schema `AgentResponse` in `schemas/agent.py` has `private_reasoning: str = Field(...)` and `public_statement: str = Field(...)` — both are **required** with no default (positional `...`). These are two different classes with the same name in different modules. The engine uses the dataclass version; the API schemas are never validated against actual agent output. If Phase 2 LLM agents return the Pydantic `AgentResponse` from schemas, required fields with `...` will raise validation errors if omitted. The dataclass in `agent_interface.py` permits empty strings, the schema does not.
**Severity**: LOW (latent Phase 2 issue; no runtime bug in Phase 1 with MockAgent)

#### ISSUE-11 — `vote_for_mayor` returns self when only one candidate
**File**: `backend/app/engine/agent_interface.py` lines 114–120
**Description**: `MockAgent.vote_for_mayor()` filters out self from candidates, but if `eligible` is empty (i.e., the only candidate is the voter themselves — mathematically impossible with 7 players but theoretically reachable with a custom `player_count`), it falls back to `eligible = candidates`, which includes self. Then `random.choice(candidates)` picks self. The `run_mayor_election()` function accepts votes for any candidate_id and does not validate that votes are not self-votes. This is only reachable with a non-standard configuration.
**Severity**: LOW

#### ISSUE-12 — Invalid UUID in API: `get_game` with non-existent UUID returns 404 correctly; malformed UUID raises 422
**File**: `backend/app/api/games.py` lines 109–126; `backend/app/api/export.py` lines 24–47
**Description**: FastAPI automatically validates `game_id: uuid.UUID` path/query parameters and returns HTTP 422 Unprocessable Entity for malformed UUIDs (non-UUID strings). For valid UUID format but non-existent game, `get_game` correctly returns HTTP 404 (line 120: `raise HTTPException(status_code=404, detail="Game not found")`). The export endpoint also validates existence (lines 43–47). The turns endpoint `get_game_turns` likewise returns 404 if game not found. **This is handled correctly**, though the 422 response body from FastAPI's automatic validation may be unexpected to API consumers who send e.g. `"invalid-id"`.
**Severity**: LOW (informational; behavior is correct per HTTP spec)

---

## Verified Edge Cases

- **3+ way vote split** — Handled in `vote.py:69`: no elimination returned. However, the **re-vote** step required by PLAN.md is missing (see ISSUE-1).
- **All wolves die simultaneously** — `check_win_condition()` in both `game_state.py:159` and `vote.py:77` returns `"villagers"` when `wolf_count == 0`. With 2 wolves: they can only be eliminated one at a time (night kills one target; vote eliminates one player per round). Simultaneous double-wolf elimination cannot happen in the current engine, and the win condition correctly handles `wolf_count == 0` regardless.
- **Doctor protects themselves** — Allowed silently. The comparison `doctor_target == wolf_target` in `night.py:58` works correctly if doctor_target is the doctor's own player_id. Not validated as forbidden or permitted by spec.
- **Seer investigates a dead player** — Accepted silently; returns their stored role with no error. See ISSUE-4.
- **Seer investigates a wolf teammate** — `night.py:47` looks up `_player_roles.get(seer_target)` and returns the true role `"werewolf"`. Correct behaviour.
- **All bids = 0** — `select_speaker()` picks a random speaker (max_bid=0, all tied, random choice). No crash. Debate always runs `debate_cap` turns. See ISSUE-7 for design note.
- **Debate with 0 bids > 0 (everyone passes at 0)** — Same as above: speaker is still chosen. See ISSUE-7.
- **Mayor eliminated — succession before win condition check** — Night path: succession happens at lines 400–421, win check at line 423 (correct order). Vote path: succession at lines 559–581, win check at line 583 (correct order). Succession always precedes win condition check.
- **Empty/null agent responses** — `AgentResponse` dataclass defaults cover all fields. `_record_turn()` in `game_loop.py:126–129` uses `response.private_reasoning or ""` and `response.public_statement or ""`. Vote target validation at lines 499–505 corrects None/invalid targets. No crash on null fields from MockAgent.
- **Exactly 2 players left (1 wolf, 1 villager)** — `check_win_condition()`: `wolf_count=1`, `non_wolf_count=1`, `wolf_count >= non_wolf_count` → `True` → returns `"werewolves"`. Parity correctly detected.
- **Game after round 10 — marked discarded** — `game_loop.py:600–604`: if `winner` is None after the for-loop, `game.status = "discarded"`, `game.winner = None`, `game.rounds_played = max_rounds`. Correct.
- **Wolf targets another wolf** — Not validated; kill proceeds if doctor does not protect the wolf target. See ISSUE-2.
- **NDJSON export with 0 turns** — Returns empty string `""`. Not a crash. See ISSUE-9.
- **API with non-existent UUID** — Returns HTTP 404 with `"Game not found"` for all relevant endpoints. Valid-format but non-existent UUIDs handled correctly.
- **API with malformed UUID** — FastAPI returns HTTP 422 automatically before the handler is called. Correct per HTTP spec.
- **Two-way tie where mayor voted for a tied candidate** — `vote.py:60–67`: correctly uses `votes.get(mayor_id)` and checks if it's in `top_targets`. Mayor tiebreak works.
- **Two-way tie where mayor did not vote for either tied candidate** — Falls through to "no elimination" path. Correct per spec.
- **Mayor is None during tiebreak** — `tally_votes()` receives `mayor_id=None`; the condition at line 60 (`mayor_id is not None`) is False, so tiebreak is skipped. No crash.
- **`assign_roles()` with wrong player count** — Raises `ValueError` immediately. Correct.
- **`run_mayor_election()` with no candidates** — Raises `ValueError("At least one candidate is required")`. Correct.
- **`handle_mayor_succession()` with no alive players** — Raises `ValueError("No alive players available for succession")`. Correct.
- **`select_speaker()` with empty bids** — Raises `ValueError("At least one bid is required")`. Correct.
- **`GameStateMachine.eliminate_player()` on already-dead player** — Guarded by `if player_id in self.alive_players`. Silent no-op. Correct.
- **`GameStateMachine.check_win_condition()` with unknown player_id in alive_players** — `_player_roles.get(pid)` returns `None`; alive_roles comprehension skips players not in `_player_roles` (line 163 `if pid in self._player_roles`). No crash, but also no role counted — slightly defensive.

---

## Summary Table

| # | Edge Case | Status | Severity |
|---|-----------|--------|----------|
| 1 | 3+ way vote split → re-vote | Missing re-vote | MEDIUM |
| 2 | Wolf targets wolf teammate | No validation | MEDIUM |
| 3 | Two wolves choose different targets | Last-wins, silent discard | MEDIUM |
| 4 | Seer investigates dead player | Accepted silently | MEDIUM |
| 5 | Doctor protects themselves | Allowed (spec ambiguity) | LOW |
| 6 | All bids = 0 | Speaker chosen anyway | LOW |
| 7 | Mayor succession ordering | Correct but confusing guard | LOW |
| 8 | NDJSON export with 0 turns | Returns "" (not a crash) | LOW |
| 9 | AgentResponse dataclass/schema mismatch | Latent Phase 2 risk | LOW |
| 10 | 2 players left (1 wolf, 1 villager) | Correctly detected | PASS |
| 11 | Game after round 10 | Correctly marked discarded | PASS |
| 12 | API with invalid UUID | 404/422 correctly returned | PASS |
| 13 | All wolves die (villagers win) | Correctly handled | PASS |
| 14 | Mayor elected → succession on death | Correct order | PASS |
| 15 | Seer investigates wolf teammate | Returns true role | PASS |
| 16 | Two-way tie + mayor tiebreak | Working | PASS |
