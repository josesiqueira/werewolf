# Test Results — Unit Group 2 (UT-030 to UT-052)
## Summary: 23 passed, 0 failed
## Results
| ID | Name | Status | Notes |
|----|------|--------|-------|
| UT-030 | Highest unique bidder wins outright | PASSED | |
| UT-031 | Mention priority breaks bid tie | PASSED | |
| UT-032 | All-zero bids falls through to random selection | PASSED | |
| UT-033 | extract_mentions finds player names case-insensitively | PASSED | |
| UT-034 | extract_mentions does not partial-match substrings | PASSED | |
| UT-035 | select_speaker raises ValueError for empty bids | PASSED | |
| UT-036 | Clear plurality eliminates single target | PASSED | |
| UT-037 | Two-way tie broken by mayor's vote | PASSED | Test plan input inconsistency: described as 2-way tie but provided votes give 3-1 split. Test adjusted to produce actual 2-way tie (2-2) so mayor tiebreak activates. |
| UT-038 | Two-way tie where mayor voted for neither — no elimination | PASSED | |
| UT-039 | Three-way split results in no elimination | PASSED | |
| UT-040 | Empty vote dict returns no elimination without error | PASSED | |
| UT-041 | check_win_condition — wolf parity wins | PASSED | |
| UT-042 | check_win_condition — all wolves dead | PASSED | |
| UT-043 | MockAgent campaign always returns non-empty public_statement | PASSED | |
| UT-044 | MockAgent.vote_for_mayor never returns agent's own ID | PASSED | |
| UT-045 | MockAgent.bid always returns value in [0, 4] | PASSED | |
| UT-046 | MockAgent.vote sets valid vote_target | PASSED | |
| UT-047 | export_game_ndjson produces one JSON per turn, no trailing newline | PASSED | |
| UT-048 | Each NDJSON record contains all 22 required fields | PASSED | |
| UT-049 | Turns ordered by round_number then created_at | PASSED | |
| UT-050 | export_game_ndjson returns empty string for no turns | PASSED | |
| UT-051 | export_batch_ndjson concatenates multiple games | PASSED | |
| UT-052 | export_batch_ndjson with empty game_ids returns empty string | PASSED | |
