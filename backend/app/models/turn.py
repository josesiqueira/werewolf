from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[str] = mapped_column(String(30), nullable=False)
    prompt_sent: Mapped[str | None] = mapped_column(Text, nullable=True)
    completion_received: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    vote_target: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True,
    )
    bid_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    technique_self_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    deception_self_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default_response: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    token_count_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    game: Mapped[Game] = relationship("Game", back_populates="turns")
    player: Mapped[Player] = relationship("Player", back_populates="turns")
    vote_target_player: Mapped[Player | None] = relationship(
        "Player", foreign_keys=[vote_target]
    )
