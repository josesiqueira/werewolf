"""Mayor election and succession for Werewolf AI Agents.

Pure logic — no database calls, no LLM calls.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass


@dataclass
class MayorResult:
    """Outcome of a mayor election."""
    winner: str
    vote_counts: dict[str, int]
    was_tiebreak: bool


def run_mayor_election(
    candidates: list[str],
    votes: dict[str, str],
) -> MayorResult:
    """Tally votes and elect a mayor by plurality.

    Args:
        candidates: List of candidate player IDs.
        votes: Mapping of voter_id -> candidate_id they voted for.

    Returns:
        MayorResult with the winning candidate.

    Raises:
        ValueError: If no candidates are provided.
    """
    if not candidates:
        raise ValueError("At least one candidate is required")

    # Count votes for each candidate
    counts = Counter(votes.values())
    # Ensure all candidates appear in counts (even with 0 votes)
    for c in candidates:
        counts.setdefault(c, 0)

    max_votes = max(counts.values())
    top_candidates = [c for c in candidates if counts[c] == max_votes]

    was_tiebreak = len(top_candidates) > 1
    winner = random.choice(top_candidates) if was_tiebreak else top_candidates[0]

    return MayorResult(
        winner=winner,
        vote_counts=dict(counts),
        was_tiebreak=was_tiebreak,
    )


def handle_mayor_succession(
    dead_mayor: str,
    alive_players: list[str],
    successor_choice: str | None,
) -> str:
    """Determine the new mayor after the current one is eliminated.

    The dead mayor may nominate a successor. If the choice is invalid
    (not alive) or None, a random alive player is selected.

    Args:
        dead_mayor: The eliminated mayor's player ID.
        alive_players: Currently alive player IDs.
        successor_choice: The dead mayor's nominated successor (or None).

    Returns:
        The new mayor's player ID.

    Raises:
        ValueError: If there are no alive players to succeed.
    """
    if not alive_players:
        raise ValueError("No alive players available for succession")

    eligible = [p for p in alive_players if p != dead_mayor]
    if not eligible:
        raise ValueError("No eligible players for mayor succession")

    if successor_choice is not None and successor_choice in eligible:
        return successor_choice

    return random.choice(eligible)
