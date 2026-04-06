"""Tests for runner.assignment — profile assignment balance (UT-121 … UT-125)."""

from __future__ import annotations

from collections import Counter

import pytest

from app.runner.assignment import (
    PROFILES,
    ROLE_DISTRIBUTION,
    ROLES,
    generate_assignment_plan,
)


# ---- helpers ---------------------------------------------------------------

def _count_profile_role(plan: list) -> Counter:
    """Return Counter of (profile, role) pairs across all games."""
    c: Counter = Counter()
    for game in plan:
        for p in game:
            c[(p["persuasion_profile"], p["role"])] += 1
    return c


# ---- UT-121 ----------------------------------------------------------------

def test_ut121_balance_over_210_games():
    """Over 210 games, each (profile x role) count is within +/-2 of mean."""
    plan = generate_assignment_plan(210)
    counts = _count_profile_role(plan)

    role_totals = Counter(ROLE_DISTRIBUTION)  # werewolf:2, seer:1, doctor:1, villager:3
    for role in ROLES:
        total_slots = role_totals[role] * 210
        mean = total_slots / len(PROFILES)
        for profile in PROFILES:
            actual = counts.get((profile, role), 0)
            assert abs(actual - mean) <= 2, (
                f"({profile}, {role}): count={actual}, mean={mean:.1f}, "
                f"deviation={abs(actual - mean):.1f} exceeds +/-2"
            )


# ---- UT-122 ----------------------------------------------------------------

def test_ut122_correct_role_distribution():
    """Each game has exactly 7 players with distribution 2W, 1S, 1D, 3V."""
    plan = generate_assignment_plan(30)
    expected_dist = Counter(ROLE_DISTRIBUTION)
    for i, game in enumerate(plan):
        assert len(game) == 7, f"Game {i}: expected 7 players, got {len(game)}"
        roles = [p["role"] for p in game]
        assert Counter(roles) == expected_dist, (
            f"Game {i}: role distribution {Counter(roles)} != {expected_dist}"
        )


# ---- UT-123 ----------------------------------------------------------------

def test_ut123_no_duplicate_personas():
    """No duplicate personas within a single game."""
    plan = generate_assignment_plan(50)
    for i, game in enumerate(plan):
        personas = [p["persona"] for p in game]
        assert len(set(personas)) == len(personas), (
            f"Game {i}: duplicate personas: {personas}"
        )


# ---- UT-124 ----------------------------------------------------------------

def test_ut124_all_profiles_appear():
    """All 7 profiles appear in each game assignment."""
    plan = generate_assignment_plan(20)
    for i, game in enumerate(plan):
        profiles_in_game = {p["persuasion_profile"] for p in game}
        assert profiles_in_game == set(PROFILES), (
            f"Game {i}: profiles {profiles_in_game} != {set(PROFILES)}"
        )


# ---- UT-125 ----------------------------------------------------------------

def test_ut125_small_batch_valid():
    """A small batch (7 games) still produces valid assignments."""
    plan = generate_assignment_plan(7)
    assert len(plan) == 7

    expected_dist = Counter(ROLE_DISTRIBUTION)
    for i, game in enumerate(plan):
        assert len(game) == 7
        roles = [p["role"] for p in game]
        assert Counter(roles) == expected_dist
        profiles_in_game = {p["persuasion_profile"] for p in game}
        assert profiles_in_game == set(PROFILES)
        # No duplicate personas
        personas = [p["persona"] for p in game]
        assert len(set(personas)) == len(personas)
