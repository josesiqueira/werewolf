# Phase 2 Agent System — Correctness Audit

**Date**: 2026-04-03
**Auditor**: Tester Agent
**Scope**: All 17 acceptance criteria from PLAN.md Phase 2
**Files examined**: llm_client.py, retry.py, personas.py, techniques.py, memory.py, output_parser.py, llm_agent.py, prompts/system_message.py, prompts/user_message.py, engine/game_loop.py

---

## Executive Summary

Phase 2 has **3 critical runtime failures** that prevent `LLMAgent` from functioning at all (ImportError and TypeErrors on instantiation), plus **6 additional correctness defects** in retry count, system message size, bid defaults, context-window enforcement, degradation tracking, and memory summarization quality. The isolated components (output_parser, personas, techniques, memory) are largely correct. The integration wiring in `llm_agent.py` is broken.

---

## Criterion-by-Criterion Verdicts

### AC-1: System message is ~750 tokens with all required sections

**STATUS: PARTIAL FAIL**

All 5 required sections are present and correctly assembled in `system_message.py`:
- Game rules (~195 char-tokens)
- Role assignment + private info (~43 char-tokens for villager; ~60 for werewolf with teammate list)
- Persona description (~150-160 char-tokens)
- JSON output format instructions (~130 char-tokens)
- Behavioral instructions (~68 char-tokens)

**Defect**: The assembled message totals approximately **530–600 tokens** (char/4 method) or **460–470 tokens** (word/0.75 method), not the specified ~750. The shortfall is concentrated in the persona section: each persona is 80–96 words (~108–128 tokens), roughly half the specified "~200 tokens each". The personas are quality text covering speaking style, reasoning tendencies, and social behavior, but they are shorter than the spec calls for.

The `build_system_message` function signature is correct and the caching logic in `get_or_build_system_message` works properly.

---

### AC-2: User message contains technique doc (or absent for baseline), game state, history, instruction

**STATUS: PASS**

`user_message.py::build_user_message` correctly structures four sections:
1. Technique document — included only when `technique_text is not None`; `None` is returned by `load_technique("baseline")` so baseline agents receive no technique section. ✓
2. Game state formatted text — always present via `_format_game_state`. ✓
3. Memory context + debate history — included when non-empty. ✓
4. Turn instruction — looked up from `_TURN_INSTRUCTIONS` dict covering all 8 phases. ✓

---

### AC-3: All 6 technique files load correctly from `persuasion-techniques/`

**STATUS: PASS**

`techniques.py` defines the correct `PROFILE_FILE_MAP` with all 6 filenames:
- `ethos` → `TECHNIQUE-ETHOS.md`
- `pathos` → `TECHNIQUE-PATHOS.md`
- `logos` → `TECHNIQUE-LOGOS.md`
- `authority_socialproof` → `TECHNIQUE-AUTHORITY-SOCIALPROOF.md`
- `reciprocity_liking` → `TECHNIQUE-RECIPROCITY-LIKING.md`
- `scarcity_commitment` → `TECHNIQUE-SCARCITY-COMMITMENT.md`

Path resolution: `Path(__file__).resolve().parents[3]` from `backend/app/agent/techniques.py` correctly resolves to the project root, and `persuasion-techniques/` exists there with all 6 files confirmed present. The in-memory cache, lazy loading, `preload_all()`, and section extraction (via `## ` regex) all look correct.

---

### AC-4: Baseline agents receive no technique document in their prompt

**STATUS: PASS**

`load_technique("baseline")` explicitly returns `None`. `build_user_message` only prepends the technique block when `technique_text` is truthy. `LLMAgent._ensure_initialized` only loads technique text when `persuasion_profile != "baseline"`. The chain is clean.

---

### AC-5: 7 distinct personas assigned per game with no duplicates

**STATUS: PASS**

`personas.py` defines exactly 7 personas: `analytical`, `aggressive`, `quiet`, `warm`, `suspicious`, `diplomatic`, `blunt`. `assign_personas` uses `random.sample(PERSONA_NAMES, k=len(player_ids))` which guarantees no duplicates and raises `ValueError` if more than 7 players are requested. All 7 persona texts cover speaking style, reasoning tendencies, and social behavior patterns.

**Minor note**: Personas are ~115–128 tokens each, below the "~200 tokens each" spec target. See AC-1.

---

### AC-6: JSON output parsed correctly for well-formed responses

**STATUS: PASS**

