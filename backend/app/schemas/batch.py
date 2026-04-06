"""Pydantic schemas for Batch API requests and responses.

Task 3 — BatchCreate for starting a batch, BatchResponse for status.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BatchCreate(BaseModel):
    """Request schema for creating a new batch run."""

    num_games: int = Field(..., ge=1, le=1000, description="Number of games to run")
    max_parallelism: int = Field(
        default=1, ge=1, le=20, description="Max concurrent games"
    )
    debate_cap: int = Field(
        default=10, ge=1, le=20, description="Max debate turns per day phase"
    )
    use_llm: bool = Field(
        default=False, description="Use LLM agents (True) or MockAgent (False)"
    )


class BatchResponse(BaseModel):
    """Response schema for batch status and progress."""

    model_config = {"from_attributes": True}

    id: UUID
    created_at: datetime
    total_games: int
    completed_games: int
    failed_games: int
    status: str
    config: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
