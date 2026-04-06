# Test Results — Unit Group 3 (UT-066 to UT-070)

## Summary: 5 passed, 0 failed

## Results

| ID | Name | Status | Notes |
|----|------|--------|-------|
| UT-066 | `AgentResponse` schema rejects `bid_level` outside 0-4 | PASSED | Verified bid_level=5 and bid_level=-1 both raise ValidationError; boundaries 0 and 4 accepted |
| UT-067 | `AgentResponse` schema rejects invalid `deception_self_label` | PASSED | "lying" raises ValidationError; all 5 valid DeceptionLabel enum values accepted |
| UT-068 | `AgentResponse` schema rejects `confidence` outside 1-5 | PASSED | confidence=0 and confidence=6 both raise ValidationError; boundaries 1 and 5 accepted |
| UT-069 | `GameCreate` accepts None config gracefully | PASSED | Empty dict, explicit None, and dict config all parse correctly |
| UT-070 | `PlayerResponse` serialises `is_mayor` and `survived` as booleans | PASSED | ORM-style objects correctly produce bool types (not int) via from_attributes=True |
