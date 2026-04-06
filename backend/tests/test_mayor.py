"""Tests UT-023 to UT-029 — Mayor Election."""

import random

import pytest

from app.engine.mayor import run_mayor_election, handle_mayor_succession
from tests.conftest import P


# UT-023: Plurality winner with no tie
class TestUT023:
    def test_plurality_winner(self):
        result = run_mayor_election(
            candidates=[P[0], P[2], P[4]],
            votes={P[0]: P[2], P[4]: P[2], P[3]: P[0]},
        )
        assert result.winner == P[2]
        assert result.was_tiebreak is False
        assert result.vote_counts == {P[0]: 1, P[2]: 2, P[4]: 0}


# UT-024: Two-way tie resolved by random selection
class TestUT024:
    def test_two_way_tie(self):
        result = run_mayor_election(
            candidates=[P[0], P[2]],
            votes={P[0]: P[2], P[1]: P[2], P[3]: P[0], P[4]: P[0]},
        )
        assert result.winner in [P[0], P[2]]
        assert result.was_tiebreak is True


# UT-025: Candidate with zero votes still appears in vote_counts
class TestUT025:
    def test_zero_vote_candidate_in_counts(self):
        result = run_mayor_election(
            candidates=[P[0], P[2], P[4]],
            votes={P[3]: P[0], P[5]: P[0]},
        )
        assert result.vote_counts[P[4]] == 0
        assert result.winner == P[0]


# UT-026: run_mayor_election raises ValueError for empty candidates
class TestUT026:
    def test_empty_candidates_raises(self):
        with pytest.raises(ValueError):
            run_mayor_election(candidates=[], votes={})


# UT-027: handle_mayor_succession — valid successor choice is honoured
class TestUT027:
    def test_valid_successor(self):
        result = handle_mayor_succession(
            dead_mayor=P[0],
            alive_players=[P[2], P[3], P[4]],
            successor_choice=P[3],
        )
        assert result == P[3]


# UT-028: handle_mayor_succession — invalid successor falls back to random
class TestUT028:
    def test_invalid_successor_fallback(self):
        result = handle_mayor_succession(
            dead_mayor=P[0],
            alive_players=[P[2], P[3]],
            successor_choice=P[6],  # not in alive list
        )
        assert result in [P[2], P[3]]


# UT-029: handle_mayor_succession raises ValueError with no alive players
class TestUT029:
    def test_no_alive_players_raises(self):
        with pytest.raises(ValueError):
            handle_mayor_succession(
                dead_mayor=P[0],
                alive_players=[],
                successor_choice=None,
            )
