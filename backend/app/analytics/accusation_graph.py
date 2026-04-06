"""Accusation graph builder.

Phase 5, Task 3 — Parse public_statements to extract accusation
relationships. Aggregate by profile. Output nodes and weighted edges
for D3 force-directed graph.
"""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.player import Player
from app.models.turn import Turn


_PROFILES = [
    "ethos",
    "pathos",
    "logos",
    "authority_socialproof",
    "reciprocity_liking",
    "scarcity_commitment",
    "baseline",
]

# Profile display colors for D3 visualization
_PROFILE_COLORS = {
    "ethos": "#3B82F6",
    "pathos": "#EF4444",
    "logos": "#10B981",
    "authority_socialproof": "#F59E0B",
    "reciprocity_liking": "#A855F7",
    "scarcity_commitment": "#F97316",
    "baseline": "#6B7280",
}

_ACCUSATION_PATTERNS = re.compile(
    r"\b(?:suspect|suspicious|accuse|accused|accusing|lying|liar|"
    r"wolf|werewolf|eliminate|guilty|blame|untrustworthy|dishonest|"
    r"deceiving|shady|hide|hiding|voted\s+against|don\'t\s+trust|"
    r"cannot\s+trust|can\'t\s+trust|not\s+trustworthy)\b",
    re.IGNORECASE,
)


async def build_accusation_graph(
    db: AsyncSession, batch_id: uuid.UUID | None = None
) -> dict[str, Any]:
    """Build accusation graph aggregated by profile.

    Parses all public_statements to find accusation relationships
    (who accused whom), then aggregates by persuasion profile.

    Returns:
        {
            "nodes": [
                {"id": "ethos", "color": "#3B82F6", "total_accusations_made": int,
                 "total_accusations_received": int},
                ...
            ],
            "edges": [
                {"source": "ethos", "target": "logos", "weight": int},
                ...
            ]
        }
    """
    # Get completed game IDs
    stmt = select(Game.id).where(Game.status == "completed")
    if batch_id is not None:
        stmt = stmt.where(Game.batch_id == batch_id)
    result = await db.execute(stmt)
    game_ids = [row[0] for row in result.all()]

    if not game_ids:
        return {"nodes": [], "edges": []}

    # Load all players
    result = await db.execute(
        select(Player).where(Player.game_id.in_(game_ids))
    )
    all_players = result.scalars().all()

    # game_id -> {player_id -> Player}
    players_by_game: dict[uuid.UUID, dict[str, Player]] = defaultdict(dict)
    for p in all_players:
        players_by_game[p.game_id][str(p.id)] = p

    # Load all public statements
    result = await db.execute(
        select(Turn)
        .where(Turn.game_id.in_(game_ids))
        .where(Turn.public_statement.isnot(None))
    )
    turns = result.scalars().all()

    # Count accusations: (accuser_profile, accused_profile) -> count
    edge_counts: dict[tuple[str, str], int] = defaultdict(int)
    accusations_made: dict[str, int] = defaultdict(int)
    accusations_received: dict[str, int] = defaultdict(int)

    for t in turns:
        text = t.public_statement or ""
        if not _ACCUSATION_PATTERNS.search(text):
            continue

        speaker_id = str(t.player_id)
        game_players = players_by_game.get(t.game_id, {})
        speaker = game_players.get(speaker_id)
        if speaker is None:
            continue

        speaker_profile = speaker.persuasion_profile or "baseline"
        if speaker_profile not in _PROFILES:
            speaker_profile = "baseline"

        text_lower = text.lower()
        for pid, p in game_players.items():
            if pid == speaker_id:
                continue
            if not p.agent_name:
                continue
            if p.agent_name.lower() not in text_lower:
                continue

            target_profile = p.persuasion_profile or "baseline"
            if target_profile not in _PROFILES:
                target_profile = "baseline"

            edge_counts[(speaker_profile, target_profile)] += 1
            accusations_made[speaker_profile] += 1
            accusations_received[target_profile] += 1

    # Build nodes
    nodes = []
    for profile in _PROFILES:
        nodes.append({
            "id": profile,
            "color": _PROFILE_COLORS.get(profile, "#6B7280"),
            "total_accusations_made": accusations_made.get(profile, 0),
            "total_accusations_received": accusations_received.get(profile, 0),
        })

    # Build edges (only include non-zero)
    edges = []
    for (source, target), weight in sorted(edge_counts.items()):
        if weight > 0:
            edges.append({
                "source": source,
                "target": target,
                "weight": weight,
            })

    return {"nodes": nodes, "edges": edges}
