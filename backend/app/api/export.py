"""Export API endpoints.

Task 13 — NDJSON and CSV export endpoints.
Updated in Phase 5 Task 4 to support CSV format and filtering by
batch, profile, and role.
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.engine.export import export_batch_ndjson, export_game_ndjson
from app.models.batch import Batch
from app.models.game import Game
from app.models.player import Player
from app.models.turn import Turn

router = APIRouter(prefix="/api/export", tags=["export"])


# ---------------------------------------------------------------------------
# CSV export helper
# ---------------------------------------------------------------------------

_CSV_COLUMNS = [
    "game_id",
    "player_id",
    "agent_name",
    "role",
    "persuasion_profile",
    "survived",
    "eliminated_round",
    "is_mayor",
    "round_number",
    "phase",
    "private_reasoning",
    "public_statement",
    "vote_target",
    "bid_level",
    "technique_self_label",
    "deception_self_label",
    "confidence",
    "is_default_response",
    "token_count_input",
    "token_count_output",
    "latency_ms",
    "created_at",
]


async def _export_csv(
    db: AsyncSession,
    game_ids: list[uuid.UUID],
    profile: str | None = None,
    role: str | None = None,
) -> str:
    """Export game-player-turn data as CSV.

    One row per turn. Enriched with player metadata.
    """
    if not game_ids:
        return ""

    # Load players
    player_stmt = select(Player).where(Player.game_id.in_(game_ids))
    if profile is not None:
        player_stmt = player_stmt.where(Player.persuasion_profile == profile)
    if role is not None:
        player_stmt = player_stmt.where(Player.role == role)

    result = await db.execute(player_stmt)
    players = result.scalars().all()
    player_map: dict[str, Player] = {str(p.id): p for p in players}
    player_ids = list(player_map.keys())

    if not player_ids:
        return ""

    # Convert to UUID objects for the IN clause
    player_uuids = [uuid.UUID(pid) for pid in player_ids]

    # Load turns for these players
    result = await db.execute(
        select(Turn)
        .where(Turn.game_id.in_(game_ids))
        .where(Turn.player_id.in_(player_uuids))
        .order_by(Turn.game_id, Turn.round_number, Turn.created_at)
    )
    turns = result.scalars().all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_CSV_COLUMNS)
    writer.writeheader()

    for t in turns:
        p = player_map.get(str(t.player_id))
        row = {
            "game_id": str(t.game_id),
            "player_id": str(t.player_id),
            "agent_name": p.agent_name if p else None,
            "role": p.role if p else None,
            "persuasion_profile": p.persuasion_profile if p else None,
            "survived": p.survived if p else None,
            "eliminated_round": p.eliminated_round if p else None,
            "is_mayor": p.is_mayor if p else None,
            "round_number": t.round_number,
            "phase": t.phase,
            "private_reasoning": t.private_reasoning,
            "public_statement": t.public_statement,
            "vote_target": str(t.vote_target) if t.vote_target else None,
            "bid_level": t.bid_level,
            "technique_self_label": t.technique_self_label,
            "deception_self_label": t.deception_self_label,
            "confidence": t.confidence,
            "is_default_response": t.is_default_response,
            "token_count_input": t.token_count_input,
            "token_count_output": t.token_count_output,
            "latency_ms": t.latency_ms,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        writer.writerow(row)

    return output.getvalue()


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/{format}")
async def export_data(
    format: str,
    game_id: uuid.UUID | None = Query(None),
    batch_id: uuid.UUID | None = Query(None),
    profile: str | None = Query(None, description="Filter by persuasion profile"),
    role: str | None = Query(None, description="Filter by role"),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Export game data.

    Supported formats: ``ndjson``, ``csv``.

    - If ``game_id`` is provided, export that single game.
    - If ``batch_id`` is provided, export all completed games in that batch.
    - Otherwise, export all completed games.

    Optional filters: ``profile``, ``role`` (CSV only applies these as
    row filters; NDJSON exports all turns for selected games).
    """
    if format not in ("ndjson", "csv"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format: {format}. Supported: ndjson, csv",
        )

    # Resolve game IDs
    if game_id is not None:
        result = await db.execute(select(Game).where(Game.id == game_id))
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Game not found")
        resolved_game_ids = [game_id]

    elif batch_id is not None:
        result = await db.execute(select(Batch).where(Batch.id == batch_id))
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Batch not found")

        result = await db.execute(
            select(Game.id)
            .where(Game.batch_id == batch_id)
            .where(Game.status == "completed")
        )
        resolved_game_ids = [row[0] for row in result.all()]
    else:
        result = await db.execute(
            select(Game.id).where(Game.status == "completed")
        )
        resolved_game_ids = [row[0] for row in result.all()]

    if not resolved_game_ids:
        if format == "csv":
            return PlainTextResponse("", media_type="text/csv")
        return PlainTextResponse("", media_type="application/x-ndjson")

    # NDJSON export
    if format == "ndjson":
        if game_id is not None:
            ndjson = await export_game_ndjson(db, game_id)
        else:
            ndjson = await export_batch_ndjson(db, resolved_game_ids)

        return PlainTextResponse(
            content=ndjson,
            media_type="application/x-ndjson",
        )

    # CSV export
    csv_content = await _export_csv(db, resolved_game_ids, profile=profile, role=role)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=werewolf_export.csv"},
    )
