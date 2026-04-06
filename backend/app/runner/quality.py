"""Quality checks for batch game execution.

Task 6 — After each game completes:
  - Check if game.is_degraded is True; track degraded count.
  - Log warning if degraded rate exceeds 20%.
After batch completes:
  - Log final summary: total games, completed, discarded, degraded count,
    games per profile, win rates by faction.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEGRADED_THRESHOLD = 0.20


@dataclass
class QualityTracker:
    """Accumulates quality metrics during a batch run."""

    total: int = 0
    completed: int = 0
    discarded: int = 0
    failed: int = 0
    degraded: int = 0

    # faction -> win count
    wins_by_faction: Counter = field(default_factory=Counter)
    # profile name -> game count
    games_per_profile: Counter = field(default_factory=Counter)

    def record_game(
        self,
        *,
        is_degraded: bool = False,
        status: str = "completed",
        winner: str | None = None,
        profiles: list[str] | None = None,
    ) -> None:
        """Record the outcome of a single completed game.

        Parameters
        ----------
        is_degraded:
            Whether the game was flagged as degraded (>30% defaults).
        status:
            Game status: "completed", "discarded", or "failed".
        winner:
            Winning faction ("villagers" or "werewolves"), or None.
        profiles:
            List of persuasion profiles used in this game.
        """
        self.total += 1

        if status == "completed":
            self.completed += 1
        elif status == "discarded":
            self.discarded += 1
        elif status == "failed":
            self.failed += 1
        else:
            self.completed += 1  # treat unknown as completed

        if is_degraded:
            self.degraded += 1

        if winner:
            self.wins_by_faction[winner] += 1

        if profiles:
            for profile in profiles:
                self.games_per_profile[profile] += 1

        # Warn if degraded rate exceeds threshold
        finished = self.completed + self.discarded
        if finished > 0:
            degraded_rate = self.degraded / finished
            if degraded_rate > DEGRADED_THRESHOLD:
                logger.warning(
                    "Quality alert: degraded rate %.1f%% (%d/%d) exceeds %.0f%% threshold",
                    degraded_rate * 100,
                    self.degraded,
                    finished,
                    DEGRADED_THRESHOLD * 100,
                )

    def log_summary(self) -> dict:
        """Log and return the final batch quality summary.

        Returns
        -------
        dict
            Summary dict suitable for JSON serialization.
        """
        finished = self.completed + self.discarded
        degraded_rate = (
            (self.degraded / finished * 100.0) if finished > 0 else 0.0
        )

        # Win rates by faction
        total_decided = sum(self.wins_by_faction.values())
        win_rates: dict[str, float] = {}
        for faction, count in self.wins_by_faction.items():
            win_rates[faction] = (
                round(count / total_decided * 100.0, 1)
                if total_decided > 0
                else 0.0
            )

        summary = {
            "total_games": self.total,
            "completed": self.completed,
            "discarded": self.discarded,
            "failed": self.failed,
            "degraded": self.degraded,
            "degraded_rate_pct": round(degraded_rate, 1),
            "games_per_profile": dict(self.games_per_profile),
            "win_rates_by_faction": win_rates,
        }

        logger.info(
            "Batch summary: %d total | %d completed | %d discarded | "
            "%d failed | %d degraded (%.1f%%)",
            self.total,
            self.completed,
            self.discarded,
            self.failed,
            self.degraded,
            degraded_rate,
        )
        logger.info("Games per profile: %s", dict(self.games_per_profile))
        logger.info("Win rates by faction: %s", win_rates)

        return summary
