"""Tests for runner.quality — quality tracking (UT-129 … UT-131)."""

from __future__ import annotations

import pytest

from app.runner.quality import QualityTracker


# ---- UT-129 ----------------------------------------------------------------

def test_ut129_degraded_count():
    """Degraded count increments when is_degraded=True."""
    qt = QualityTracker()

    qt.record_game(is_degraded=False, status="completed")
    assert qt.degraded == 0

    qt.record_game(is_degraded=True, status="completed")
    assert qt.degraded == 1

    qt.record_game(is_degraded=True, status="completed")
    assert qt.degraded == 2

    qt.record_game(is_degraded=False, status="completed")
    assert qt.degraded == 2

    assert qt.total == 4
    assert qt.completed == 4


# ---- UT-130 ----------------------------------------------------------------

def test_ut130_win_tracking():
    """Win tracking counts villager and werewolf wins correctly."""
    qt = QualityTracker()

    qt.record_game(status="completed", winner="villagers")
    qt.record_game(status="completed", winner="villagers")
    qt.record_game(status="completed", winner="werewolves")
    qt.record_game(status="completed", winner="villagers")
    qt.record_game(status="completed", winner="werewolves")

    assert qt.wins_by_faction["villagers"] == 3
    assert qt.wins_by_faction["werewolves"] == 2
    assert qt.total == 5

    # Verify summary win rates
    summary = qt.log_summary()
    assert summary["win_rates_by_faction"]["villagers"] == 60.0
    assert summary["win_rates_by_faction"]["werewolves"] == 40.0


# ---- UT-131 ----------------------------------------------------------------

def test_ut131_profile_tracking():
    """Profile tracking counts games per profile."""
    qt = QualityTracker()

    qt.record_game(
        status="completed",
        profiles=["ethos", "pathos", "logos", "baseline",
                  "authority_socialproof", "reciprocity_liking",
                  "scarcity_commitment"],
    )
    qt.record_game(
        status="completed",
        profiles=["ethos", "pathos", "logos", "baseline",
                  "authority_socialproof", "reciprocity_liking",
                  "scarcity_commitment"],
    )
    qt.record_game(
        status="completed",
        profiles=["ethos", "logos"],
    )

    assert qt.games_per_profile["ethos"] == 3
    assert qt.games_per_profile["pathos"] == 2
    assert qt.games_per_profile["logos"] == 3
    assert qt.games_per_profile["baseline"] == 2
    assert qt.total == 3
