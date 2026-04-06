"""Day phase bidding and speech selection for Werewolf AI Agents.

Pure logic — no database calls, no LLM calls.
"""

from __future__ import annotations

import random
import re


def extract_mentions(statement: str, player_names: list[str]) -> list[str]:
    """Find which player names are mentioned in a public statement.

    Matching is case-insensitive and looks for whole-word occurrences.

    Args:
        statement: The text of a public statement.
        player_names: All player names to search for.

    Returns:
        List of mentioned player names (preserving original casing),
        in the order they first appear.
    """
    mentioned: list[str] = []
    lower_statement = statement.lower()
    for name in player_names:
        # Use word-boundary matching so "Al" doesn't match "Also"
        pattern = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
        if pattern.search(statement):
            if name not in mentioned:
                mentioned.append(name)
    return mentioned


def select_speaker(
    bids: dict[str, int],
    previous_mentions: list[str],
) -> str:
    """Select the next speaker based on bids and mention priority.

    Resolution order:
      1. Highest bid value wins.
      2. Among ties, players mentioned in the previous turn's public
         statement get priority (earlier mention = higher priority).
      3. Further ties broken randomly.

    Args:
        bids: Mapping of player_id -> bid level (integer).
        previous_mentions: Ordered list of player IDs mentioned in the
            previous turn's public statement (first = highest priority).

    Returns:
        The player_id selected to speak.

    Raises:
        ValueError: If bids is empty.
    """
    if not bids:
        raise ValueError("At least one bid is required")

    max_bid = max(bids.values())
    top_bidders = [pid for pid, bid in bids.items() if bid == max_bid]

    if len(top_bidders) == 1:
        return top_bidders[0]

    # Tiebreak by mention priority
    for mentioned_player in previous_mentions:
        if mentioned_player in top_bidders:
            return mentioned_player

    # Further ties: random
    return random.choice(top_bidders)
