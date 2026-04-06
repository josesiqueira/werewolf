# Phase 2 Integration Audit
**Date:** 2026-04-03
**Scope:** Agent system integration — verifying all components wire together correctly and connect to Phase 1 engine code.

---

## Summary

The agent system has **4 blocking bugs** that will cause immediate runtime errors when LLMAgent is used, plus **3 design gaps** that silently degrade functionality. MockAgent works correctly and the game_loop's core structure is sound.

---

## Check 1 — LLMAgent extends AgentInterface: all abstract methods with matching signatures

**Result: PASS**

`LLMAgent` in `backend/app/agent/llm_agent.py` extends `AgentInterface` and implements all 6 abstract methods with exactly matching signatures:

| Method | AgentInterface signature | LLMAgent signature |
|--------|-------------------------|-------------------|
| `campaign` | `(self, game_state: dict)` → `AgentResponse` | matches |
| `vote_for_mayor` | `(self, game_state: dict, candidates: list[str])` → `str` | matches |
| `night_action` | `(self, game_state: dict, role: str)` → `str` | matches |
| `bid` | `(self, game_state: dict, debate_history: list[str])` → `int` | matches |
| `speak` | `(self, game_state: dict, debate_history: list[str])` → `AgentResponse` | matches |
| `vote` | `(self, game_state: dict, debate_history: list[str])` → `AgentResponse` | matches |

All methods return the correct types and are `async`.

---

## Check 2 — LLMAgent produces AgentResponse compatible with game_loop expectations

**Result: PASS**

`game_loop.py` expects `AgentResponse` with fields: `private_reasoning`, `public_statement`, `vote_target`, `bid_level`, `technique_self_label`, `deception_self_label`, `confidence`. `_record_turn()` reads all of these. `LLMAgent._call_llm()` returns the dataclass `AgentResponse` from `agent_interface.py`, which has all those fields. The field mapping is correct.

---

## Check 3 — Technique loader paths resolve correctly

**Result: PASS**

`backend/app/agent/techniques.py` computes:
```python
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # app/agent/techniques.py -> 3 levels up
_TECHNIQUES_DIR = _PROJECT_ROOT / "persuasion-techniques"
```
`parents[3]` of `.../backend/app/agent/techniques.py` resolves to `/home/jose/Documents/Werewolf Projects/Werewolf 2`, which is the correct project root. The `persuasion-techniques/` directory exists there with all 6 expected files:
- `TECHNIQUE-ETHOS.md`, `TECHNIQUE-PATHOS.md`, `TECHNIQUE-LOGOS.md`
- `TECHNIQUE-AUTHORITY-SOCIALPROOF.md`, `TECHNIQUE-RECIPROCITY-LIKING.md`, `TECHNIQUE-SCARCITY-COMMITMENT.md`

All 6 entries in `PROFILE_FILE_MAP` map to files that exist. **Path resolution is correct.**

---

## Check 4 — System message builder receives correct arguments from LLMAgent

**Result: BUG — BLOCKING**

`LLMAgent._ensure_initialized()` calls `build_system_message` with the wrong keyword arguments:

```python
# llm_agent.py line 129-133 (ACTUAL CALL):
self._system_message = build_system_message(
    role=self.role,
    private_info=private_info,   # WRONG: parameter does not exist
    persona=self._persona_description,  # WRONG: parameter is named persona_description
)
```

```python
# system_message.py line 85-88 (ACTUAL SIGNATURE):
def build_system_message(
    role: str,
    player_id: str,            # MISSING from call
    persona_description: str,  # called as "persona"
    teammates: list[str] | None = None,
) -> str:
```

**Two problems:**
1. `player_id` is a required positional argument — it is not passed at all. This will raise `TypeError`.
2. `persona` is not a valid parameter name; it should be `persona_description`.
3. `private_info` is not a valid parameter name; there is no such parameter. The system message builder does not accept a `private_info` dict.

Additionally, `LLMAgent` never passes `player_id` to the system message builder, so the role section (`"You are Player {player_id}..."`) will not be populated correctly even if the call were fixed.

**Impact:** Every first call to any LLMAgent method triggers `_ensure_initialized()`, which will immediately raise `TypeError: build_system_message() got an unexpected keyword argument 'private_info'`. LLMAgent is completely non-functional.

---

## Check 5 — User message builder receives correct game state format from game_loop

**Result: PASS with minor gap**

