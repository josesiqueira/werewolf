"""Vote phase and elimination for Werewolf AI Agents.

Pure logic — no database calls, no LLM calls.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass
class VoteResult:
    """Outcome of a vote phase."""
    eliminated_player: str | None
    vote_counts: dict[str, int]
    was_tiebreak: bool


def tally_votes(
    votes: dict[str, str],
    mayor_id: str | None = None,
) -> VoteResult:
    """Tally votes and determine elimination.

    Rules:
        - Simple majority (plurality) eliminates a player.
        - If there is a two-way tie and the mayor voted for one of the
          tied candidates, the mayor breaks the tie.
        - If there is a 3+ way split (or a tie the mayor cannot break),
          no one is eliminated.

    Args:
        votes: Mapping of voter_id -> target_id they voted to eliminate.
        mayor_id: The current mayor's player ID (or None).

    Returns:
        VoteResult describing the outcome.
    """
    if not votes:
        return VoteResult(
            eliminated_player=None,
            vote_counts={},
            was_tiebreak=False,
        )

    counts = Counter(votes.values())
    max_votes = max(counts.values())
    top_targets = [target for target, c in counts.items() if c == max_votes]

    # Clear winner
    if len(top_targets) == 1:
        return VoteResult(
            eliminated_player=top_targets[0],
            vote_counts=dict(counts),
            was_tiebreak=False,
        )

    # Two-way tie — mayor tiebreak
    if len(top_targets) == 2 and mayor_id is not None:
        mayor_vote = votes.get(mayor_id)
        if mayor_vote in top_targets:
            return VoteResult(
                eliminated_player=mayor_vote,
                vote_counts=dict(counts),
                was_tiebreak=True,
            )

    # 3+ way split or unresolvable tie — no elimination
    return VoteResult(
        eliminated_player=None,
        vote_counts=dict(counts),
        was_tiebreak=False,
    )


def check_win_condition(
    alive_players: list[dict[str, str]],
) -> str | None:
    """Check whether the game has been won.

    Args:
        alive_players: List of dicts with at least a ``"role"`` key.

    Returns:
        ``"villagers"`` if all werewolves are dead,
        ``"werewolves"`` if werewolves equal or outnumber others,
        or ``None`` if the game continues.
    """
    wolf_count = sum(1 for p in alive_players if p["role"] == "werewolf")
    non_wolf_count = len(alive_players) - wolf_count

    if wolf_count == 0:
        return "villagers"
    if wolf_count >= non_wolf_count:
        return "werewolves"
    return None
