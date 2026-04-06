"""Batch runner for executing multiple Werewolf games.

Task 2 — Runs N games with configurable concurrency, balanced profile
assignment, and per-game error handling.
Task 5 — ``resume_batch``: resumption logic for interrupted batches.
Task 6 — Quality checks integrated into batch execution.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.engine.agent_interface import AgentInterface, MockAgent
from app.engine.game_loop import run_game
from app.models.batch import Batch
from app.models.game import Game
from app.runner.assignment import generate_assignment_plan
from app.runner.progress import ProgressTracker
from app.runner.quality import QualityTracker

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Active tracker registry — accessed by API status endpoint
# ------------------------------------------------------------------

_active_trackers: dict[str, ProgressTracker] = {}
_active_quality: dict[str, QualityTracker] = {}


def get_tracker(batch_id: str) -> ProgressTracker | None:
    """Return the live ProgressTracker for an in-flight batch, if any."""
    return _active_trackers.get(batch_id)


def get_quality_tracker(batch_id: str) -> QualityTracker | None:
    """Return the live QualityTracker for an in-flight batch, if any."""
    return _active_quality.get(batch_id)


@dataclass
class BatchConfig:
    """Configuration for a batch run."""

    num_games: int
    max_parallelism: int = 1
    debate_cap: int = 10
    use_llm: bool = False


def _create_agents(
    assignment: list[dict[str, Any]],
    use_llm: bool,
    config: dict[str, Any] | None = None,
) -> list[AgentInterface]:
    """Create agent instances from a game assignment plan.

    Parameters
    ----------
    assignment:
        List of 7 dicts with keys: player_index, role, persuasion_profile, persona.
    use_llm:
        If True, create LLMAgent instances; otherwise MockAgent.
    config:
        Optional config dict passed to LLMAgent.

    Returns
    -------
    list[AgentInterface]
        7 agent instances ready for a game.
    """
    agents: list[AgentInterface] = []

    for entry in assignment:
        player_id = str(uuid.uuid4())
        agent_name = f"Agent_{entry['player_index']}"
        role = entry["role"]

        if use_llm:
            from app.agent.llm_agent import LLMAgent

            agent = LLMAgent(
                player_id=player_id,
                agent_name=agent_name,
                role=role,
                persona=entry["persona"],
                persuasion_profile=entry["persuasion_profile"],
                config=config,
            )
        else:
            agent = MockAgent(
                player_id=player_id,
                agent_name=agent_name,
                role=role,
            )

        agents.append(agent)

    return agents


def _build_game_config(
    assignment: list[dict[str, Any]],
    agents: list[AgentInterface],
    batch_config: BatchConfig,
) -> dict[str, Any]:
    """Build the game config dict from assignment data and batch config.

    Maps player_id -> persuasion_profile and player_id -> persona so
    that run_game() can persist them on the Player records.
    """
    profiles: dict[str, str] = {}
    personas: dict[str, str] = {}

    for entry, agent in zip(assignment, agents):
        profiles[agent.player_id] = entry["persuasion_profile"]
        personas[agent.player_id] = entry["persona"]

    return {
        "debate_cap": batch_config.debate_cap,
        "profiles": profiles,
        "personas": personas,
    }


async def _run_single_game(
    db_session: AsyncSession,
    batch: Batch,
    game_index: int,
    assignment: list[dict[str, Any]],
    batch_config: BatchConfig,
    progress: ProgressTracker | None = None,
    quality: QualityTracker | None = None,
) -> None:
    """Run a single game within a batch, handling errors gracefully.

    Updates the batch record's completed/failed counts after the game.
    Integrates with progress and quality trackers when provided.
    """
    game_num = game_index + 1
    if progress:
        progress.mark_game_started(game_num)

    start = time.monotonic()

    try:
        agents = _create_agents(assignment, batch_config.use_llm)
        game_config = _build_game_config(assignment, agents, batch_config)

        game = await run_game(db_session, agents, game_config)

        # Link game to batch
        game.batch_id = batch.id

        batch.completed_games += 1

        duration = time.monotonic() - start

        # Quality check (Task 6)
        if quality:
            profiles_used = [
                entry.get("persuasion_profile", "baseline")
                for entry in assignment
            ]
            quality.record_game(
                is_degraded=game.is_degraded,
                status=game.status,
                winner=game.winner,
                profiles=profiles_used,
            )

        # Progress tracking (Task 4)
        if progress:
            progress.update(
                game_num,
                batch.total_games,
                duration,
                failed=False,
                degraded=game.is_degraded,
            )

        logger.info(
            "Batch %s: game %d/%d completed (game_id=%s, winner=%s, %.1fs)",
            batch.id, game_num, batch.total_games,
            game.id, game.winner, duration,
        )

    except Exception:
        batch.failed_games += 1
        duration = time.monotonic() - start

        if progress:
            progress.update(
                game_num,
                batch.total_games,
                duration,
                failed=True,
            )
        if quality:
            quality.record_game(status="failed")

        logger.exception(
            "Batch %s: game %d/%d failed",
            batch.id, game_num, batch.total_games,
        )

    await db_session.flush()


async def run_batch(
    db_session: AsyncSession,
    config: BatchConfig,
) -> Batch:
    """Execute a batch of Werewolf games.

    Parameters
    ----------
    db_session:
        Async SQLAlchemy session. The caller is responsible for
        committing after this coroutine returns.
    config:
        Batch configuration (num_games, parallelism, etc.).

    Returns
    -------
    Batch
        The completed Batch model instance.
    """
    # 1. Generate assignment plan
    plan = generate_assignment_plan(config.num_games)

    # 2. Create Batch record (store plan in config for resumption)
    batch = Batch(
        id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        total_games=config.num_games,
        completed_games=0,
        failed_games=0,
        status="running",
        config={
            "num_games": config.num_games,
            "max_parallelism": config.max_parallelism,
            "debate_cap": config.debate_cap,
            "use_llm": config.use_llm,
            "assignment_plan": plan,
        },
    )
    db_session.add(batch)
    await db_session.flush()

    batch_id_str = str(batch.id)

    logger.info(
        "Batch %s started: %d games, max_parallelism=%d, use_llm=%s",
        batch.id, config.num_games, config.max_parallelism, config.use_llm,
    )

    # 3. Set up progress and quality trackers
    progress = ProgressTracker(config.num_games)
    quality = QualityTracker()
    _active_trackers[batch_id_str] = progress
    _active_quality[batch_id_str] = quality

    try:
        # 4. Execute games with configurable concurrency
        await _execute_games(
            db_session, batch, plan, config, progress, quality,
            start_index=0,
        )

        # 5. Finalize batch — log quality summary (Task 6)
        summary = quality.log_summary()

        batch.status = "completed"
        batch.completed_at = datetime.now(timezone.utc)
        await db_session.flush()

        logger.info(
            "Batch %s completed: %d/%d games succeeded, %d failed",
            batch.id, batch.completed_games, batch.total_games, batch.failed_games,
        )

    except Exception:
        logger.exception("Batch %s failed", batch.id)
        batch.status = "failed"
        await db_session.flush()
        raise

    finally:
        _active_trackers.pop(batch_id_str, None)
        _active_quality.pop(batch_id_str, None)

    return batch


async def _execute_games(
    db_session: AsyncSession,
    batch: Batch,
    plan: list[list[dict[str, Any]]],
    config: BatchConfig,
    progress: ProgressTracker,
    quality: QualityTracker,
    start_index: int = 0,
) -> None:
    """Run games from ``start_index`` through the end of the plan."""
    semaphore = asyncio.Semaphore(config.max_parallelism)

    async def _guarded_run(game_index: int, assignment: list[dict[str, Any]]) -> None:
        async with semaphore:
            # Each concurrent game gets its own session to avoid shared-session
            # race conditions when max_parallelism > 1.
            async with async_session_factory() as game_session:
                try:
                    await _run_single_game(
                        game_session, batch, game_index, assignment, config,
                        progress=progress,
                        quality=quality,
                    )
                    await game_session.commit()
                except Exception:
                    await game_session.rollback()
                    raise

    remaining_plan = plan[start_index:]

    if config.max_parallelism == 1:
        # Sequential execution — simpler and avoids session concurrency issues
        for i, assignment in enumerate(remaining_plan):
            game_index = start_index + i
            await _run_single_game(
                db_session, batch, game_index, assignment, config,
                progress=progress,
                quality=quality,
            )
    else:
        # Concurrent execution with semaphore; each task owns its own session.
        tasks = [
            asyncio.create_task(
                _guarded_run(start_index + i, assignment)
            )
            for i, assignment in enumerate(remaining_plan)
        ]
        await asyncio.gather(*tasks)


# ------------------------------------------------------------------
# resume_batch — Task 5: resumption logic
# ------------------------------------------------------------------

async def resume_batch(
    db_session: AsyncSession,
    batch_id: uuid.UUID,
) -> Batch:
    """Resume an interrupted batch from the last completed game.

    Steps:
      1. Find batch with given ID.
      2. Check it has status "running" or "paused".
      3. Find last completed game number in that batch.
      4. Mark any games with status "running" (interrupted) as "discarded".
      5. Resume from next game using the pre-generated assignment plan
         stored in batch.config.

    Parameters
    ----------
    db_session:
        Async SQLAlchemy session.
    batch_id:
        UUID of the batch to resume.

    Returns
    -------
    Batch
        The completed Batch model instance.

    Raises
    ------
    ValueError
        If batch not found or not in a resumable state.
    """
    # 1. Find batch
    result = await db_session.execute(
        select(Batch).where(Batch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if batch is None:
        raise ValueError(f"Batch {batch_id} not found")

    # 2. Check status is resumable
    if batch.status not in ("running", "paused"):
        raise ValueError(
            f"Batch {batch_id} has status '{batch.status}'; "
            f"only 'running' or 'paused' batches can be resumed"
        )

    # 3. Count completed games in this batch
    completed_result = await db_session.execute(
        select(Game)
        .where(Game.batch_id == batch_id)
        .where(Game.status.in_(["completed", "discarded"]))
    )
    completed_games = completed_result.scalars().all()
    completed_count = len(completed_games)

    # 4. Mark interrupted games (status=running) as discarded
    interrupted_result = await db_session.execute(
        select(Game)
        .where(Game.batch_id == batch_id)
        .where(Game.status == "running")
    )
    interrupted_games = interrupted_result.scalars().all()
    for game in interrupted_games:
        game.status = "discarded"
        logger.info(
            "Marked interrupted game %s as discarded (batch %s)",
            game.id, batch_id,
        )

    # 5. Resume from next game
    batch.status = "running"
    await db_session.flush()

    batch_config = BatchConfig(
        num_games=batch.config.get("num_games", batch.total_games),
        max_parallelism=batch.config.get("max_parallelism", 1),
        debate_cap=batch.config.get("debate_cap", 10),
        use_llm=batch.config.get("use_llm", False),
    )

    # Recover assignment plan from batch config
    plan = batch.config.get("assignment_plan")
    if plan is None:
        logger.warning(
            "Batch %s has no stored assignment plan; regenerating",
            batch_id,
        )
        plan = generate_assignment_plan(batch_config.num_games)

    start_index = completed_count
    if start_index >= batch_config.num_games:
        logger.info(
            "Batch %s: all %d games already completed, nothing to resume",
            batch_id, batch_config.num_games,
        )
        batch.status = "completed"
        batch.completed_at = datetime.now(timezone.utc)
        await db_session.flush()
        return batch

    logger.info(
        "Resuming batch %s from game %d/%d (%d completed, %d interrupted -> discarded)",
        batch_id,
        start_index + 1,
        batch_config.num_games,
        completed_count,
        len(interrupted_games),
    )

    batch_id_str = str(batch_id)
    progress = ProgressTracker(batch_config.num_games)
    quality = QualityTracker()

    # Pre-populate progress with already-completed games
    for i in range(completed_count):
        progress.update(i + 1, batch_config.num_games, 0.0)

    _active_trackers[batch_id_str] = progress
    _active_quality[batch_id_str] = quality

    try:
        await _execute_games(
            db_session, batch, plan, batch_config, progress, quality,
            start_index=start_index,
        )

        summary = quality.log_summary()

        batch.status = "completed"
        batch.completed_at = datetime.now(timezone.utc)
        await db_session.flush()

        logger.info(
            "Resumed batch %s completed: %d/%d games succeeded, %d failed",
            batch.id, batch.completed_games, batch.total_games, batch.failed_games,
        )

    except Exception:
        logger.exception("Resumed batch %s failed", batch_id)
        batch.status = "failed"
        await db_session.flush()
        raise

    finally:
        _active_trackers.pop(batch_id_str, None)
        _active_quality.pop(batch_id_str, None)

    return batch
