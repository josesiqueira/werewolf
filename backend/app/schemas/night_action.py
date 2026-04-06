from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NightActionResponse(BaseModel):
    """Response schema for a night action record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    round_number: int
    wolf_target: uuid.UUID | None = None
    doctor_target: uuid.UUID | None = None
    seer_target: uuid.UUID | None = None
    seer_result: str | None = None
    kill_successful: bool
    created_at: datetime
