"""Batch API endpoints.

Task 7 — Start, monitor, and list batch runs.

- POST /api/batch       — start a batch (background task)
- GET  /api/batch/{id}/status — progress, ETA, degraded count
- GET  /api/batch       — list all batches
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory, get_session
from app.models.batch import Batch
from app.runner.batch import (
    BatchConfig,
    get_quality_tracker,
    get_tracker,
    run_batch,
)
from app.schemas.batch import BatchCreate, BatchResponse

router = APIRouter(prefix="/api/batch", tags=["batch"])


# ------------------------------------------------------------------
# Background task wrapper
# ------------------------------------------------------------------

async def _run_batch_background(batch_id: uuid.UUID, config: BatchConfig) -> None:
    """Execute a batch in the background with its own DB session.

    The Batch record identified by ``batch_id`` must already exist
    (created by the API endpoint with status "pending").  This function
    transitions it to "running", executes all games, and then marks it
    "completed" (or "failed").
    """
    from app.runner.batch import (
        ProgressTracker,
        QualityTracker,
        _active_quality,
        _active_trackers,
        _execute_games,
        generate_assignment_plan,
    )
    from datetime import datetime, timezone

    async with async_session_factory() as db:
        try:
            # Load the existing batch
            result = await db.execute(
                select(Batch).where(Batch.id == batch_id)
            )
            batch = result.scalar_one()

            # Generate assignment plan and store in config
            plan = generate_assignment_plan(config.num_games)
            stored_config = dict(batch.config or {})
            stored_config["assignment_plan"] = plan
            batch.config = stored_config
            batch.status = "running"
            batch.started_at = datetime.now(timezone.utc)
            await db.flush()

            batch_id_str = str(batch_id)
            progress = ProgressTracker(config.num_games)
            quality = QualityTracker()
            _active_trackers[batch_id_str] = progress
            _active_quality[batch_id_str] = quality

            try:
                await _execute_games(
                    db, batch, plan, config, progress, quality,
                    start_index=0,
                )

                summary = quality.log_summary()
                batch.status = "completed"
                batch.completed_at = datetime.now(timezone.utc)
                await db.flush()
            except Exception:
                batch.status = "failed"
                await db.flush()
                raise
            finally:
                _active_trackers.pop(batch_id_str, None)
                _active_quality.pop(batch_id_str, None)

            await db.commit()

        except Exception:
            await db.rollback()
            raise


# ------------------------------------------------------------------
# POST /api/batch — start a batch
# ------------------------------------------------------------------

@router.post("", response_model=BatchResponse, status_code=202)
async def start_batch(
    body: BatchCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Start a new batch run as a background task.

    Creates the batch record immediately with status "pending" and
    returns it. The actual game execution happens asynchronously in
    a background task.
    """
    from datetime import datetime, timezone

    config = BatchConfig(
        num_games=body.num_games,
        max_parallelism=body.max_parallelism,
        debate_cap=body.debate_cap,
        use_llm=body.use_llm,
    )

    batch = Batch(
        id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        total_games=config.num_games,
        completed_games=0,
        failed_games=0,
        status="pending",
        config={
            "num_games": config.num_games,
            "max_parallelism": config.max_parallelism,
            "debate_cap": config.debate_cap,
            "use_llm": config.use_llm,
        },
        started_at=None,
        completed_at=None,
    )
    db.add(batch)
    await db.flush()

    # Schedule background execution using the pre-created batch ID
    background_tasks.add_task(_run_batch_background, batch.id, config)

    return batch


# ------------------------------------------------------------------
# GET /api/batch/{batch_id}/status — progress + ETA + degraded
# ------------------------------------------------------------------

@router.get("/{batch_id}/status")
async def get_batch_status(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Return live progress, ETA, and degraded count for a batch.

    If the batch is currently running, returns real-time metrics
    from the in-memory ProgressTracker. Otherwise, returns stored
    values from the database.
    """
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch_id_str = str(batch_id)
    tracker = get_tracker(batch_id_str)
    quality = get_quality_tracker(batch_id_str)

    if tracker is not None:
        # Batch is currently running — return live metrics
        status = tracker.get_status()
        degraded = quality.degraded if quality else 0
        return {
            "batch_id": str(batch.id),
            "status": batch.status,
            "total_games": status["total_games"],
            "completed_games": status["completed"],
            "failed_games": status["failed"],
            "current_game": status["current_game"],
            "completion_pct": status["completion_pct"],
            "eta_seconds": status["eta_seconds"],
            "games_per_minute": status["games_per_minute"],
            "elapsed_seconds": status["elapsed_seconds"],
            "degraded_count": degraded,
        }

    # Batch is not running — return stored data
    return {
        "batch_id": str(batch.id),
        "status": batch.status,
        "total_games": batch.total_games,
        "completed_games": batch.completed_games,
        "failed_games": batch.failed_games,
        "current_game": batch.completed_games + batch.failed_games,
        "completion_pct": (
            round(
                (batch.completed_games + batch.failed_games)
                / batch.total_games
                * 100.0,
                1,
            )
            if batch.total_games > 0
            else 0.0
        ),
        "eta_seconds": 0.0,
        "games_per_minute": 0.0,
        "elapsed_seconds": 0.0,
        "degraded_count": 0,
    }


# ------------------------------------------------------------------
# GET /api/batch — list all batches
# ------------------------------------------------------------------

@router.get("", response_model=list[BatchResponse])
async def list_batches(
    db: AsyncSession = Depends(get_session),
) -> Any:
    """List all batches, ordered by creation date (newest first)."""
    result = await db.execute(
        select(Batch).order_by(Batch.created_at.desc())
    )
    batches = result.scalars().all()
    return batches
