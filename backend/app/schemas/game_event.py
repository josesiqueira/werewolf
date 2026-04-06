from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class GameEventResponse(BaseModel):
    """Response schema for a game event."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    round_number: int
    event_type: str
    details: dict[str, Any] | None = None
    created_at: datetime
