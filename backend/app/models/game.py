from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    winner: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rounds_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_turns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_degraded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    batch: Mapped["Batch | None"] = relationship(
        "Batch", back_populates="games"
    )
    players: Mapped[list[Player]] = relationship(
        "Player", back_populates="game", cascade="all, delete-orphan"
    )
    turns: Mapped[list[Turn]] = relationship(
        "Turn", back_populates="game", cascade="all, delete-orphan"
    )
    night_actions: Mapped[list[NightAction]] = relationship(
        "NightAction", back_populates="game", cascade="all, delete-orphan"
    )
    votes: Mapped[list[Vote]] = relationship(
        "Vote", back_populates="game", cascade="all, delete-orphan"
    )
    events: Mapped[list[GameEvent]] = relationship(
        "GameEvent", back_populates="game", cascade="all, delete-orphan"
    )
