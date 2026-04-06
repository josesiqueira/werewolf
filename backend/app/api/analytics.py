"""Analytics API endpoints.

Phase 5, Task 4 — Expose computed metrics via REST endpoints.
All endpoints accept an optional ``batch_id`` query parameter to scope
results to a specific batch.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.accusation_graph import build_accusation_graph
from app.analytics.detection import detection_difficulty_matrix
from app.analytics.metrics import (
    bandwagon_dynamics,
    bus_throwing_rate,
    deception_index,
    survival_duration_by_role_profile,
    technique_adherence_rate,
    vote_swing_per_message,
    win_rate_by_faction_profile,
)
from app.database import get_session

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/winrates")
async def get_winrates(
    batch_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Win rate matrix: faction x profile with counts, mean, SEM, 95% CI."""
    return await win_rate_by_faction_profile(db, batch_id)


@router.get("/survival")
async def get_survival(
    batch_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Survival duration by role x profile."""
    return await survival_duration_by_role_profile(db, batch_id)


@router.get("/techniques")
async def get_techniques(
    batch_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Aggregated technique metrics.

    Returns technique adherence, deception index, detection difficulty,
    bus-throwing rate, and bandwagon dynamics.
    """
    adherence = await technique_adherence_rate(db, batch_id)
    deception = await deception_index(db, batch_id)
    detection = await detection_difficulty_matrix(db, batch_id)
    bus = await bus_throwing_rate(db, batch_id)
    bandwagon = await bandwagon_dynamics(db, batch_id)

    return {
        "technique_adherence": adherence,
        "deception_index": deception,
        "detection_difficulty": detection,
        "bus_throwing": bus,
        "bandwagon_dynamics": bandwagon,
    }


@router.get("/accusations")
async def get_accusations(
    batch_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Accusation graph data for D3 force-directed visualization."""
    return await build_accusation_graph(db, batch_id)


@router.get("/vote-swing/{game_id}")
async def get_vote_swing(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Vote swing per message for a specific game."""
    return await vote_swing_per_message(db, game_id)
