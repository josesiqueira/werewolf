# Audit — Phase 1 — Integration

## Verdict: FIX REQUIRED

Eight issues were found. Two are MEDIUM severity (missing test infrastructure, missing re-vote logic), four are LOW severity, and two are informational. No CRITICAL blockers — the game loop will run and produce valid database records — but the acceptance criteria cannot be verified without a test suite.

---

## Issues Found

### MEDIUM

- **`backend/` (missing):** `backend/tests/` directory does not exist. PLAN.md lists 6 test files (`test_game_state.py`, `test_night.py`, `test_mayor.py`, `test_day.py`, `test_vote.py`, `test_game_loop.py`) and a `conftest.py`, none of which were created. The acceptance criteria are entirely untested. Severity: MEDIUM.

- **`backend/requirements.txt` (all lines):** `pytest`, `pytest-asyncio`, and `pytest-cov` are absent from `requirements.txt`. Running `pytest` after `pip install -r requirements.txt` will fail immediately. STACK.md documents all three as required testing dependencies. Severity: MEDIUM.

- **`app/engine/game_loop.py:490–589` / `app/engine/vote.py`:** The re-vote mechanism specified in PLAN.md Task 9 is not implemented. PLAN.md states: *"If no majority and no tie (3+ way split), re-vote once then no elimination."* `tally_votes()` correctly returns `eliminated_player=None` on a 3-way split, but `game_loop.py` never calls `tally_votes` a second time. The game silently skips elimination with no re-vote. This is a specified acceptance criterion. Severity: MEDIUM.

### LOW

- **`backend/requirements.txt:7`:** `psycopg2-binary==2.9.10` is listed but is never imported or used anywhere in the codebase. All database connections — application and Alembic migrations — use `asyncpg` exclusively. The dead dependency wastes install time and adds a C-extension build requirement for no benefit. Severity: LOW.

- **`app/engine/game_loop.py:481–483`:** `extract_mentions(public_text, game_state.alive_players)` passes UUID strings as the `player_names` list. `extract_mentions()` does word-boundary regex matching on natural-language speech text; UUID strings will never appear there. As a result, `previous_mentions` is always empty, and the mention-priority tiebreak in `select_speaker()` always degrades to random. The spec requires mention-priority tiebreaking. The fix is to pass agent names (e.g., `[players[pid].agent_name for pid in game_state.alive_players]`) and map the result back to IDs. Severity: LOW.

- **`app/engine/game_loop.py:401`:** The condition `if killed_pid == game_state.mayor_id or game_state.mayor_id is None` contains dead code. `resolve_night()` calls `game_state.eliminate_player()` before this check, and `eliminate_player()` already clears `mayor_id` when the mayor is killed. By line 401, `killed_pid == game_state.mayor_id` is always `False`; only the second clause `game_state.mayor_id is None` ever fires. The logic produces the correct outcome but the first condition is misleading. Severity: LOW.

- **`app/engine/game_loop.py` (throughout):** `game_state.current_phase` is never updated from its initial value of `GamePhase.INIT`. `_build_game_state()` reads `game_state.current_phase` and includes it in the dict passed to agents, so every agent receives `"current_phase": "INIT"` regardless of the actual phase. `GameStateMachine.transition_to_next_phase()` is never called. With `MockAgent` this is harmless, but LLM agents in Phase 2 will receive incorrect phase context. Severity: LOW (Phase 1 impact: none; Phase 2 impact: HIGH).

### INFORMATIONAL

- **`app/engine/agent_interface.py` and `app/schemas/agent.py`:** Two independent `AgentResponse` classes exist with different field types. The engine's dataclass (`vote_target: str | None`) is used by `game_loop.py`. The Pydantic model (`vote_target: uuid.UUID | None`) is in `schemas/agent.py` and is not used anywhere in Phase 1. This is not a bug yet but will require reconciliation in Phase 2 when the LLM agent returns a Pydantic `AgentResponse` and game_loop expects the dataclass version.

- **`app/engine/game_loop.py:317`:** With two werewolves, `wolf_target` is overwritten by the second wolf's choice (`wolf_target = target  # last wolf target wins`). Both wolves independently pick random targets; the first wolf's choice is discarded. This is noted in a code comment and is acceptable for mock agents, but the two wolves may record different `night_kill` turns pointing to different targets while only one kill is actually resolved.

---

## Verified Items

- **Syntax:** All Python files (`app/`, `alembic/env.py`, `alembic/versions/001_initial_schema.py`) parse without syntax errors via `ast.parse`.

- **SQLAlchemy 2.0 compliance:** All six models use `mapped_column` (not `Column`), `Mapped[T]` type annotations, `DeclarativeBase`, and `async_sessionmaker` / `create_async_engine`. No legacy `Column` usage found.

