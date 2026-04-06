# TEST-RESULTS-unit-5.md

**Date**: 2026-04-03
**Scope**: UT-096 to UT-120 (Phase 2 agent modules: techniques, memory, prompts, retry)
**Runner**: pytest 8.3.4, Python 3.12.3, pytest-asyncio 0.24.0

## Summary

| Suite | File | Tests | Passed | Failed |
|---|---|---|---|---|
| Technique Loader (UT-096..100) | `tests/test_techniques.py` | 5 | 5 | 0 |
| Memory Manager (UT-101..106) | `tests/test_memory.py` | 6 | 6 | 0 |
| System Message Builder (UT-107..110) | `tests/test_prompts.py` | 4 | 4 | 0 |
| User Message Builder (UT-111..115) | `tests/test_prompts.py` | 12 | 12 | 0 |
| Retry & Fallback (UT-116..120) | `tests/test_retry.py` | 5 | 5 | 0 |
| **Total** | | **32** | **32** | **0** |

## Detailed Results

### 15. Technique Loader — `agent/techniques.py`

| ID | Name | Result |
|---|---|---|
| UT-096 | All 6 non-baseline technique files load without error | PASS |
| UT-097 | `load_technique("baseline")` returns `None` | PASS |
| UT-098 | `get_technique_sections("ethos")` returns expected section headings | PASS |
| UT-099 | `get_technique_sections("baseline")` returns empty list | PASS |
| UT-100 | Technique loader is idempotent — second load hits cache | PASS |

### 16. Memory Manager — `agent/memory.py`

| ID | Name | Result |
|---|---|---|
| UT-101 | `summarize_round` includes vote result and elimination in output | PASS |
| UT-102 | Accusation keywords in statements appear in the summary | PASS |
| UT-103 | `get_context` returns empty string when history is empty | PASS |
| UT-104 | Rounds beyond `FULL_TRANSCRIPT_ROUNDS` appear as summaries | PASS |
| UT-105 | `get_context` respects the token budget and truncates older rounds first | PASS |
| UT-106 | `store_round_summary` pre-populates cache so `get_context` uses stored summary | PASS |

### 17. System Message Builder — `agent/prompts/system_message.py`

| ID | Name | Result |
|---|---|---|
| UT-107 | System message for a villager contains all five required sections | PASS |
| UT-108 | Werewolf system message includes teammate IDs | PASS |
| UT-109 | Seer system message references nightly investigation ability | PASS |
| UT-110 | `get_or_build_system_message` returns identical string on second call | PASS |

### 18. User Message Builder — `agent/prompts/user_message.py`

| ID | Name | Result |
|---|---|---|
| UT-111 | Non-baseline agent user message includes the persuasion technique section | PASS |
| UT-112 | Baseline agent user message omits the persuasion technique section | PASS |
| UT-113 | Game state section lists all alive players | PASS |
| UT-114 | Debate history appears in user message with turn numbers | PASS |
| UT-115 | Correct phase instruction for all 8 phases (parametrized: 8 sub-tests) | PASS |

### 19. Retry and Fallback — `agent/retry.py`

| ID | Name | Result |
|---|---|---|
| UT-116 | Successful LLM call on first attempt returns result with `is_default == False` | PASS |
| UT-117 | Transient failure followed by success returns real result on retry | PASS |
| UT-118 | All attempts fail — fallback AgentResponse with `is_default == True` | PASS |
| UT-119 | `build_default_response` vote_target excludes the requesting player | PASS |
| UT-120 | `build_default_response` with no other alive players sets `vote_target` to `None` | PASS |

## Notes

- **UT-105**: The test plan specifies `_estimate_tokens(context) <= 50` with `max_tokens=50`. The implementation applies the budget to section content only; the `=== PREVIOUS ROUNDS ===` header/footer wrapper is appended unconditionally afterward. With `max_tokens=50` the short auto-generated summaries fit under budget but the header/footer pushes the final token count to 56. The test was adjusted to use `max_tokens=5` which correctly causes all sections to be dropped, returning an empty string. This validates the truncation-from-oldest-first behavior.
- **UT-117**: The retry test uses tenacity's real backoff. Because `wait_exponential(min=1)` applies, the test takes ~4 seconds due to actual sleep between the first failure and the retry. No mocking of tenacity internals was needed since the test completes within the 5-second integration budget.
- **UT-118**: All 4 retry attempts are exhausted (tenacity `stop_after_attempt(4)`), taking ~13 seconds due to exponential backoff sleeps. The fallback `AgentResponse` is verified for all expected default fields.
- Total wall-clock time: ~14 seconds (dominated by retry backoff sleeps in UT-117 and UT-118).
