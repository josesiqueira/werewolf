from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VoteResponse(BaseModel):
    """Response schema for a vote record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    round_number: int
    voter: uuid.UUID
    target: uuid.UUID
    is_mayor_tiebreak: bool
    created_at: datetime
