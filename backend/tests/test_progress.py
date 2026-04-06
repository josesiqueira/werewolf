"""Tests for runner.progress — progress tracking (UT-126 … UT-128)."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from app.runner.progress import ProgressTracker


# ---- UT-126 ----------------------------------------------------------------

def test_ut126_completion_pct_and_eta():
    """After 5 of 10 games at 30s each, completion_pct=50.0 and ETA~150s."""
    tracker = ProgressTracker(total_games=10)

    for i in range(1, 6):
        tracker.update(game_num=i, total_games=10, game_duration_seconds=30.0)

    status = tracker.get_status()
    assert status["completion_pct"] == 50.0
    # ETA = avg_duration(30) * remaining(5) = 150
    assert status["eta_seconds"] == 150.0


# ---- UT-127 ----------------------------------------------------------------

def test_ut127_games_per_minute():
    """games_per_minute = finished / elapsed * 60."""
    tracker = ProgressTracker(total_games=10)

    # Simulate: 4 games completed in exactly 120 seconds elapsed
    # games_per_minute should be 4/120*60 = 2.0
    with patch("app.runner.progress.time") as mock_time:
        # _started_at is set in __init__ using time.monotonic()
        # We need to control monotonic calls
        pass

    # Simpler approach: just call update and verify the formula is reasonable
    tracker = ProgressTracker(total_games=10)
    # Record the start time, then monkey-patch _started_at
    tracker._started_at = time.monotonic() - 120.0  # pretend started 120s ago

    for i in range(1, 5):
        tracker.update(game_num=i, total_games=10, game_duration_seconds=30.0)

    status = tracker.get_status()
    # 4 games in 120s = 2.0 games/min
    assert status["games_per_minute"] == pytest.approx(2.0, abs=0.1)


# ---- UT-128 ----------------------------------------------------------------

def test_ut128_initial_status():
    """Initial status before any updates shows 0 completed."""
    tracker = ProgressTracker(total_games=10)
    status = tracker.get_status()

    assert status["completed"] == 0
    assert status["failed"] == 0
    assert status["degraded"] == 0
    assert status["completion_pct"] == 0.0
    assert status["eta_seconds"] == 0.0
    assert status["games_per_minute"] == 0.0
    assert status["total_games"] == 10
