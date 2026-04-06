from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TurnResponse(BaseModel):
    """Response schema for a single turn."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    player_id: uuid.UUID
    round_number: int
    phase: str
    prompt_sent: str | None = None
    completion_received: str | None = None
    private_reasoning: str | None = None
    public_statement: str | None = None
    vote_target: uuid.UUID | None = None
    bid_level: int | None = None
    technique_self_label: str | None = None
    deception_self_label: str | None = None
    confidence: int | None = None
    is_default_response: bool
    token_count_input: int | None = None
    token_count_output: int | None = None
    latency_ms: int | None = None
    created_at: datetime
