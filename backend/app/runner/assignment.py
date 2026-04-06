"""Profile assignment strategy for batch game execution.

Task 1 — Balanced randomization using a Latin-square-inspired approach.
Each of 7 persuasion profiles is paired with each of 4 roles roughly
equally across N games, with cell counts within +/-1 of the mean.
"""

from __future__ import annotations

import random
from typing import Any

from app.agent.personas import PERSONA_NAMES

# The 7 persuasion profiles used in the experiment
PROFILES: list[str] = [
    "ethos",
    "pathos",
    "logos",
    "authority_socialproof",
    "reciprocity_liking",
    "scarcity_commitment",
    "baseline",
]

# The 4 distinct roles in a 7-player game (2 werewolves, 1 seer, 1 doctor, 3 villagers)
ROLES: list[str] = ["werewolf", "seer", "doctor", "villager"]

# Role distribution per game: 2 werewolves, 1 seer, 1 doctor, 3 villagers = 7 players
ROLE_DISTRIBUTION: list[str] = [
    "werewolf", "werewolf", "seer", "doctor",
    "villager", "villager", "villager",
]


def _build_target_matrix(num_games: int, players_per_game: int = 7) -> dict[tuple[str, str], int]:
    """Compute the ideal number of times each (profile, role) cell should appear.

    With 7 profiles and 7 players per game, each game assigns every profile
    exactly once. The role distribution is fixed (2W, 1S, 1D, 3V), so across
    N games the total slots per role are:
      - werewolf:  2N
      - seer:      1N
      - doctor:    1N
      - villager:  3N

    Each profile should fill each role slot roughly equally:
      - werewolf:  2N / 7  per profile
      - seer:      1N / 7  per profile
      - doctor:    1N / 7  per profile
      - villager:  3N / 7  per profile

    Returns a dict mapping (profile, role) -> target count.
    """
    role_totals = {
        "werewolf": 2 * num_games,
        "seer": 1 * num_games,
        "doctor": 1 * num_games,
        "villager": 3 * num_games,
    }

    targets: dict[tuple[str, str], int] = {}
    for role, total in role_totals.items():
        base = total // len(PROFILES)
        remainder = total % len(PROFILES)
        # Distribute remainder across profiles deterministically
        for i, profile in enumerate(PROFILES):
            targets[(profile, role)] = base + (1 if i < remainder else 0)

    return targets


def generate_assignment_plan(
    num_games: int,
    players_per_game: int = 7,
) -> list[list[dict[str, Any]]]:
    """Generate a balanced assignment plan for a batch of games.

    Uses a Latin-square-inspired greedy approach: for each game, assign
    profiles to role slots by picking the (profile, role) pair that is
    most under-represented relative to its target count.

    Parameters
    ----------
    num_games:
        Number of games in the batch (typically 200-500).
    players_per_game:
        Players per game (default 7, must be 7 for the fixed role distribution).

    Returns
    -------
    list[list[dict]]
        A list of ``num_games`` game assignments, where each game is a list
        of 7 dicts with keys: ``player_index``, ``role``, ``persuasion_profile``,
        ``persona``.
    """
    if players_per_game != 7:
        raise ValueError(
            f"players_per_game must be 7 (fixed role distribution), got {players_per_game}"
        )

    targets = _build_target_matrix(num_games, players_per_game)

    # Running count of how many times each (profile, role) has been assigned
    counts: dict[tuple[str, str], int] = {key: 0 for key in targets}

    plan: list[list[dict[str, Any]]] = []

    for game_idx in range(num_games):
        # For each game we need to assign 7 profiles to the 7 role slots
        # (one profile per player, no duplicate profiles within a game).
        roles = list(ROLE_DISTRIBUTION)  # copy
        random.shuffle(roles)

        available_profiles = list(PROFILES)  # all 7 profiles, one per player

        # Greedy assignment: for each role slot, pick the available profile
        # that has the largest deficit (target - current count) for that role.
        assignments: list[tuple[str, str]] = []  # (profile, role) pairs

        for role in roles:
            # Score each available profile by how much it needs this role
            best_profile = None
            best_deficit = -float("inf")

            for profile in available_profiles:
                key = (profile, role)
                deficit = targets[key] - counts[key]
                if deficit > best_deficit:
                    best_deficit = deficit
                    best_profile = profile

            assert best_profile is not None
            assignments.append((best_profile, role))
            available_profiles.remove(best_profile)
            counts[(best_profile, role)] += 1

        # Assign personas (shuffled for each game)
        personas = random.sample(PERSONA_NAMES, k=players_per_game)

        game_assignment: list[dict[str, Any]] = []
        for player_idx, ((profile, role), persona) in enumerate(
            zip(assignments, personas)
        ):
            game_assignment.append({
                "player_index": player_idx,
                "role": role,
                "persuasion_profile": profile,
                "persona": persona,
            })

        plan.append(game_assignment)

    return plan
