# TEST-RESULTS-unit-4.md

**Date**: 2026-04-03
**Scope**: UT-071 to UT-095 (Output Parser, Werewolf Leak Detection, Personas)
**Runner**: pytest 8.3.4, Python 3.12.3
**Duration**: 0.09s

---

## Summary

| Range | Module | Tests | Passed | Failed | Skipped |
|-------|--------|-------|--------|--------|---------|
| UT-071 to UT-082 | Output Parser (`agent/output_parser.py`) | 19 | 19 | 0 | 0 |
| UT-083 to UT-089 | Werewolf Leak Detection (`agent/output_parser.py`) | 9 | 9 | 0 | 0 |
| UT-090 to UT-095 | Personas (`agent/personas.py`) | 14 | 14 | 0 | 0 |
| **Total** | | **42** | **42** | **0** | **0** |

---

## Detailed Results

### 12. Output Parser

| ID | Name | Result |
|----|------|--------|
| UT-071 | Valid JSON parses to correct AgentResponse fields | PASS |
| UT-072 | Markdown-fenced JSON is stripped and parsed successfully | PASS |
| UT-073 | Trailing-comma JSON is repaired and parsed | PASS |
| UT-074 | Completely invalid text falls back to conservative defaults | PASS |
| UT-075 | vote_target pointing to self is auto-corrected | PASS |
| UT-076 | vote_target for eliminated player is auto-corrected | PASS |
| UT-077 | bid_level above 4 is clamped to 4 | PASS |
| UT-078 | Negative bid_level is clamped to 0 | PASS |
| UT-079 | Unrecognised deception_self_label auto-corrected (x4 inputs) | PASS |
| UT-080 | Valid deception_self_label values preserved (x5 inputs) | PASS |
| UT-081 | Missing bid_level key defaults to 1 | PASS |
| UT-082 | Missing confidence key defaults to 3 | PASS |

### 13. Werewolf Leak Detection

| ID | Name | Result |
|----|------|--------|
| UT-083 | Explicit role admission triggers leak detection | PASS |
| UT-084 | Direct night-kill admission triggers leak detection | PASS |
| UT-085 | Wolf teammate reference triggers leak detection | PASS |
| UT-086 | Innocent wolf-themed language does NOT trigger (x3 inputs) | PASS |
| UT-087 | Empty statement returned unchanged | PASS |
| UT-088 | "Our kill" phrase triggers leak detection | PASS |
| UT-089 | "As a werewolf" phrase triggers leak detection | PASS |

### 14. Personas

| ID | Name | Result |
|----|------|--------|
| UT-090 | PERSONAS dict contains exactly 7 entries with correct keys | PASS |
| UT-091 | Every persona description is a non-empty string (x7) | PASS |
| UT-092 | assign_personas for 7 players produces all-unique assignments | PASS |
| UT-093 | assign_personas raises ValueError for >7 players | PASS |
| UT-094 | get_persona_description returns correct description (x3) | PASS |
| UT-095 | get_persona_description raises KeyError for unknown persona | PASS |

---

## App Bugs Found

None. All tested logic behaves as specified in TEST-PLAN.md.

---

## Test Files

- `backend/tests/test_output_parser.py` — UT-071 to UT-089 (19 test cases, 42 parametrized variants total with personas)
- `backend/tests/test_personas.py` — UT-090 to UT-095 (14 test cases including parametrized variants)