`game_loop._build_agent_state()` produces a dict with keys: `alive_players`, `eliminated_players`, `mayor`, `current_round`, `current_phase`, `private_info`. The `build_user_message()` function reads `alive_players`, `eliminated_players`, `current_round`, `current_phase`, and `private_info` — all present. It also checks `mayor_id` and falls back to `mayor`, matching the game_loop's key name (`"mayor"`).

**Minor gap:** `build_user_message` checks for `night_results` and `voting_history` keys for optional display, but `game_loop` never populates these keys in the state dict. These sections will silently be omitted. This is not a bug but reduces agent information quality.

---

## Check 6 — Output parser returns the correct AgentResponse (no name collision)

**Result: PASS — no active collision, but latent risk**

`output_parser.py` imports from `app.engine.agent_interface`:
```python
from app.engine.agent_interface import AgentResponse
```
It constructs and returns `AgentResponse` from `agent_interface.py` (a plain dataclass).

`schemas/agent.py` also defines an `AgentResponse` (a Pydantic `BaseModel`). The two differ significantly:
- Dataclass `AgentResponse`: plain Python, `bid_level: int | None`, `vote_target: str | None`
- Pydantic `AgentResponse`: validates, `bid_level: int` (no None), `vote_target: uuid.UUID | None`

`schemas/__init__.py` exports `AgentResponse` by name. **No file currently imports both at the top level**, so there is no active collision. However, any future code that does `from app.schemas import AgentResponse` and also `from app.engine.agent_interface import AgentResponse` in the same file will shadow one with the other silently. The types are incompatible. This is a naming risk that should be resolved (e.g. rename the Pydantic one to `AgentResponseSchema`).

---

## Check 7 — Retry module correctly wraps the LLM client call

**Result: BUG — BLOCKING (two errors)**

`llm_agent.py` line 27 imports names that do not exist in `retry.py`:

```python
# llm_agent.py (ACTUAL IMPORT):
from app.agent.retry import call_with_retry, get_conservative_defaults
```

```python
# retry.py (ACTUAL EXPORTS):
build_default_response          # exported (not get_conservative_defaults)
call_with_retry_and_fallback    # exported (not call_with_retry)
retry_llm_call                  # exported
```

**Error 1:** `call_with_retry` does not exist — the function is named `call_with_retry_and_fallback`. This causes an `ImportError` at module load time.

**Error 2:** `get_conservative_defaults` does not exist — the function is named `build_default_response`. Same `ImportError`.

Furthermore, even if the names were corrected, the **call signature** in `llm_agent.py` is wrong:

```python
# llm_agent.py line 178 (ACTUAL CALL — intended for call_with_retry):
llm_response = await call_with_retry(
    self._llm_client.complete,
    self._system_message,
    user_message,
)
```

```python
# retry.py (ACTUAL SIGNATURE of call_with_retry_and_fallback):
async def call_with_retry_and_fallback(
    llm_coroutine: Callable[[], Awaitable[Any]],  # zero-arg callable
    alive_players: list[str],
    player_id: str,
) -> tuple[Any, bool]:
```

The retry function expects a **zero-argument lambda wrapping the coroutine**, plus `alive_players` and `player_id`. `llm_agent.py` passes the bound method and its arguments directly — the API is incompatible on both the wrapping pattern and the parameter list.

**Impact:** Importing `llm_agent.py` raises `ImportError`. LLMAgent cannot be instantiated.

---

## Check 8 — LLMClient constructor: api_key parameter mismatch

**Result: BUG — BLOCKING**

`LLMAgent.__init__` constructs `LLMClient` with an `api_key` keyword argument:

```python
# llm_agent.py lines 77-81:
self._llm_client = LLMClient(
    api_key=self.config.get("openai_api_key", ""),
    model=self.config.get("openai_model", "gpt-4o"),
    timeout=self.config.get("llm_timeout", 60),
)
```

`LLMClient.__init__` does not accept `api_key`:

```python
# llm_client.py lines 39-44:
def __init__(
    self,
    model: str | None = None,
    timeout: float = 60.0,
    temperature: float = 0.7,
) -> None:
```

`LLMClient` reads `api_key` directly from `settings.OPENAI_API_KEY` (line 49). Passing `api_key` as a constructor argument raises `TypeError: __init__() got an unexpected keyword argument 'api_key'`.

**Config key naming note:** `LLMAgent` reads `config.get("openai_api_key")` (lowercase), while `config.py` exposes `settings.OPENAI_API_KEY` (uppercase). These are two separate config paths — `LLMAgent` uses a dict config passed at construction time, while `LLMClient` reads from the pydantic `Settings`. The two are not connected. If `LLMAgent.config` is not populated with the right key, `LLMClient` still works because it reads from `settings` directly. But passing `api_key` to `LLMClient()` will always crash.

