# Phase 2 Edge Case Audit — Werewolf AI Agent System

**Auditor:** Claude (automated static + dynamic analysis)
**Date:** 2026-04-03
**Scope:** `/backend/app/agent/` — all Phase 2 files
**Method:** Source reading + live Python execution for each edge case

---

## CRITICAL BUGS (will crash at runtime)

These are import-time or construction-time failures that prevent `LLMAgent` from being instantiated at all.

---

### BUG-1: Import names do not exist in `retry.py`

**File:** `llm_agent.py` line 27
**Severity:** CRITICAL — `ImportError` at module load time

```
from app.agent.retry import call_with_retry, get_conservative_defaults
```

`retry.py` exports:
- `call_with_retry_and_fallback` (not `call_with_retry`)
- `build_default_response` (not `get_conservative_defaults`)

Neither name matches. The entire `LLMAgent` class is un-importable.

---

### BUG-2: `LLMClient` constructor called with wrong keyword arguments

**File:** `llm_agent.py` lines 77–81
**Severity:** CRITICAL — `TypeError` at `LLMAgent.__init__`

```python
# llm_agent.py (caller)
self._llm_client = LLMClient(
    api_key=self.config.get("openai_api_key", ""),
    model=self.config.get("openai_model", "gpt-4o"),
    timeout=self.config.get("llm_timeout", 60),
)

# llm_client.py (actual signature)
def __init__(self, model=None, timeout=60.0, temperature=0.7) -> None:
```

`api_key` is not a parameter of `LLMClient`. The `LLMClient` reads its API key from `settings.OPENAI_API_KEY` internally, not from the caller. Passing `api_key=` causes a `TypeError`.

---

### BUG-3: `build_system_message` called with wrong keyword arguments

**File:** `llm_agent.py` lines 129–133
**Severity:** CRITICAL — `TypeError` at first LLM call

```python
# llm_agent.py (caller)
self._system_message = build_system_message(
    role=self.role,
    private_info=private_info,
    persona=self._persona_description,
)

# system_message.py (actual signature)
def build_system_message(role, player_id, persona_description, teammates=None) -> str:
```

`private_info` and `persona` are not valid parameters. `player_id` and `persona_description` are missing. This raises `TypeError` the first time any agent tries to produce an LLM response.

---

### BUG-4: `call_with_retry` called with wrong argument count and shape

**File:** `llm_agent.py` lines 178–180
**Severity:** CRITICAL (secondary to BUG-1, same code path)

Even if BUG-1 were fixed by renaming the import, the call site is wrong:

```python
# llm_agent.py (caller)
llm_response = await call_with_retry(
    self._llm_client.complete,
    self._system_message,
    user_message,
)

# retry.py (actual signature)
async def call_with_retry_and_fallback(
    llm_coroutine: Callable[[], Awaitable[Any]],
    alive_players: list[str],
    player_id: str,
) -> tuple[Any, bool]:
```

The caller passes `(fn, str, str)` but the function expects `(zero-arg-callable, list[str], str)`. The design intent is different: `llm_agent.py` expects `call_with_retry` to wrap a bound call, while `retry.py` expects a pre-bound zero-arg coroutine plus game state for the fallback.

---

## EDGE CASE FINDINGS (per audit checklist)

---

### 1. LLM returns empty string

**File:** `output_parser.py` → `_try_parse_json` → `parse_agent_response`
**Behavior:** HANDLED CORRECTLY

`json.loads("")` raises `JSONDecodeError`. All repair strategies also fail. `_try_parse_json` returns `None`. `parse_agent_response` falls through to `_get_conservative_defaults`, which returns a safe `AgentResponse` with generic statement and random vote target.

```
Result: AgentResponse(
    private_reasoning='[parse failure — using defaults]',
    public_statement='I need more time to think about this.',
    vote_target='p2',   # random valid target
    bid_level=1, confidence=3, deception_self_label='truthful'
)
```

No crash. Graceful degradation confirmed by live test.

---

### 2. LLM returns non-JSON text (natural language)

**File:** `output_parser.py`
**Behavior:** HANDLED CORRECTLY

