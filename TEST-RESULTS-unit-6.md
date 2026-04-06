# TEST-RESULTS-unit-6 — Phase 3 Game Runner

**Date:** 2026-04-03
**Module:** `backend/app/runner/` (assignment, progress, quality)
**Runner:** pytest 8.3.4, Python 3.12.3

## Summary

| Result | Count |
|--------|-------|
| Passed | 11    |
| Failed | 0     |
| Errors | 0     |
| Total  | 11    |

**Duration:** 0.08s

## Test Details

### test_assignment.py — Profile Assignment Balance

| ID     | Test                              | Result |
|--------|-----------------------------------|--------|
| UT-121 | Balance over 210 games (+/-2)     | PASS   |
| UT-122 | Correct role distribution (2W/1S/1D/3V) | PASS   |
| UT-123 | No duplicate personas per game    | PASS   |
| UT-124 | All 7 profiles appear per game    | PASS   |
| UT-125 | Small batch (7 games) valid       | PASS   |

### test_progress.py — Progress Tracking

| ID     | Test                              | Result |
|--------|-----------------------------------|--------|
| UT-126 | 5/10 games -> 50% pct, ETA=150s  | PASS   |
| UT-127 | games_per_minute calculation      | PASS   |
| UT-128 | Initial status shows 0 completed  | PASS   |

### test_quality.py — Quality Tracking

| ID     | Test                              | Result |
|--------|-----------------------------------|--------|
| UT-129 | Degraded count increments         | PASS   |
| UT-130 | Win tracking (villagers/werewolves) | PASS   |
| UT-131 | Profile tracking per game         | PASS   |

## Raw Output

```
tests/test_assignment.py::test_ut121_balance_over_210_games PASSED       [  9%]
tests/test_assignment.py::test_ut122_correct_role_distribution PASSED    [ 18%]
tests/test_assignment.py::test_ut123_no_duplicate_personas PASSED        [ 27%]
tests/test_assignment.py::test_ut124_all_profiles_appear PASSED          [ 36%]
tests/test_assignment.py::test_ut125_small_batch_valid PASSED            [ 45%]
tests/test_progress.py::test_ut126_completion_pct_and_eta PASSED         [ 54%]
tests/test_progress.py::test_ut127_games_per_minute PASSED               [ 63%]
tests/test_progress.py::test_ut128_initial_status PASSED                 [ 72%]
tests/test_quality.py::test_ut129_degraded_count PASSED                  [ 81%]
tests/test_quality.py::test_ut130_win_tracking PASSED                    [ 90%]
tests/test_quality.py::test_ut131_profile_tracking PASSED                [100%]

============================== 11 passed in 0.08s ==============================
```