`output_parser.py::_try_parse_json` attempts `json.loads(raw_text)` first. For well-formed JSON this succeeds immediately. All fields are then extracted and individually validated. Tested manually and logic is correct.

---

### AC-7: Malformed JSON repaired: markdown fences stripped, trailing commas fixed

**STATUS: PASS**

- `_strip_markdown_fences`: handles `` ```json `` and `` ``` `` variants with a `re.DOTALL` regex; also handles the edge case where `` ``` `` is present but not wrapping (fallback branch). Tested: works correctly.
- `_fix_trailing_commas`: `re.sub(r",\s*([}\]])", r"\1", text)` correctly removes trailing commas before `}` and `]`. Tested: works correctly.
- `_fix_missing_key_quotes`: `re.sub(r'(?<=\{|,)\s*(\w+)\s*:', r' "\1":', text)` uses lookbehind for `{` or `,`; Python's `re` module accepts this because both alternatives are fixed-width. Tested: works correctly.
- Fallback: `re.search(r"\{.*\}", repaired, re.DOTALL)` extracts the first JSON object from surrounding text. Tested: works correctly.

---

### AC-8: Invalid vote target (dead player) auto-corrected to random alive player

**STATUS: PASS**

In `parse_agent_response`:
```python
if vote_target not in alive_players or vote_target == self_id:
    valid_targets = [p for p in alive_players if p != self_id]
    if valid_targets:
        vote_target = random.choice(valid_targets)
```
This correctly handles dead players, self-votes, and None targets. The game_loop also has a second layer of validation at the vote collection point.

---

### AC-9: Bid outside 0-4 clamped to valid range

**STATUS: PASS (in output_parser) — PARTIAL in llm_agent**

`parse_agent_response` clamps bid correctly: `max(0, min(4, int(bid_level)))`.

**Defect**: When `bid_level` is missing from the LLM's JSON response, `data.get("bid_level")` returns `None` and the `if bid_level is not None` block is skipped — leaving `bid_level=None` in the returned `AgentResponse`. The spec requires that missing fields use conservative defaults (bid=1). See AC-10.

---

### AC-10: Missing response fields filled with conservative defaults

**STATUS: PARTIAL FAIL**

| Field | Behavior when absent | Status |
|---|---|---|
| `private_reasoning` | Defaults to `""` via `str(data.get(..., ""))` | OK |
| `public_statement` | Defaults to `""` via `str(data.get(..., ""))` | OK |
| `vote_target` | Stays `None` (optional field) | OK |
| `bid_level` | **Stays `None` — no default applied** | **FAIL** |
| `technique_self_label` | Stays `None` (acceptable) | OK |
| `deception_self_label` | Defaults to `"truthful"` via explicit `else` | OK |
| `confidence` | Defaults to `3` via explicit `else` | OK |

**Defect**: `bid_level` has no `else` branch. When the field is absent from the JSON, `AgentResponse.bid_level` is `None` instead of the conservative default of `1`.

The `_get_conservative_defaults` helper used on total JSON parse failure does correctly set all fields including `bid_level=1`.

---

### AC-11: Retry fires 3 times with backoff (1s, 3s, 9s)

**STATUS: FAIL**

`retry.py` uses:
```python
retry_llm_call = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=9, exp_base=3),
    ...
)
```

`stop_after_attempt(3)` means **3 total attempts** (1 initial + 2 retries). The resulting wait sequence is:
- After attempt 1 fails → wait 1s (3^0 * 1)
- After attempt 2 fails → wait 3s (3^1 * 1)
- Attempt 3 runs → if fails, raise (no 9s wait, no third retry)

**The spec requires "3 retries with exponential backoff (1s, 3s, 9s)"**, which implies **4 total attempts** (1 initial + 3 retries). To produce all three backoff waits (1s, 3s, 9s), the implementation needs `stop_after_attempt(4)`.

**Fix**: Change `stop_after_attempt(3)` to `stop_after_attempt(4)`.

---

### AC-12: After 3 failures, conservative defaults used and turn marked is_default_response=True

**STATUS: CRITICAL FAIL — LLMAgent cannot be imported**

`llm_agent.py` contains three fatal import/call-signature errors that prevent any `LLMAgent` instance from being created:

**Error 1 — ImportError on module load:**
```python
from app.agent.retry import call_with_retry, get_conservative_defaults
```
`retry.py` exports `call_with_retry_and_fallback` and `build_default_response`. Neither `call_with_retry` nor `get_conservative_defaults` exist. This causes `ImportError` when `llm_agent` is imported.

**Error 2 — TypeError: LLMClient instantiation:**
```python
self._llm_client = LLMClient(
    api_key=self.config.get("openai_api_key", ""),
    model=self.config.get("openai_model", "gpt-4o"),
    timeout=self.config.get("llm_timeout", 60),
)
```
`LLMClient.__init__` accepts `(model, timeout, temperature)` — not `api_key`. Passing `api_key=` raises `TypeError: __init__() got an unexpected keyword argument 'api_key'`.

**Error 3 — TypeError: build_system_message call:**
```python
self._system_message = build_system_message(
    role=self.role,
    private_info=private_info,
    persona=self._persona_description,
)
```
`build_system_message` requires `(role, player_id, persona_description, teammates=None)`. The call passes `private_info=` (not a valid parameter) and `persona=` (should be `persona_description=`), and omits the required `player_id` argument. This raises `TypeError`.

**Error 4 — Wrong function call signature for retry:**
```python
llm_response = await call_with_retry(
    self._llm_client.complete,
    self._system_message,
    user_message,
)
```
The actual function `call_with_retry_and_fallback` expects a **zero-argument callable** as first arg, plus `alive_players` and `player_id`. The call passes the bound method `self._llm_client.complete` plus two strings — wrong on both function name and signature.

**Secondary issue**: Even after errors above are fixed, the `is_default_response` flag is never propagated from `LLMAgent.last_turn_metadata` to `_record_turn` in `game_loop.py`. The game_loop never passes `is_default_response=True` to `_record_turn`, so the degradation count query always returns 0. See AC-16.

---

### AC-13: API timeout set to 60s

**STATUS: PASS**

`LLMClient.__init__` has `timeout: float = 60.0` as the default and passes it to `AsyncOpenAI(timeout=self._timeout)`. The spec requirement is satisfied.

---

### AC-14: Memory: last 2-3 rounds full transcript, earlier rounds summarized

**STATUS: PASS (with minor quality note)**

`MemoryManager` sets `FULL_TRANSCRIPT_ROUNDS = 3`, which is within the "2-3" spec range. `get_context` correctly applies the cutoff: rounds before `num_rounds - 3` get summaries, the last 3 rounds get full transcripts. Partial transcript fitting within budget is also handled.

**Minor quality note**: When older rounds are summarized on-the-fly (no pre-stored summary), the `vote_result` is hardcoded to `"(see game state)"` rather than the actual vote result. The actual result is only available when `store_round_summary` was called explicitly by the game loop. Since `game_loop.py` does not call `store_round_summary`, all summaries in practice will use the placeholder `"(see game state)"` for the vote result field. The game loop should call `update_round_history` or `store_round_summary` on the LLMAgent at the end of each round to populate real data.

---

### AC-15: Total context stays under 80% of model window

**STATUS: PARTIAL FAIL**

The spec requires dynamic enforcement: total context (system message + user message + memory) must stay under 80% of the model's context window.

**What is implemented**: `MemoryManager` enforces a flat `max_tokens=2000` budget for the memory portion only. There is no calculation of 80% of any model's context window size. No model window size constant is defined anywhere in the codebase.

**What is NOT implemented**: There is no function that computes `model_window * 0.80`, no per-model window size table, and no total-context budget enforcer that combines system message + user message + memory tokens against that threshold.

**Practical impact**: With GPT-4o's 128k context window, 80% = ~102,400 tokens. The current total prompt (system ~600 tokens + technique doc ~800-1200 tokens + game state ~400 tokens + memory 2000 tokens max) is well under that limit in practice. The criterion is satisfied by coincidence, not by enforcement.

---

### AC-16: Werewolf leak detection catches night-phase references in public_statement

**STATUS: PASS (with one false-positive risk)**

`check_werewolf_leaks` in `output_parser.py` defines 19 regex patterns covering the most common ways a werewolf might accidentally reveal night-phase information. Testing confirmed:

**Correctly caught**: "I targeted Player 3 last night", "My wolf partner and I decided", "We chose to kill the doctor", "I'm a werewolf", "My teammate is safe", "As a werewolf, I know who is who", "We killed Player 5".

**Correctly ignored**: "I suspect Player 3 is a werewolf", "The wolves probably targeted the seer", "There might be a wolf among us".

**False positive risk**: `\bmy\s+partner\b` is overly broad — a villager or seer saying "My partner in analysis is Player 2" would not trigger this (since the check only applies when `self.role == "werewolf"`), so the false-positive risk only affects wolves, where it is acceptable to err on the side of caution.

The function replaces the leaked statement with a random choice from 5 generic alternatives and logs a warning. This is correct behavior per the spec.

---

### AC-17: Game flagged as degraded when >30% turns use defaults

**STATUS: FAIL — degradation tracking is non-functional**

`game_loop.py` contains the degradation logic (Task 11 comment at line 740), which queries the database for `Turn.is_default_response == True` records after flushing. The threshold check (`default_rate > 0.30`) and `game.is_degraded = True` assignment are present.

**Defect**: The `_record_turn` helper has `is_default_response: bool = False` as its default, and **no call site in `game_loop.py` ever passes `is_default_response=True`**. The `LLMAgent` tracks `self.last_turn_metadata.is_default_response` internally, but `game_loop.py` never reads this attribute before calling `_record_turn`. As a result, the DB query at the end of the game always returns `default_count = 0`, and `game.is_degraded` is never set to `True`.

**Fix required**: After each `await agent.speak(...)` / `await agent.vote(...)` call, read `agent.last_turn_metadata.is_default_response` and pass it to `_record_turn`.

---

## Summary Table

| # | Criterion | Status | Severity |
|---|---|---|---|
| 1 | System message ~750 tokens, all sections present | PARTIAL FAIL | Low |
| 2 | User message structure correct | PASS | — |
| 3 | All 6 technique files load | PASS | — |
| 4 | Baseline gets no technique doc | PASS | — |
| 5 | 7 distinct personas, no duplicates | PASS | — |
| 6 | JSON parsing for well-formed responses | PASS | — |
| 7 | Malformed JSON repair (fences, commas) | PASS | — |
| 8 | Invalid vote target auto-corrected | PASS | — |
| 9 | Bid clamped to 0-4 | PASS | — |
| 10 | Missing fields filled with defaults | PARTIAL FAIL | Medium |
| 11 | Retry fires 3 times with 1s/3s/9s backoff | FAIL | Medium |
| 12 | Conservative defaults after 3 failures; LLMAgent wiring | CRITICAL FAIL | Critical |
| 13 | API timeout 60s | PASS | — |
| 14 | Memory: recent full, earlier summarized | PASS | — |
| 15 | Context under 80% of model window | PARTIAL FAIL | Low |
| 16 | Werewolf leak detection | PASS | — |
| 17 | Game degraded when >30% defaults | FAIL | High |

---

## Defect Catalogue

### DEFECT-1 (Critical): ImportError — `llm_agent.py` imports non-existent names from `retry.py`

**File**: `backend/app/agent/llm_agent.py`, line 27  
**Code**: `from app.agent.retry import call_with_retry, get_conservative_defaults`  
**Reality**: `retry.py` exports `call_with_retry_and_fallback` and `build_default_response`  
**Impact**: `LLMAgent` cannot be imported; the entire agent system is non-functional at runtime  
**Fix**: Change import to `from app.agent.retry import call_with_retry_and_fallback, build_default_response` and update all call sites

### DEFECT-2 (Critical): TypeError — `LLMClient` instantiated with wrong keyword argument

**File**: `backend/app/agent/llm_agent.py`, lines 77–81  
**Code**: `LLMClient(api_key=..., model=..., timeout=...)`  
**Reality**: `LLMClient.__init__` accepts `(model, timeout, temperature)` — no `api_key` parameter; API key is read from `settings.OPENAI_API_KEY` internally  
**Impact**: `TypeError` on `LLMAgent.__init__`; all agent instantiation fails  
**Fix**: Remove `api_key=` argument; optionally add `temperature=` if needed

### DEFECT-3 (Critical): TypeError — `build_system_message` called with wrong kwargs

**File**: `backend/app/agent/llm_agent.py`, lines 129–133  
**Code**: `build_system_message(role=self.role, private_info=private_info, persona=self._persona_description)`  
**Reality**: Signature is `build_system_message(role, player_id, persona_description, teammates=None)`. Missing required `player_id`; `private_info` is not a valid kwarg; `persona` should be `persona_description`  
**Impact**: `TypeError` on first call to `_ensure_initialized`; system message never built  
**Fix**: `build_system_message(role=self.role, player_id=self.player_id, persona_description=self._persona_description, teammates=teammates)`

### DEFECT-4 (Critical): Wrong retry function call signature

**File**: `backend/app/agent/llm_agent.py`, lines 178–183  
**Code**: `await call_with_retry(self._llm_client.complete, self._system_message, user_message)`  
**Reality**: `call_with_retry_and_fallback` takes `(llm_coroutine: Callable[[], Awaitable], alive_players, player_id)` — the coroutine must be a **zero-argument** callable  
**Impact**: Wrong function name (ImportError, blocked by DEFECT-1) and wrong call signature  
**Fix**: `await call_with_retry_and_fallback(lambda: self._llm_client.complete(self._system_message, user_message), alive_players, self.player_id)`

### DEFECT-5 (High): Degradation tracking never sets `is_default_response=True`

**File**: `backend/app/engine/game_loop.py`  
**Problem**: `LLMAgent.last_turn_metadata.is_default_response` is tracked but never read by game_loop before calling `_record_turn`. All turns are recorded with `is_default_response=False`. The DB query at game end always returns `default_count=0`. `game.is_degraded` is never set to `True`.  
**Fix**: After each agent action, check `isinstance(agent, LLMAgent)` and pass `agent.last_turn_metadata.is_default_response` to `_record_turn`

### DEFECT-6 (Medium): Retry count is 2, not 3

**File**: `backend/app/agent/retry.py`, line 70  
**Code**: `stop=stop_after_attempt(3)` — this means 3 total attempts (1 initial + 2 retries)  
**Spec**: "3 retries with exponential backoff (1s, 3s, 9s)" — implies 4 total attempts  
**Result**: The 9s backoff wait never occurs; only two retries with waits of 1s and 3s  
**Fix**: Change to `stop_after_attempt(4)`

### DEFECT-7 (Medium): `bid_level` not defaulted when missing from JSON

**File**: `backend/app/agent/output_parser.py`, lines 230–237  
**Problem**: When `bid_level` is absent from the LLM JSON, `data.get("bid_level")` returns `None`, the `if bid_level is not None` block is skipped, and `bid_level=None` flows into `AgentResponse`. Spec requires default of 1.  
**Fix**: Add `else: bid_level = 1` after the `if bid_level is not None` block

### DEFECT-8 (Low): System message is ~530–600 tokens, not ~750

**File**: `backend/app/agent/prompts/system_message.py` and `personas.py`  
**Problem**: Personas are ~115–128 tokens each (80–96 words), approximately half the "~200 tokens each" specification. The total system message is ~530–600 tokens vs the ~750 token target.  
**Note**: The spec uses "~" so some tolerance is expected, but the shortfall is ~25–30%.  
**Fix**: Expand each persona to cover additional behavioral details (e.g., specific verbal tics, reaction to accusations, alliance-forming tendencies)

### DEFECT-9 (Low): Context window 80% enforcement is not dynamic

**File**: `backend/app/agent/memory.py`  
**Problem**: `MemoryManager` uses a flat `max_tokens=2000` limit rather than computing 80% of the actual model context window. No model window size is defined anywhere.  
**Practical impact**: Low — current prompts are far under any reasonable limit  
**Fix**: Define `MODEL_CONTEXT_WINDOWS = {"gpt-4o": 128000}` and compute `max_tokens = int(MODEL_CONTEXT_WINDOWS[model] * 0.80)` in LLMAgent initialization

### DEFECT-10 (Low): Round summaries use placeholder vote results

**File**: `backend/app/agent/memory.py`, lines 149–154  
**Problem**: When `get_context` generates on-the-fly summaries for older rounds (no pre-stored summary), it passes `vote_result="(see game state)"` as a placeholder. The game_loop never calls `agent.update_round_history()` so no real vote results are stored.  
**Fix**: Game loop should call `llm_agent.update_round_history(round_statements, vote_result, eliminated)` at end of each round; or game_loop should pass vote results when requesting context

---

## Files with No Issues

- `backend/app/agent/llm_client.py` — correct async wrapper, timeout, token tracking
- `backend/app/agent/personas.py` — correct 7 personas, sample without replacement
- `backend/app/agent/techniques.py` — correct path resolution, all 6 files map correctly, cache works
- `backend/app/agent/output_parser.py` — correct repair logic (fences, commas, brace extraction), correct validation and auto-correction; only minor bid_level default gap (DEFECT-7)
- `backend/app/agent/prompts/user_message.py` — correct structure for all phases
- `backend/app/engine/game_loop.py` (degradation query logic) — the SQL query is correct; the bug is in the upstream data (DEFECT-5)