---

## Check 8b — "default" persona raises KeyError

**Result: BUG — BLOCKING**

`LLMAgent.__init__` defaults `persona` to `"default"`:
```python
persona: str = "default",
```

`_ensure_initialized()` calls:
```python
self._persona_description = get_persona_description(self.persona)
```

`get_persona_description("default")` raises `KeyError` because `"default"` is not in `PERSONAS`. The 7 valid persona keys are: `analytical`, `aggressive`, `quiet`, `warm`, `suspicious`, `diplomatic`, `blunt`.

**Impact:** Any LLMAgent created without an explicit valid persona (the common default case, as used in `api/games.py` if LLMAgent were ever wired in) raises `KeyError` on first method call.

---

## Check 9 — Memory manager integrates with game_loop's debate_history

**Result: DESIGN GAP — memory is never populated by game_loop**

`LLMAgent` has a `update_round_history(round_statements, vote_result, eliminated)` method that feeds the `MemoryManager`. The `MemoryManager.get_context()` is called inside `_call_llm()` when `_round_history` is non-empty.

However, `game_loop.py` **never calls `update_round_history()`** on any agent after a round completes. The `_round_history` list on every LLMAgent remains empty for the entire game. The memory subsystem will always produce an empty context, and agents will have no cross-round memory.

The integration hook exists in `LLMAgent` but the orchestration side in `game_loop.py` is missing. The `debate_history` list (intra-round speeches) is passed to agents correctly per-turn — that is working. But inter-round memory is dead.

---

## Check 10 — Game degradation tracking: Turn model query

**Result: PASS**

`game_loop.py` lines 747-751:
```python
default_count_result = await db_session.execute(
    sa_select(sa_func.count())
    .select_from(Turn)
    .where(Turn.game_id == game.id, Turn.is_default_response.is_(True))
)
```

`Turn.is_default_response` is defined as `Mapped[bool]` with a `Boolean` column (line 42-44 of `models/turn.py`). SQLAlchemy's `InstrumentedAttribute` on a `Mapped[bool]` column correctly supports `.is_(True)`. The `select_from(Turn)` with `.where()` chaining is valid SQLAlchemy 2.x async syntax. The 30% threshold logic is correct.

---

## Check 11 — Import chain: circular imports between agent/ and engine/

**Result: PASS — no circular imports**

Import direction:
- `agent/` modules import from `engine/agent_interface.py` only (for `AgentResponse`, `AgentInterface`)
- `engine/` modules do NOT import from `agent/` modules
- `api/games.py` imports from both `engine/` and `agent/` but does not create a cycle

The import graph is: `api` → `engine` + `agent`, `agent` → `engine.agent_interface`. No cycles exist.

---

## Check 12 — All __init__.py files exist and export correctly

**Result: PASS with notes**

All required `__init__.py` files are present:
- `backend/app/__init__.py` — empty (fine)
- `backend/app/agent/__init__.py` — has docstring only, no exports (acceptable; modules imported by full path)
- `backend/app/agent/prompts/__init__.py` — has docstring only
- `backend/app/engine/__init__.py` — empty
- `backend/app/models/__init__.py` — exports all 6 model classes correctly
- `backend/app/schemas/__init__.py` — exports all schema classes including `AgentResponse`
- `backend/app/api/__init__.py` — empty

No missing `__init__.py` files. The `models/__init__.py` and `schemas/__init__.py` exports are correct and complete.

---

## Check 13 — Config settings used by LLMAgent match config.py

**Result: PARTIAL MISMATCH**

| Setting | config.py field | LLMClient reads | LLMAgent dict key |
|---------|----------------|-----------------|-------------------|
| API key | `OPENAI_API_KEY` | `settings.OPENAI_API_KEY` directly | `config.get("openai_api_key")` — unused (crash before use) |
| Model name | `OPENAI_MODEL` (default `"gpt-4o"`) | `settings.OPENAI_MODEL` directly | `config.get("openai_model", "gpt-4o")` |
| Timeout | not in config.py | N/A | `config.get("llm_timeout", 60)` |