Same path as empty string. The brace-extraction fallback (`re.search(r"\{.*\}", ...)`) finds no `{` in plain text, so `_try_parse_json` returns `None` and conservative defaults are used. Verified live with `"I think Player 2 is the werewolf because they were suspicious."`.

---

### 3. JSON has extra fields not in schema

**File:** `output_parser.py` → `parse_agent_response`
**Behavior:** HANDLED CORRECTLY (by design)

The parser uses `data.get("field_name")` for each expected field. Unknown keys in the parsed dict are simply never accessed. Extra fields are silently discarded with no error or warning. This is safe but note that no strict schema validation is applied — unknown fields produce no audit log entry.

---

### 4. Technique file doesn't exist on disk

**File:** `techniques.py` → `_ensure_loaded`
**Behavior:** GRACEFUL DEGRADATION — but the agent gets no technique content silently

```python
if not filepath.exists():
    logger.error("Technique file not found: %s", filepath)
    return  # returns without setting _cache[profile]
```

Consequence chain:
- `load_technique(profile)` returns `None` (via `_cache.get(profile)` with no entry set)
- `get_technique_sections(profile)` returns `[]`
- In `llm_agent.py`, `_technique_text = None` → no technique section in the user message
- `_technique_sections = []` → all `technique_self_label` values become `"none"`

The error is logged at `ERROR` level but execution continues silently. The agent behaves as a baseline agent without informing the caller. No exception is raised.

**Risk:** A missing file due to deployment error (wrong directory, case-sensitive filesystem) would cause the agent to silently lose its persuasion profile, producing subtly wrong experimental results with no crash to alert the operator.

---

### 5. Persona count less than 7 (not enough for all players)

**File:** `personas.py` → `assign_personas`
**Behavior:** DEPENDS ON DIRECTION

The guard is:
```python
if len(player_ids) > len(PERSONAS):
    raise ValueError(...)
```

- **Fewer than 7 players (e.g., 5):** `assign_personas` works correctly — `random.sample(PERSONA_NAMES, k=5)` draws 5 of 7 personas. Verified live.
- **More than 7 players (e.g., 8):** Raises `ValueError` with a clear message. Correct.
- **Exactly 7 players:** Normal case.

The docstring says "must be <= 7" which correctly documents the constraint. There is no issue here, but note the `ValueError` is not caught anywhere in `llm_agent.py` or the broader agent setup code visible in this audit, so it would propagate to the game engine.

---

### 6. `alive_players` is empty when building defaults

**File:** `output_parser.py` → `_get_conservative_defaults`; `retry.py` → `build_default_response`
**Behavior:** HANDLED — `vote_target` becomes `None`

```python
valid_targets = [p for p in alive_players if p != self_id]
vote_target = random.choice(valid_targets) if valid_targets else None
```

Both `_get_conservative_defaults` and `build_default_response` use this same pattern. When `alive_players=[]`, `valid_targets=[]`, and `random.choice` is guarded by the conditional — `vote_target` is set to `None`. No crash. Verified live.

In `llm_agent.py`'s `_call_llm`, the fallback path calls:
```python
get_conservative_defaults(alive_players=game_state.get("alive_players", []))
```
This also passes `player_id` in some variants, so the filter `p != self_id` works correctly. If the game state provides an empty list, `vote_target=None` propagates cleanly.

---

### 7. Leak detection with partial matches — "we chose" in "we chose to wait"

**File:** `output_parser.py` → `check_werewolf_leaks`
**Behavior:** FALSE POSITIVE — confirmed by live test

The pattern `r"\bwe\s+chose\b"` matches the substring `"we chose"` in any larger phrase. All of the following innocent phrases are flagged and replaced:

| Statement | Flagged? | Verdict |
|-----------|----------|---------|
| `"we chose to wait"` | YES | False positive |
| `"yesterday we chose to relax"` | YES | False positive |
| `"we chose our target"` | YES | True positive |

More broadly, several patterns are overly broad:

