"""Unit tests for vote tallying and win conditions (UT-036 to UT-042)."""

from app.engine.vote import VoteResult, check_win_condition, tally_votes
from tests.conftest import P


# UT-036: Clear plurality eliminates single target
class TestUT036:
    def test_clear_plurality(self):
        votes = {P[0]: P[1], P[2]: P[1], P[3]: P[1], P[4]: P[1], P[5]: P[2]}
        result = tally_votes(votes)
        assert result.eliminated_player == P[1]
        assert result.was_tiebreak is False
        assert result.vote_counts[P[1]] == 4


# UT-037: Two-way tie broken by mayor's vote
class TestUT037:
    def test_mayor_breaks_tie(self):
        # Two-way tie: P[0] gets 2 votes (P[2], P[5]), P[1] gets 2 votes (P[3], P[4]).
        # Mayor P[5] voted for P[0], so P[0] is eliminated via tiebreak.
        votes = {P[2]: P[0], P[5]: P[0], P[3]: P[1], P[4]: P[1]}
        result = tally_votes(votes, mayor_id=P[5])
        assert result.eliminated_player == P[0]
        assert result.was_tiebreak is True


# UT-038: Two-way tie where mayor voted for neither -- no elimination
class TestUT038:
    def test_mayor_voted_for_neither(self):
        votes = {P[2]: P[0], P[3]: P[0], P[4]: P[1], P[5]: P[1], P[6]: P[2]}
        result = tally_votes(votes, mayor_id=P[6])
        assert result.eliminated_player is None
        assert result.was_tiebreak is False


# UT-039: Three-way split results in no elimination
class TestUT039:
    def test_three_way_split(self):
        votes = {
            P[0]: P[4], P[1]: P[4],
            P[2]: P[5], P[3]: P[5],
            P[5]: P[6], P[6]: P[6],
        }
        result = tally_votes(votes, mayor_id=None)
        assert result.eliminated_player is None
        assert result.was_tiebreak is False


# UT-040: Empty vote dict returns no elimination without error
class TestUT040:
    def test_empty_votes(self):
        result = tally_votes({}, mayor_id=None)
        assert result.eliminated_player is None
        assert result.vote_counts == {}


# UT-041: check_win_condition -- wolf parity wins
class TestUT041:
    def test_wolf_parity(self):
        alive = [
            {"role": "werewolf"}, {"role": "werewolf"},
            {"role": "villager"}, {"role": "villager"},
        ]
        assert check_win_condition(alive) == "werewolves"


# UT-042: check_win_condition -- all wolves dead
class TestUT042:
    def test_all_wolves_dead(self):
        alive = [
            {"role": "seer"}, {"role": "doctor"}, {"role": "villager"},
        ]
        assert check_win_condition(alive) == "villagers"
