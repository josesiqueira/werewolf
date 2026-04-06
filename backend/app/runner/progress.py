"""Progress tracking for batch game execution.

Task 4 — ProgressTracker maintains real-time metrics during a batch run:
  - current game / total games
  - completion percentage
  - estimated time remaining (rolling average of game durations)
  - games per minute rate
  - degraded game count
Logs progress to stdout every 10 games.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from threading import Lock

logger = logging.getLogger(__name__)

# Rolling window size for ETA estimation
_ROLLING_WINDOW = 20


class ProgressTracker:
    """Track batch execution progress with ETA estimation.

    Thread-safe — multiple concurrent games can call ``update`` safely.
    """

    def __init__(self, total_games: int) -> None:
        self.total_games = total_games
        self._completed = 0
        self._failed = 0
        self._degraded = 0
        self._current_game = 0
        self._started_at: float = time.monotonic()
        self._durations: deque[float] = deque(maxlen=_ROLLING_WINDOW)
        self._lock = Lock()
        self._last_log_milestone = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(
        self,
        game_num: int,
        total_games: int,
        game_duration_seconds: float,
        *,
        failed: bool = False,
        degraded: bool = False,
    ) -> None:
        """Record completion of a game and update metrics.

        Parameters
        ----------
        game_num:
            1-based index of the game that just finished.
        total_games:
            Total games in the batch (kept in sync with tracker).
        game_duration_seconds:
            Wall-clock seconds the game took to run.
        failed:
            Whether the game failed (error, not just discarded).
        degraded:
            Whether the game was flagged as degraded.
        """
        with self._lock:
            self.total_games = total_games
            self._current_game = game_num
            self._durations.append(game_duration_seconds)

            if failed:
                self._failed += 1
            else:
                self._completed += 1

            if degraded:
                self._degraded += 1

            # Log every 10 games
            finished = self._completed + self._failed
            milestone = (finished // 10) * 10
            if milestone > 0 and milestone > self._last_log_milestone:
                self._last_log_milestone = milestone
                status = self.get_status()
                logger.info(
                    "Batch progress: %d/%d games (%.1f%%) | "
                    "ETA: %.0fs | %.1f games/min | "
                    "degraded: %d | failed: %d",
                    status["completed"] + status["failed"],
                    status["total_games"],
                    status["completion_pct"],
                    status["eta_seconds"],
                    status["games_per_minute"],
                    status["degraded"],
                    status["failed"],
                )

    def mark_game_started(self, game_num: int) -> None:
        """Record that a game has started (updates current_game)."""
        with self._lock:
            self._current_game = game_num

    def get_status(self) -> dict:
        """Return current progress metrics.

        Returns
        -------
        dict with keys:
            current_game, total_games, completed, failed, degraded,
            completion_pct, eta_seconds, games_per_minute,
            elapsed_seconds
        """
        with self._lock:
            finished = self._completed + self._failed
            completion_pct = (
                (finished / self.total_games * 100.0)
                if self.total_games > 0
                else 0.0
            )

            # Rolling average duration for ETA
            if self._durations:
                avg_duration = sum(self._durations) / len(self._durations)
            else:
                avg_duration = 0.0

            remaining = max(0, self.total_games - finished)
            eta_seconds = avg_duration * remaining

            elapsed = time.monotonic() - self._started_at
            games_per_minute = (
                (finished / elapsed * 60.0) if elapsed > 0 and finished > 0 else 0.0
            )

            return {
                "current_game": self._current_game,
                "total_games": self.total_games,
                "completed": self._completed,
                "failed": self._failed,
                "degraded": self._degraded,
                "completion_pct": round(completion_pct, 1),
                "eta_seconds": round(eta_seconds, 1),
                "games_per_minute": round(games_per_minute, 2),
                "elapsed_seconds": round(elapsed, 1),
            }
