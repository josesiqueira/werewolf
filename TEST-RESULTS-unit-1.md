# Test Results — Unit Group 1 (UT-001 to UT-029)
## Summary: 29 passed, 0 failed
## Results
| ID | Name | Status | Notes |
|----|------|--------|-------|
| UT-001 | Linear phase progression from INIT to NIGHT | PASS | |
| UT-002 | NIGHT → DAY_BID resets debate_turn_count | PASS | |
| UT-003 | DAY_SPEECH increments debate counter and loops back to DAY_BID | PASS | |
| UT-004 | VOTE advances round counter and returns to NIGHT | PASS | |
| UT-005 | Max rounds cap sets status to "discarded" | PASS | |
| UT-006 | Win condition detected before phase transition halts game immediately | PASS | |
| UT-007 | eliminate_player removes player from alive list and clears mayor | PASS | |
| UT-008 | eliminate_player is idempotent — duplicate call does nothing | PASS | |
| UT-009 | get_state_for_agent — werewolf sees teammates, not role of others | PASS | |
| UT-010 | get_state_for_agent — seer sees investigation history | PASS | |
| UT-011 | check_win_condition — wolves win at parity | PASS | |
| UT-012 | check_win_condition — villagers win when all wolves eliminated | PASS | |
| UT-013 | check_win_condition — game continues when wolves are minority | PASS | |
| UT-014 | assign_roles produces exactly the fixed distribution for 7 players | PASS | |
| UT-015 | assign_roles raises ValueError for wrong player count | PASS | Tested both 6 and 8 players |
| UT-016 | get_private_info — werewolf receives teammate list | PASS | |
| UT-017 | get_private_info — non-werewolf roles receive only their own role | PASS | Tested seer, doctor, villager |
| UT-018 | Wolf kill succeeds when doctor protects a different player | PASS | |
| UT-019 | Doctor save blocks wolf kill when targets match | PASS | |
| UT-020 | Seer investigation returns correct role regardless of kill outcome | PASS | |
| UT-021 | No wolf target produces no kill and kill_successful == False | PASS | |
| UT-022 | Seer investigates a villager — result role is "villager" | PASS | |
| UT-023 | Plurality winner with no tie | PASS | |
| UT-024 | Two-way tie resolved by random selection, was_tiebreak == True | PASS | |
| UT-025 | Candidate with zero votes still appears in vote_counts | PASS | |
| UT-026 | run_mayor_election raises ValueError for empty candidates | PASS | |
| UT-027 | handle_mayor_succession — valid successor choice is honoured | PASS | |
| UT-028 | handle_mayor_succession — invalid successor falls back to random | PASS | |
| UT-029 | handle_mayor_succession raises ValueError with no alive players | PASS | |
