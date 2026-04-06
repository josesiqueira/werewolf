from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    persona: Mapped[str | None] = mapped_column(Text, nullable=True)
    persuasion_profile: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_mayor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    eliminated_round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    survived: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    character_image: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    game: Mapped[Game] = relationship("Game", back_populates="players")
    turns: Mapped[list[Turn]] = relationship(
        "Turn", back_populates="player", cascade="all, delete-orphan"
    )
