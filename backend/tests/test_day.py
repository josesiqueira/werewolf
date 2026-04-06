"""Unit tests for day-phase bidding and speech selection (UT-030 to UT-035)."""

import random

import pytest

from app.engine.day import extract_mentions, select_speaker
from tests.conftest import P


# UT-030: Highest unique bidder wins outright
class TestUT030:
    def test_highest_unique_bidder_wins(self):
        bids = {P[0]: 4, P[1]: 2, P[2]: 1, P[3]: 0}
        result = select_speaker(bids, previous_mentions=[])
        assert result == P[0]


# UT-031: Mention priority breaks bid tie
class TestUT031:
    def test_mention_priority_breaks_tie(self):
        bids = {P[0]: 3, P[1]: 3, P[2]: 1}
        result = select_speaker(bids, previous_mentions=[P[1], P[0]])
        assert result == P[1]


# UT-032: All-zero bids falls through to random selection
class TestUT032:
    def test_all_zero_bids_random(self):
        random.seed(42)
        bids = {P[0]: 0, P[1]: 0, P[2]: 0}
        result = select_speaker(bids, previous_mentions=[])
        assert result in [P[0], P[1], P[2]]


# UT-033: extract_mentions finds player names case-insensitively
class TestUT033:
    def test_case_insensitive_mentions(self):
        result = extract_mentions(
            "ALICE thinks BOB is suspicious.",
            ["Alice", "Bob", "Carol"],
        )
        assert result == ["Alice", "Bob"]


# UT-034: extract_mentions does not partial-match substrings
class TestUT034:
    def test_no_partial_match(self):
        result = extract_mentions(
            "I think we should also consider.",
            ["Al"],
        )
        assert result == []


# UT-035: select_speaker raises ValueError for empty bids
class TestUT035:
    def test_empty_bids_raises(self):
        with pytest.raises(ValueError):
            select_speaker({}, previous_mentions=[])