| Pattern | Innocent phrase that triggers it |
|---------|----------------------------------|
| `\bi\s+killed\b` | "I killed it at that presentation" |
| `\bmy\s+partner\b` | "my partner and I disagree on this vote" |
| `\bour\s+kill\b` | "our kill rate in this game was high" |
| `\bwe\s+killed\b` | "we killed that topic last round" |
| `\bmy\s+teammate\b` | "my teammate from the last game" |

**Impact:** Werewolf agents producing legitimate public statements containing these common English collocations will have their speech silently replaced with generic text. This degrades gameplay quality and could suppress valid strategic communication from werewolf agents.

The replacement is also non-deterministic (`random.choice(_GENERIC_REPLACEMENTS)`) with no logging of which specific replacement was chosen — only the original leaked statement is logged.

---

### 8. Memory manager with 0 rounds of history

**File:** `memory.py` → `get_context`
**Behavior:** HANDLED CORRECTLY

```python
if not full_history:
    return ""
```

`get_context(current_round=1, full_history=[])` returns empty string immediately. No crash. Verified live.

One edge case within this: if `full_history=[[]]` (one round with zero statements), the code still runs correctly — it produces a valid `[Round 1 - full transcript]` section header with no speaker lines below it, then wraps with the `=== PREVIOUS ROUNDS ===` / `=== END PREVIOUS ROUNDS ===` delimiters. Not a bug, but the output is slightly wasteful (non-empty string with no substantive content).

---

### 9. Token counting edge cases — very long messages

**File:** `memory.py` → `_estimate_tokens`
**Behavior:** PARTIAL — memory is bounded, but user message is not

`_estimate_tokens` uses `len(text.split()) / 0.75`. This is safe for any string length including empty strings (returns 0).

The `MemoryManager.get_context` correctly enforces a budget and truncates older summaries and recent transcripts to fit. When a single statement exceeds the entire budget:
- The full-transcript section fails the budget check
- A partial transcript is attempted, but since the first line also exceeds the budget, `partial_lines` stays at length 1 (header only)
- The `if len(partial_lines) > 1` guard rejects it
- `sections` remains empty, `get_context` returns `""`

This is correct behavior. However, **the user message itself has no total token cap.** The `build_user_message` function assembles:
- Technique text: 800–1200 tokens (unbounded, read directly from file)
- Game state: ~300–500 tokens
- Memory context: capped at `max_tokens` (default 2000)
- Debate history: **no length limit** — all turns concatenated
- Turn instruction: ~50 tokens

If `debate_history` is long (10 turns × long speeches), the total user message could exceed the model's context window. When this happens, the OpenAI API returns a `context_length_exceeded` error. This propagates as an exception through the retry logic, exhausts all 3 retries, and falls back to defaults.

The fallback is safe, but the root cause (debate history overflow) is never trimmed, so every retry of the same turn will fail identically — wasting 12 seconds of backoff time before producing a default response.

---

### 10. OpenAI API returns unexpected status codes

**File:** `llm_client.py` → `complete`; `retry.py` → `call_with_retry_and_fallback`
**Behavior:** GENERIC CATCH-ALL — works but non-discriminating

The OpenAI Python SDK raises typed exceptions for HTTP errors:
- `openai.RateLimitError` (429) — retriable
- `openai.APIConnectionError` — retriable
- `openai.InternalServerError` (500) — retriable
- `openai.AuthenticationError` (401) — NOT retriable (wrong key)
- `openai.BadRequestError` (400) — NOT retriable (invalid request, e.g. context overflow)

The retry decorator in `retry.py` is:
```python
retry_llm_call = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=9, exp_base=3),
    before_sleep=_log_retry,
    reraise=True,
)
```

There is no `retry=` predicate to filter which exceptions are retriable. A 401 `AuthenticationError` will be retried 3 times (wasting 12 seconds) before being re-raised. A 400 `BadRequestError` from context overflow will similarly retry 3 times with identical inputs, failing identically each time.

`llm_client.py` also has an unguarded index access:
```python
choice = response.choices[0]  # line 85
```
If OpenAI returns a response with an empty `choices` list (e.g., content moderation blocked all output), this raises `IndexError`. This is not caught inside `complete()` and will propagate as a non-HTTP exception through the retry path.

