"""NDJSON export for game turn data.

Task 12 — Each line is a JSON object with game_id, round_number, phase,
player_id, agent_name, role, and all turn fields.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player
from app.models.turn import Turn


async def export_game_ndjson(
    db_session: AsyncSession,
    game_id: uuid.UUID | str,
) -> str:
    """Export all turns for a single game as an NDJSON string.

    Each line is a JSON object containing the turn data enriched with
    player-level metadata (agent_name, role).
    """
    game_id = uuid.UUID(str(game_id))

    # Load players for this game keyed by id
    player_result = await db_session.execute(
        select(Player).where(Player.game_id == game_id)
    )
    players = {str(p.id): p for p in player_result.scalars().all()}

    # Load turns ordered by round then created_at
    turn_result = await db_session.execute(
        select(Turn)
        .where(Turn.game_id == game_id)
        .order_by(Turn.round_number, Turn.created_at)
    )
    turns = turn_result.scalars().all()

    lines: list[str] = []
    for t in turns:
        player = players.get(str(t.player_id))
        record: dict[str, Any] = {
            "game_id": str(t.game_id),
            "round_number": t.round_number,
            "phase": t.phase,
            "player_id": str(t.player_id),
            "agent_name": player.agent_name if player else None,
            "role": player.role if player else None,
            "turn_id": str(t.id),
            "prompt_sent": t.prompt_sent,
            "completion_received": t.completion_received,
            "private_reasoning": t.private_reasoning,
            "public_statement": t.public_statement,
            "vote_target": str(t.vote_target) if t.vote_target else None,
            "bid_level": t.bid_level,
            "technique_self_label": t.technique_self_label,
            "deception_self_label": t.deception_self_label,
            "confidence": t.confidence,
            "is_default_response": t.is_default_response,
            "token_count_input": t.token_count_input,
            "token_count_output": t.token_count_output,
            "latency_ms": t.latency_ms,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        lines.append(json.dumps(record, ensure_ascii=False))

    return "\n".join(lines)


async def export_batch_ndjson(
    db_session: AsyncSession,
    game_ids: list[uuid.UUID | str],
) -> str:
    """Export turns for multiple games as a single NDJSON string."""
    parts: list[str] = []
    for gid in game_ids:
        chunk = await export_game_ndjson(db_session, gid)
        if chunk:
            parts.append(chunk)
    return "\n".join(parts)
