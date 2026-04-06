"""Add batches table and batch_id FK on games

Revision ID: 002_add_batches
Revises: 001_initial
Create Date: 2026-04-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_add_batches"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- batches ---
    op.create_table(
        "batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("total_games", sa.Integer(), nullable=False),
        sa.Column(
            "completed_games", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "failed_games", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- add batch_id FK to games ---
    op.add_column(
        "games",
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("batches.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("games", "batch_id")
    op.drop_table("batches")