---

### 11. System message + user message exceeds model context

**File:** `llm_agent.py`, `prompts/user_message.py`
**Behavior:** UNHANDLED at construction — handled only via fallback after all retries fail

See item 9 above for the full analysis. No pre-call token budget is checked. The system message (~750 tokens) plus user message (1600–3700+ tokens) can theoretically stay within GPT-4o's 128k context window under normal game conditions, but there is no enforcement. Under adversarial or malformed input (very long debate history), overflow is possible.

---

### 12. Retry with immediate success on first try

**File:** `retry.py` → `call_with_retry_and_fallback`
**Behavior:** HANDLED CORRECTLY

`before_sleep` is only invoked between attempts (i.e., only when a retry is about to happen). If the first attempt succeeds, `before_sleep` is never called, no backoff occurs, and the result is returned immediately as `(result, False)`. This is correct tenacity behavior, confirmed by code review.

---

## SUMMARY TABLE

| # | Edge Case | Status | Severity |
|---|-----------|--------|----------|
| BUG-1 | Import names mismatch (`call_with_retry`, `get_conservative_defaults`) | BROKEN | CRITICAL |
| BUG-2 | `LLMClient` called with `api_key=` (not a parameter) | BROKEN | CRITICAL |
| BUG-3 | `build_system_message` called with `private_info=`, `persona=` (wrong params) | BROKEN | CRITICAL |
| BUG-4 | `call_with_retry` called with 3 positional args (expects zero-arg callable + game state) | BROKEN | CRITICAL |
| 1 | LLM returns empty string | Handled — safe defaults | OK |
| 2 | LLM returns non-JSON natural language | Handled — safe defaults | OK |
| 3 | JSON has extra fields not in schema | Handled — silently ignored | OK |
| 4 | Technique file missing on disk | Graceful degradation, logged at ERROR but silent to caller | WARN |
| 5 | Persona count < 7 players | OK (samples k=n from 7) — ValueError only if n > 7 | OK |
| 6 | `alive_players` empty in defaults | Handled — `vote_target=None` | OK |
| 7 | `"we chose"` matches `"we chose to wait"` (false positive) | FALSE POSITIVE — innocent speech suppressed | WARN |
| 7+ | `\bi killed\b`, `\bmy partner\b`, `\bour kill\b` etc. — overly broad patterns | FALSE POSITIVES — see table above | WARN |
| 8 | Memory manager with 0 rounds | Handled — returns `""` | OK |
| 9 | Very long messages / token overflow | Memory capped; debate history uncapped; context overflow causes 3-retry waste | WARN |
| 10 | OpenAI API unexpected status codes | Non-retriable errors (401, 400) are retried anyway; `choices[0]` unguarded | WARN |
| 11 | System + user message exceeds model context | No pre-check; same failure path as #10 | WARN |
| 12 | Immediate success on first retry attempt | Handled — no backoff, returns immediately | OK |

---

## RECOMMENDED FIXES (priority order)

1. **Fix BUG-1–4** — `llm_agent.py` is incoherent with the modules it imports. Either align `retry.py` / `llm_client.py` / `system_message.py` to the calling convention in `llm_agent.py`, or rewrite the call sites. The agent system cannot run at all until these are resolved.

2. **Add retriable-exception filter to retry decorator** — use `retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError))` to avoid burning retries on permanent errors.

3. **Guard `response.choices[0]`** in `llm_client.py` — check `len(response.choices) > 0` and treat empty choices as a retriable error.

4. **Refine leak detection patterns** — add context-sensitive suffixes or use negative lookahead to avoid flagging innocent phrases. For example, `r"\bwe\s+chose\b(?!\s+to\b)"` would exempt "we chose to ...". Alternatively, require night-phase context keywords adjacent to the match.

5. **Cap debate history length** in `build_user_message` — truncate `debate_history` to the last N turns (e.g., last 5) before formatting, or estimate tokens and trim.

6. **Raise or propagate technique-load failure** — when a technique file is missing, either raise at startup (fast-fail) or expose a flag on the agent so the experiment runner knows the profile was not applied.
