"""Role assignment for Werewolf AI Agents.

Fixed distribution for 7 players:
  2 werewolves, 1 seer, 1 doctor, 3 villagers.

Pure logic — no database calls, no LLM calls.
"""

from __future__ import annotations

import random

ROLE_DISTRIBUTION: list[str] = [
    "werewolf",
    "werewolf",
    "seer",
    "doctor",
    "villager",
    "villager",
    "villager",
]

EXPECTED_PLAYER_COUNT = 7


def assign_roles(player_ids: list[str]) -> dict[str, str]:
    """Randomly assign roles to players.

    Args:
        player_ids: Exactly 7 unique player identifiers.

    Returns:
        Mapping of player_id -> role.

    Raises:
        ValueError: If the number of players is not 7.
    """
    if len(player_ids) != EXPECTED_PLAYER_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_PLAYER_COUNT} players, got {len(player_ids)}"
        )

    roles = list(ROLE_DISTRIBUTION)
    random.shuffle(roles)
    return dict(zip(player_ids, roles))


def get_private_info(
    player_id: str,
    role: str,
    all_assignments: dict[str, str],
) -> dict:
    """Return the private information a player should receive at game start.

    - Werewolves learn who their teammate is.
    - All other roles learn only their own role.

    Args:
        player_id: The player requesting info.
        role: That player's assigned role.
        all_assignments: Full mapping of player_id -> role.

    Returns:
        Dict with at least ``role``; werewolves also get ``teammates``.
    """
    info: dict = {"role": role}

    if role == "werewolf":
        info["teammates"] = [
            pid
            for pid, r in all_assignments.items()
            if r == "werewolf" and pid != player_id
        ]

    return info
