from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.player import PlayerResponse


class GameCreate(BaseModel):
    """Request body for creating a new game."""

    config: dict | None = Field(default=None, description="Optional game configuration")


class GameResponse(BaseModel):
    """Response for a single game (list view)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    status: str
    winner: str | None = None
    rounds_played: int
    total_turns: int
    is_degraded: bool
    config: dict | None = None


class GameStateResponse(BaseModel):
    """Full game state including players (detail view)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    status: str
    winner: str | None = None
    rounds_played: int
    total_turns: int
    is_degraded: bool
    config: dict | None = None
    players: list[PlayerResponse] = []
