# Phase 3 Audit — Game Runner

**Verdict: FIX REQUIRED**

Date: 2026-04-03
Auditor: Tester Agent

---

## Summary

Phase 3 implements the batch execution system across six files plus schema, migration, and API. The core logic is largely correct: profile assignment balance is verified to work, progress tracking is coherent, quality checks use the right thresholds, and the background task pattern is sound. However, three defects require fixes before Phase 3 can be considered complete.

---

## Acceptance Criteria Results

### 1. Profile Assignment Balance — PASS

Verified mathematically and by simulation. With 210 games (7 profiles × 4 roles), all targets divide evenly (werewolf: 60 per profile, seer: 30, doctor: 30, villager: 90 — all remainders = 0). The greedy Latin-square algorithm in `assignment.py` achieves max deviation of ±1 across 100 random seeds tested. Acceptance criterion is ±2, so this is well within bounds.

### 2. Batch Runs N Games — PASS

`run_batch()` in `batch.py` correctly:
- Generates the assignment plan
- Creates the Batch record with plan stored in `config.assignment_plan`
- Calls `_execute_games()` which iterates through the plan
- Finalises with status "completed" or "failed"

`_run_single_game()` correctly creates agents, builds game config, calls `run_game()`, links the game to the batch via `game.batch_id = batch.id`, and updates counters.

### 3. Concurrent Execution with Semaphore — DEFECT (HIGH)

**File:** `backend/app/runner/batch.py`, `_execute_games()` (lines 307–347)

When `max_parallelism > 1`, all concurrent game coroutines share a single `AsyncSession` passed from the caller. SQLAlchemy's `AsyncSession` is not designed for concurrent coroutine access. Coroutines interleave at every `await` point — including `db_session.add()`, `db_session.flush()`, and `run_game()`'s many awaited DB operations. This can silently corrupt session state, cause incomplete writes, or raise `InvalidRequestError`.

The code itself acknowledges this problem in a comment for the sequential path: _"simpler and avoids session concurrency issues"_ — but the concurrent path does not resolve it.

**Fix required:** Each concurrent game coroutine must use its own session, created via `async_session_factory()` and committed independently.

### 4. Progress Tracking — PASS

`ProgressTracker` in `progress.py` correctly tracks:
- `current_game` (updated on start and on completion)
- `completion_pct` = finished / total × 100
- `eta_seconds` = rolling average duration × remaining games (20-game window)
- `games_per_minute` = finished / elapsed × 60
- Logs every 10 games via milestone check

`threading.Lock` is safe here because no `await` call occurs while the lock is held (all operations inside `update()` and `get_status()` are pure Python arithmetic).

### 5. Resumption Logic — PASS (with caveat)

`resume_batch()` correctly:
- Finds the batch by ID
- Validates status is "running" or "paused"
- Counts completed+discarded games
- Marks all `status="running"` games as "discarded"
- Recovers assignment plan from `batch.config["assignment_plan"]`
- Resumes from `start_index = completed_count`

**Caveat:** The `start_index` relies on games completing in sequential order. With `max_parallelism > 1` (already flagged as defective), completion order is non-deterministic, so resume would use the wrong start index. This is a secondary consequence of defect #3 above.

For `max_parallelism = 1` (the only safe mode currently), resumption is correct.

### 6. Degraded Games Tracked and Warning at 20% — PASS

`QualityTracker` in `quality.py` uses `DEGRADED_THRESHOLD = 0.20`. After every `record_game()` call, if `degraded / (completed + discarded) > 0.20`, a warning is logged. The final `log_summary()` emits the full batch summary with `degraded_rate_pct`.

Per-game degradation is set in `game_loop.py` at >30% default responses. Per-batch warning fires at >20% degraded games. Both thresholds match the specification.

### 7. API Endpoints Return Correct Data — PASS (with minor gap)

All three endpoints are present and correctly wired in `main.py`:
- `POST /api/batch` → creates Batch with status "pending", schedules background task, returns 202
- `GET /api/batch/{id}/status` → returns live ProgressTracker data if running, or DB data if not
- `GET /api/batch` → returns all batches ordered by creation date

The status endpoint returns a raw dict (not a Pydantic schema), which is acceptable but inconsistent with the other endpoints. The response shape is correct.

### 8. Assignment Plan Stored in Batch Config for Resumption — PASS

