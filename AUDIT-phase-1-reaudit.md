# Re-Audit — Phase 1

## Verdict: FIX REQUIRED

Two issues prevent a clean pass: one pre-existing phase-transition mismatch between `game_loop.py` and `game_state.py` (present in the debate loop) and a redundant-but-harmless expression in Bug 6. All other fixes are correctly implemented.

---

## Fix Verification

### Fix 1 — `transition_to_next_phase()` called at correct points
**PARTIALLY VERIFIED / REGRESSION PRESENT**

The five call-sites added are correct for the phases they cover:
- Line 246: INIT → MAYOR_CAMPAIGN ✓
- Line 260: MAYOR_CAMPAIGN → MAYOR_VOTE ✓
- Line 307: → NIGHT (top of each round) ✓
- Line 493: NIGHT → DAY_BID ✓
- Line 558: intended to transition to VOTE ✗ (see Regressions section)

The debate loop (lines 497–553) never calls `transition_to_next_phase()` internally, so the state machine stays stuck at DAY_BID throughout all bid/speech turns. When the loop exits and line 558 calls `transition_to_next_phase()`, the state machine transitions DAY_BID → DAY_SPEECH (not VOTE, as intended). The state machine never naturally reaches VOTE through this path, leaving `current_phase` incorrect for the rest of the round and every subsequent round.

### Fix 2 — Seer results stored in `game_state.seer_results` after night
**VERIFIED**

Lines 415–420 in `game_loop.py`:
```python
if night_result.seer_result and seer_target:
    game_state.seer_results.append(SeerResult(
        target_id=night_result.seer_result["target_id"],
        role=night_result.seer_result["role"],
        round_number=round_num,
    ))
```
`SeerResult` dataclass exists in `game_state.py` (line 56–60). `game_state.seer_results` is initialised as an empty list (line 89). The `get_state_for_agent` method correctly exposes `seer_results` to the seer role (lines 242–249). The fix is complete and correct.

### Fix 3 — Wolf consensus implemented (agree → use target, disagree → random)
**VERIFIED**

Lines 393–407 correctly implement:
- Single wolf: use that target directly.
- Multiple wolves, unanimous: use the agreed target, log agreement.
- Multiple wolves, split: `random.choice(wolf_targets)` picks one, logs disagreement.

The logic is sound and handles all cases.

### Fix 4 — Re-vote on 3+ way split implemented
**VERIFIED**

Lines 605–651 implement a complete re-vote when `eliminated_id is None` after the first tally:
- A second full vote round is conducted with `revote_map`.
- The re-vote is tallied via `tally_votes`.
- Re-vote records are persisted with phase `"revote"`.
- If the re-vote also fails to produce an elimination, it logs and skips elimination gracefully.

The implementation is correct.

### Fix 5 — `is_mayor_tiebreak` set correctly from `vote_result.was_tiebreak`
**VERIFIED**

Lines 589–600 (first vote) and lines 632–644 (re-vote) both set:
```python
is_mayor_tiebreak=(
    vote_result.was_tiebreak and voter_id == game_state.mayor_id
),
```
`VoteResult.was_tiebreak` is correctly defined in `vote.py` (line 17) and set accurately in `tally_votes` — `True` only when the mayor's vote resolved a two-way tie (line 66). The fix correctly scopes the flag to only the mayor voter.

### Fix 6 — Round-cap returns "discarded" not "villagers"
**VERIFIED (with minor code-quality note)**

`game_state.py` line 145:
```python
self.winner = self.check_win_condition() or "discarded"
```
At this branch point `check_win_condition()` was already called at line 138 and returned `None` (otherwise the `if win is not None` branch at line 139 would have been taken). Therefore `check_win_condition()` at line 145 is guaranteed to return `None`, and `self.winner` will always be `"discarded"`. The intended semantics are correct — the round cap results in "discarded", not "villagers". The redundant call to `check_win_condition()` is harmless but confusing; it could simply be `self.winner = "discarded"`.

Additionally, `game_loop.py` lines 725–727 set `game.status = "discarded"` and `game.winner = None` when the loop exits without a winner, which is consistent and correct at the DB record level.

### Fix 7 — `extract_mentions` uses agent names, maps back to IDs
**VERIFIED**

Lines 542–553 build `alive_names` (list of agent name strings) and `name_to_id` (name→player_id dict), then pass `alive_names` to `extract_mentions`, and map the returned names back to player IDs for `previous_mentions`. This correctly matches the signature of `extract_mentions(statement, player_names)` in `day.py` (line 12), which expects name strings, not UUIDs. The fix is complete and correct.

