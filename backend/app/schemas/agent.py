from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field


class DeceptionLabel(str, Enum):
    """Valid taxonomy for agent self-reported deception."""

    TRUTHFUL = "truthful"
    OMISSION = "omission"
    DISTORTION = "distortion"
    FABRICATION = "fabrication"
    MISDIRECTION = "misdirection"


class AgentResponse(BaseModel):
    """Structured JSON response expected from the LLM agent."""

    private_reasoning: str = Field(
        ..., description="Agent's private chain-of-thought (not shown to other agents)"
    )
    public_statement: str = Field(
        ..., description="What the agent says publicly during debate"
    )
    vote_target: uuid.UUID | None = Field(
        default=None, description="UUID of the player this agent votes to eliminate"
    )
    bid_level: int = Field(
        default=1, ge=0, le=4, description="Speaking urgency bid (0=pass, 4=critical)"
    )
    technique_self_label: str | None = Field(
        default=None,
        description="Which section of the assigned persuasion profile the agent used",
    )
    deception_self_label: DeceptionLabel = Field(
        default=DeceptionLabel.TRUTHFUL,
        description="Agent's self-assessment of deception level",
    )
    confidence: int = Field(
        default=3, ge=1, le=5, description="Agent's confidence in their action (1-5)"
    )