Both code paths store the plan:
- `run_batch()`: stores plan in `batch.config["assignment_plan"]` at creation time
- `_run_batch_background()`: generates plan and writes it into `batch.config` before execution

`resume_batch()` reads it back with fallback regeneration if missing.

### 9. Integration: Batch Runner Correctly Creates Agents and Calls run_game — PASS

`_create_agents()` correctly creates `MockAgent` instances for `use_llm=False`, or dynamically imports and instantiates `LLMAgent` for `use_llm=True` (deferred import avoids circular imports). `_build_game_config()` correctly maps player IDs to profiles and personas. `run_game()` receives the 7-agent list and config dict.

### 10. Import Chain: No Circular Imports — PASS

Import graph:
- `app.api.batch` → `app.runner.batch` → `app.runner.{assignment,progress,quality}`, `app.engine.{agent_interface,game_loop}`, `app.models.{batch,game}`
- `app.runner.assignment` → `app.agent.personas` (no cycle)
- `app.agent.llm_agent` is imported lazily inside a function (avoids circular dependency)

No circular import detected.

### 11. Batch Model Migration — PASS (with minor note)

`002_add_batches.py` correctly:
- Creates `batches` table with all required columns: id (UUID PK), created_at, total_games, completed_games, failed_games, status, config (JSONB), started_at, completed_at
- Adds `batch_id` FK column to `games` with `ondelete="SET NULL"`
- `down_revision = "001_initial"` correctly links to Phase 1 migration

**Minor note:** `Batch.games` relationship in `batch.py` uses `cascade="all, delete-orphan"`, which is semantically contradictory with the `ondelete="SET NULL"` FK. `delete-orphan` means SQLAlchemy will attempt to DELETE a Game if it is removed from `batch.games` via the ORM collection. The FK says the DB should only SET NULL. In practice this cascade is never triggered (the runner sets `game.batch_id` directly, not via the relationship), but the mismatch is a latent correctness risk and should be changed to `cascade="save-update, merge"` or the FK changed to `CASCADE`. Not blocking for current usage, but should be fixed.

### 12. Background Task Execution — PASS

The background task correctly uses its own independent session (`async with async_session_factory() as db`). Timing is safe: FastAPI commits the request session (which includes the initial Batch flush) before background tasks run, so the background task reads a committed batch record. The task commits at the end and rolls back on exception.

---

## Test Coverage — FAIL

The following test files are listed in the PLAN as required but do not exist:
- `backend/tests/test_assignment.py` — MISSING
- `backend/tests/test_batch.py` — MISSING
- `backend/tests/test_progress.py` — MISSING

The acceptance criterion explicitly includes: "Test profile assignment balance (over 100 mock games, each profile × role count within +/-2 of mean), test resumption, test progress calculation, test quality check thresholds." None of these tests exist.

---

## NDJSON Batch Export — PARTIAL FAIL

`export_batch_ndjson()` exists in `app/engine/export.py` and works correctly. However, no API endpoint exposes batch-scoped NDJSON export. The `/api/export/ndjson` endpoint exports all completed games system-wide but has no `batch_id` query parameter. The acceptance criterion is "NDJSON export works for full batch (all games)." The function works but is not reachable via API for a specific batch.

---

## Defect Register

| # | Severity | File | Description |
|---|----------|------|-------------|
| 1 | HIGH | `app/runner/batch.py` `_execute_games()` | Concurrent games share one AsyncSession — unsafe for max_parallelism > 1 |
| 2 | MEDIUM | `app/models/batch.py` | `Batch.games` uses `cascade="all, delete-orphan"` but FK is `ondelete=SET NULL` — contradictory |
| 3 | MEDIUM | `backend/tests/` | Three Phase 3 test files missing: test_assignment.py, test_batch.py, test_progress.py |
| 4 | LOW | `app/api/export.py` | No `batch_id` query param on `/api/export/ndjson` — batch-scoped export unreachable via API |

---

## What Works Well

- Profile assignment algorithm is elegant and provably correct
- Progress tracker design (rolling average ETA, milestone logging) is solid
- Quality tracker correctly separates per-game and per-batch thresholds
- Resumption logic covers the interrupted-game-discard requirement fully
- Background task pattern with separate session is the right approach
- Import organization is clean with no circular imports
- Migration is correct and reversible
