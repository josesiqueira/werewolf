from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class PlayerResponse(BaseModel):
    """Response schema for a player."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    agent_name: str
    role: str
    persona: str | None = None
    persuasion_profile: str | None = None
    is_mayor: bool
    eliminated_round: int | None = None
    survived: bool
    character_image: str | None = None