- **Async session handling:** `database.get_session()` correctly uses `async with async_session_factory() as session`, commits on success, rolls back on exception. `run_game()` calls `db_session.flush()` before returning. No blocking sync calls inside async paths.

- **Pydantic v2 compliance:** All schemas use `model_config = ConfigDict(from_attributes=True)` (not `class Config`). `pydantic-settings` `BaseSettings` uses `model_config = SettingsConfigDict(...)`. No `from_orm()` calls found; `model_validate()` is not needed in Phase 1 (dict construction used throughout).

- **FastAPI async:** All endpoint functions in `app/api/games.py` and `app/api/export.py` are `async def`. `Depends(get_session)` is used correctly for all database sessions.

- **Import integrity:** No circular imports detected. `app/models/__init__.py` imports all six models. `alembic/env.py` imports all models to register with `Base.metadata`. `app/main.py` imports routers after app creation (post-init import pattern, acceptable).

- **`back_populates` consistency:** All bidirectional relationships are correctly paired: `Game.players ↔ Player.game`, `Game.turns ↔ Turn.game`, `Game.night_actions ↔ NightAction.game`, `Game.votes ↔ Vote.game`, `Game.events ↔ GameEvent.game`, `Player.turns ↔ Turn.player`. Unidirectional FK relationships (`Turn.vote_target_player`, `NightAction.wolf/doctor/seer_target_player`, `Vote.voter_player`, `Vote.target_player`) correctly omit `back_populates`.

- **Foreign key references:** All FK columns reference correct tables and columns. `ondelete="CASCADE"` on child tables, `ondelete="SET NULL"` on nullable target references. Correct in both ORM models and Alembic migration.

- **Alembic migration:** `001_initial_schema.py` creates all six tables (`games`, `players`, `turns`, `night_actions`, `votes`, `game_events`) with correct column types. `JSONB` used for `config` and `details`. UUID primary keys use `postgresql.UUID(as_uuid=True)`. `downgrade()` drops tables in correct reverse dependency order.

- **UUID handling:** `postgresql.UUID(as_uuid=True)` used throughout ORM models and migration. `game_loop.py` converts string player_ids to `uuid.UUID(pid)` before passing to `Turn`, `Vote`, `NightAction` constructors. Consistent.

- **`docker-compose.yml`:** PostgreSQL 16 service configured with user/password/db matching `DATABASE_URL` in `.env.example` and `alembic.ini`. Health check present. Named volume for persistence.

- **`.env.example`:** `DATABASE_URL` uses `postgresql+asyncpg://` (correct async driver). All required environment variables documented.

- **`.gitignore`:** Contains `_queries.cypher`, `.env`, `__pycache__/`, `.pytest_cache/`. Correct.

- **`app/config.py`:** Uses `pydantic-settings` `BaseSettings` with `SettingsConfigDict`. `DATABASE_URL` defaults to asyncpg URL. CORS origins are configurable.

- **`app/engine/roles.py`:** Correct distribution (2 werewolf, 1 seer, 1 doctor, 3 villager). `assign_roles()` validates exactly 7 players. `get_private_info()` correctly restricts werewolf teammate info.

- **`app/engine/game_state.py`:** `GameStateMachine` correctly tracks alive players, mayor, eliminated players, and seer results. `check_win_condition()` correctly tests wolf count vs non-wolf count. `eliminate_player()` correctly updates `mayor_id`.

- **`app/engine/night.py`:** Doctor save logic correct (`doctor_target == wolf_target → kill blocked`). Seer result correctly looks up role from `_player_roles`.

- **`app/engine/mayor.py`:** Plurality election with random tiebreak. `handle_mayor_succession()` validates successor is alive.

- **`app/engine/vote.py`:** `tally_votes()` implements plurality, mayor tiebreak on two-way tie, and no-elimination on 3+ way split. `check_win_condition()` correctly mirrors state machine logic.

- **`app/engine/export.py`:** NDJSON export queries players and turns with correct join logic. Output is valid JSON per line. `export_batch_ndjson()` delegates to `export_game_ndjson()`.

- **API endpoints:** All five required endpoints implemented: `POST /api/games`, `GET /api/games`, `GET /api/games/{id}`, `GET /api/games/{id}/turns`, `GET /api/export/{format}`. An additional `GET /api/games/{id}/replay` endpoint is included as a bonus.

- **`openai` and `tenacity` in requirements:** Listed for Phase 2 readiness. Not used in Phase 1 code but not harmful.

- **`asyncpg` in requirements:** Correct async PostgreSQL driver for SQLAlchemy 2.0 async.

- **`pydantic-settings` in requirements:** Listed and correctly used in `app/config.py`.
