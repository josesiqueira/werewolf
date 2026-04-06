"""Export API endpoints.

Task 13 — NDJSON export endpoint.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.engine.export import export_batch_ndjson, export_game_ndjson
from app.models.game import Game

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/{format}")
async def export_data(
    format: str,
    game_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Export game data.

    Currently supports ``ndjson`` format.
    If ``game_id`` is provided, export that single game.
    Otherwise, export all completed games.
    """
    if format != "ndjson":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format: {format}. Supported: ndjson",
        )

    if game_id is not None:
        # Verify game exists
        result = await db.execute(
            select(Game).where(Game.id == game_id)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Game not found")

        ndjson = await export_game_ndjson(db, game_id)
    else:
        # Export all completed games
        result = await db.execute(
            select(Game.id).where(Game.status == "completed")
        )
        game_ids = [row[0] for row in result.all()]
        if not game_ids:
            return PlainTextResponse("", media_type="application/x-ndjson")

        ndjson = await export_batch_ndjson(db, game_ids)

    return PlainTextResponse(
        content=ndjson,
        media_type="application/x-ndjson",
    )
