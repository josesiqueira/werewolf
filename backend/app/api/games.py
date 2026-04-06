"""Core API endpoints for games.

Task 13 — CRUD + game execution endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.engine.agent_interface import MockAgent
from app.engine.game_loop import run_game
from app.models.game import Game
from app.models.game_event import GameEvent
from app.models.player import Player
from app.models.turn import Turn
from app.schemas.game import GameCreate, GameResponse, GameStateResponse
from app.schemas.turn import TurnResponse

router = APIRouter(prefix="/api/games", tags=["games"])


# ---------------------------------------------------------------------------
# POST /api/games — create and run a single game with mock agents
# ---------------------------------------------------------------------------

@router.post("", response_model=GameStateResponse, status_code=201)
async def create_game(
    body: GameCreate | None = None,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Create and immediately run a game using MockAgents."""
    config: dict[str, Any] = {}
    if body is not None:
        config = body.config if hasattr(body, "config") and body.config else {}

    player_count = config.get("player_count", 7)

    # Build mock agents
    agents: list[MockAgent] = []
    for i in range(player_count):
        pid = str(uuid.uuid4())
        agents.append(
            MockAgent(
                player_id=pid,
                agent_name=f"Agent_{i + 1}",
                role="",  # assigned by game loop
            )
        )

    game = await run_game(db, agents, config)
    await db.flush()

    # Reload with players for response
    result = await db.execute(
        select(Game).where(Game.id == game.id)
    )
    game = result.scalar_one()

    player_result = await db.execute(
        select(Player).where(Player.game_id == game.id)
    )
    players = player_result.scalars().all()

    return _game_to_response(game, players)


# ---------------------------------------------------------------------------
# GET /api/games — list games with filters
# ---------------------------------------------------------------------------

@router.get("", response_model=list[GameStateResponse])
async def list_games(
    status: str | None = Query(None),
    winner: str | None = Query(None),
    is_degraded: bool | None = Query(None),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """List games, optionally filtered by status, winner, or degraded flag."""
    stmt = select(Game).order_by(Game.created_at.desc())
    if status is not None:
        stmt = stmt.where(Game.status == status)
    if winner is not None:
        stmt = stmt.where(Game.winner == winner)
    if is_degraded is not None:
        stmt = stmt.where(Game.is_degraded == is_degraded)

    result = await db.execute(stmt)
    games = result.scalars().all()

    responses = []
    for g in games:
        player_result = await db.execute(
            select(Player).where(Player.game_id == g.id)
        )
        players = player_result.scalars().all()
        responses.append(_game_to_response(g, players))
    return responses


# ---------------------------------------------------------------------------
# GET /api/games/{game_id} — full game state with players
# ---------------------------------------------------------------------------

@router.get("/{game_id}", response_model=GameStateResponse)
async def get_game(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Get full game state including nested player data."""
    result = await db.execute(
        select(Game).where(Game.id == game_id)
    )
    game = result.scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    player_result = await db.execute(
        select(Player).where(Player.game_id == game.id)
    )
    players = player_result.scalars().all()
    return _game_to_response(game, players)


# ---------------------------------------------------------------------------
# GET /api/games/{game_id}/turns — all turns for a game
# ---------------------------------------------------------------------------

@router.get("/{game_id}/turns", response_model=list[TurnResponse])
async def get_game_turns(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Return all turns for a game in chronological order."""
    # Verify game exists
    game_result = await db.execute(
        select(Game).where(Game.id == game_id)
    )
    if game_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Game not found")

    result = await db.execute(
        select(Turn)
        .where(Turn.game_id == game_id)
        .order_by(Turn.round_number, Turn.created_at)
    )
    turns = result.scalars().all()
    return [_turn_to_response(t) for t in turns]


# ---------------------------------------------------------------------------
# GET /api/games/{game_id}/replay — replay data
# ---------------------------------------------------------------------------

@router.get("/{game_id}/replay")
async def get_game_replay(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Return replay data: game info, players, turns, and events in order."""
    # Game
    game_result = await db.execute(
        select(Game).where(Game.id == game_id)
    )
    game = game_result.scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    # Players
    player_result = await db.execute(
        select(Player).where(Player.game_id == game_id)
    )
    players = player_result.scalars().all()

    # Turns
    turn_result = await db.execute(
        select(Turn)
        .where(Turn.game_id == game_id)
        .order_by(Turn.round_number, Turn.created_at)
    )
    turns = turn_result.scalars().all()

    # Events
    event_result = await db.execute(
        select(GameEvent)
        .where(GameEvent.game_id == game_id)
        .order_by(GameEvent.round_number, GameEvent.created_at)
    )
    events = event_result.scalars().all()

    return {
        "game": _game_to_response(game, players),
        "players": [
            {
                "id": str(p.id),
                "game_id": str(p.game_id),
                "agent_name": p.agent_name,
                "role": p.role,
                "persona": p.persona,
                "persuasion_profile": p.persuasion_profile,
                "is_mayor": p.is_mayor,
                "eliminated_round": p.eliminated_round,
                "survived": p.survived,
                "character_image": p.character_image,
            }
            for p in players
        ],
        "turns": [_turn_to_response(t) for t in turns],
        "events": [
            {
                "id": str(e.id),
                "round_number": e.round_number,
                "event_type": e.event_type,
                "details": e.details,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _game_to_response(game: Game, players: list[Player]) -> dict[str, Any]:
    return {
        "id": str(game.id),
        "created_at": game.created_at.isoformat() if game.created_at else None,
        "status": game.status,
        "winner": game.winner,
        "rounds_played": game.rounds_played,
        "total_turns": game.total_turns,
        "is_degraded": game.is_degraded,
        "config": game.config,
        "players": [
            {
                "id": str(p.id),
                "game_id": str(p.game_id),
                "agent_name": p.agent_name,
                "role": p.role,
                "persona": p.persona,
                "persuasion_profile": p.persuasion_profile,
                "is_mayor": p.is_mayor,
                "eliminated_round": p.eliminated_round,
                "survived": p.survived,
                "character_image": p.character_image,
            }
            for p in players
        ],
    }


def _turn_to_response(t: Turn) -> dict[str, Any]:
    return {
        "id": str(t.id),
        "game_id": str(t.game_id),
        "player_id": str(t.player_id),
        "round_number": t.round_number,
        "phase": t.phase,
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