`LLMClient` reads `api_key` and `model` from `settings` directly, **ignoring** any per-agent config dict. This means changing the model per-agent via config dict has no effect (once the crash bug is fixed), because `LLMClient` ignores the `model` kwarg — wait, actually it does: `LLMClient.__init__` accepts `model` and uses `model or settings.OPENAI_MODEL`. So model can be overridden via kwarg. But `api_key` cannot — it is hardwired to `settings`.

The `OPENAI_MODEL` default in both `config.py` and `LLMAgent`'s fallback is `"gpt-4o"`. These are consistent.

---

## Bug Severity Table

| # | File | Bug | Severity |
|---|------|-----|----------|
| B1 | `agent/llm_agent.py:27` | Imports `call_with_retry` and `get_conservative_defaults` — neither exists in `retry.py` (correct names: `call_with_retry_and_fallback`, `build_default_response`) | **BLOCKING — ImportError** |
| B2 | `agent/llm_agent.py:77-81` | Passes `api_key=` to `LLMClient()` — not an accepted parameter | **BLOCKING — TypeError** |
| B3 | `agent/llm_agent.py:129-133` | Calls `build_system_message(private_info=..., persona=...)` — wrong kwargs; correct params are `player_id` and `persona_description`; `player_id` entirely missing | **BLOCKING — TypeError** |
| B4 | `agent/llm_agent.py:67` | Default `persona="default"` — `get_persona_description("default")` raises `KeyError`; valid values are the 7 named personas | **BLOCKING — KeyError** |
| B5 | `agent/llm_agent.py:178` | `call_with_retry(self._llm_client.complete, system_msg, user_msg)` — wrong argument pattern; `call_with_retry_and_fallback` expects a zero-arg callable plus `alive_players` and `player_id` | **BLOCKING — once B1 fixed** |
| D1 | `engine/game_loop.py` | Never calls `agent.update_round_history()` after round completion — inter-round memory always empty | **Design gap — silent** |
| D2 | `engine/game_loop.py` | `_build_game_state()` does not include `night_results` or `voting_history` keys — those `build_user_message()` sections are always empty | **Design gap — silent** |
| R1 | `schemas/agent.py` + `engine/agent_interface.py` | Both define `AgentResponse` — different types (Pydantic vs dataclass) — risk of name collision in future code | **Latent risk** |

---

## What Works Correctly

- `MockAgent` is fully functional and the game loop runs correctly end-to-end with mock agents
- `AgentInterface` ABC definition is correct; all abstract methods are properly declared
- `game_loop.py` calls the correct agent methods with correct argument types
- Technique file path resolution is correct
- `build_user_message()` produces correct structured text from game state
- Output parser (`parse_agent_response`) correctly returns the dataclass `AgentResponse` from `agent_interface.py`
- Retry decorator (`retry_llm_call` / `call_with_retry_and_fallback`) logic is correct internally
- Memory manager (`MemoryManager`) internal logic is correct
- Turn model query for degradation tracking is valid SQLAlchemy 2.x
- No circular imports between `agent/` and `engine/` packages
- All `__init__.py` files present; `models/__init__.py` and `schemas/__init__.py` export correctly
- `OPENAI_MODEL` default (`"gpt-4o"`) is consistent between `config.py` and `LLMAgent`
- `schemas/agent.py` `AgentResponse` (Pydantic) is not currently used by any game-loop code path
- `revote` phase correctly calls `agent.vote()` and uses `user_message.py`'s fallback `vote` instruction

---

## Recommended Fixes (in priority order)

1. **Fix import names in `llm_agent.py`:** Change `call_with_retry` → `call_with_retry_and_fallback`, `get_conservative_defaults` → `build_default_response`.

2. **Fix `call_with_retry_and_fallback` call site:** Wrap the client call as a zero-arg lambda: `lambda: self._llm_client.complete(self._system_message, user_message)`, and pass `alive_players` and `self.player_id`.

3. **Fix `LLMClient()` constructor call:** Remove the `api_key=` kwarg (LLMClient reads from settings directly). If per-agent API keys are needed, add `api_key` as a parameter to `LLMClient.__init__`.

4. **Fix `build_system_message()` call:** Add `player_id=self.player_id`, rename `persona=` → `persona_description=`, remove the invalid `private_info=` kwarg. Werewolf teammate info should be sourced separately and passed via `teammates=`.

5. **Fix default persona:** Change `persona: str = "default"` to `persona: str = "analytical"` or another valid value, or add a `"default"` entry to `PERSONAS` as an alias.

6. **Wire memory updates in game_loop:** After each round's vote phase, call `agent.update_round_history(debate_history, vote_result_str, eliminated_description)` for each LLMAgent.