### Fix 8 — New schemas: `NightActionResponse`, `VoteResponse`, `GameEventResponse` exist
**VERIFIED**

All three schemas are present and correctly defined:
- `/backend/app/schemas/night_action.py`: `NightActionResponse` with `from_attributes=True`, all relevant fields including `kill_successful: bool`.
- `/backend/app/schemas/vote.py`: `VoteResponse` with `is_mayor_tiebreak: bool`.
- `/backend/app/schemas/game_event.py`: `GameEventResponse` with `details: dict[str, Any] | None`.

All three are exported from `/backend/app/schemas/__init__.py` (lines 3–7, 13–19). Correct.

### Fix 9 — Wolf target validated as non-wolf
**VERIFIED**

Lines 315–338: `wolf_player_ids` is built from alive wolves. After `agent.night_action` returns a target, if `target in wolf_player_ids` the code reassigns to a random non-wolf alive player and logs a warning. The validation runs before appending to `wolf_targets`, so the consensus logic (Fix 3) always operates on validated targets. Correct.

### Fix 10 — Seer target validated as alive
**VERIFIED**

Lines 354–364: after `agent.night_action` returns a seer target, if `target not in game_state.alive_players` the code reassigns to a random other alive player and logs a warning. The validated target is then stored in `seer_target` and used for both the investigation result and DB persistence. Correct.

### Fix 11 — `requirements.txt` includes pytest packages
**VERIFIED**

`/backend/requirements.txt` lines 13–15:
```
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
```
All three test packages are pinned to specific versions. Correct.

---

## Regressions

### R1 — Phase-transition mismatch in the debate loop (CRITICAL)

**File**: `game_loop.py` lines 493–558 vs `game_state.py` lines 125–134

The debate loop (for `turn_idx in range(debate_cap)`) processes bids and a speech each iteration but never calls `transition_to_next_phase()` inside the loop. The state machine therefore remains at `DAY_BID` for all debate turns.

After the loop, `game_state.transition_to_next_phase()` is called at line 558 with the comment `# -> VOTE`. However, because the state machine is still at `DAY_BID`, the transition resolves as `DAY_BID → DAY_SPEECH` (per `game_state.py` line 126), not `DAY_BID → VOTE`.

Consequences:
1. `current_phase` reported to agents during the vote is `DAY_SPEECH`, not `VOTE`.
2. At the start of the next round, line 307 calls `transition_to_next_phase()` intending `VOTE → NIGHT`. Instead it finds `DAY_SPEECH` and, because `debate_turn_count` is 0 (reset at NIGHT→DAY_BID), it transitions `DAY_SPEECH → DAY_BID`, not `DAY_SPEECH → VOTE`. This cascades incorrectly for all subsequent rounds.
3. The state machine's `max_rounds` check and `current_round` increment inside the VOTE branch (lines 142–149) are never triggered, so the round counter in the state machine drifts from the loop variable `round_num`.

**Root cause**: The state machine's DAY phase is designed as a bid/speech micro-loop managed entirely by phase transitions, but `game_loop.py` manages the debate loop manually without calling transitions, then calls a single transition expecting to skip directly to VOTE.

**Required fix**: Either (a) manage the debate loop entirely through the state machine by calling `transition_to_next_phase()` for each bid and speech sub-phase, or (b) bypass the state machine's DAY_BID/DAY_SPEECH states in the game loop and call `transition_to_next_phase()` only when the state machine is at NIGHT (→DAY_BID) and then advance directly from DAY_BID to VOTE by calling the transition twice (DAY_BID→DAY_SPEECH, DAY_SPEECH→DAY_BID repeated until DAY_SPEECH→VOTE) — or simplest: add a `force_phase` method that sets `current_phase = GamePhase.VOTE` directly before calling the vote logic.

### R2 — Night elimination not removed from `game_state.alive_players` before `transition_to_next_phase()` is called for the next round (minor)

**File**: `game_loop.py` lines 442–480 vs line 307

`resolve_night` calls `game_state.eliminate_player(wolf_target)` internally (night.py line 67), which correctly removes the player from `alive_players` before the state machine's `check_win_condition` runs at line 307's `transition_to_next_phase()`. This part is actually correct — no regression here. (Noted for completeness; not an issue.)

### R3 — `game_state.py` BUG-6 fix uses a redundant `check_win_condition()` call (cosmetic)

Line 145: `self.winner = self.check_win_condition() or "discarded"` — the inner `check_win_condition()` call is guaranteed to return `None` at this branch. The result is always `"discarded"` as intended, but the redundant call adds confusion. Not a functional bug, but a code clarity issue.
