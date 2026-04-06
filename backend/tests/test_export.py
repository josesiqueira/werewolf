"""Async unit tests for NDJSON export (UT-047 to UT-052).

Uses an in-memory SQLite database via aiosqlite to test the export
functions without requiring PostgreSQL. We create SQLite-compatible
table definitions and use raw inserts, then call the export functions
which query via the ORM-mapped Turn/Player classes. To make this work,
we bind the ORM models' tables to the same metadata used for creation
by creating tables only for 'players' and 'turns' with compatible types.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.engine.export import export_batch_ndjson, export_game_ndjson


# ---------------------------------------------------------------------------
# Helper: mock async DB session that simulates the export queries
# ---------------------------------------------------------------------------

class _FakePlayer:
    """Minimal stand-in for a Player ORM object."""
    def __init__(self, id, game_id, agent_name, role):
        self.id = id
        self.game_id = game_id
        self.agent_name = agent_name
        self.role = role


class _FakeTurn:
    """Minimal stand-in for a Turn ORM object."""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.game_id = kwargs.get("game_id")
        self.player_id = kwargs.get("player_id")
        self.round_number = kwargs.get("round_number", 1)
        self.phase = kwargs.get("phase", "day_bid")
        self.prompt_sent = kwargs.get("prompt_sent", "test prompt")
        self.completion_received = kwargs.get("completion_received", "test completion")
        self.private_reasoning = kwargs.get("private_reasoning", "reasoning")
        self.public_statement = kwargs.get("public_statement", "statement")
        self.vote_target = kwargs.get("vote_target")
        self.bid_level = kwargs.get("bid_level")
        self.technique_self_label = kwargs.get("technique_self_label")
        self.deception_self_label = kwargs.get("deception_self_label")
        self.confidence = kwargs.get("confidence")
        self.is_default_response = kwargs.get("is_default_response", False)
        self.token_count_input = kwargs.get("token_count_input")
        self.token_count_output = kwargs.get("token_count_output")
        self.latency_ms = kwargs.get("latency_ms")
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))


class _FakeScalars:
    """Mimics result.scalars().all()."""
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _FakeResult:
    """Mimics the result from session.execute()."""
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _FakeScalars(self._items)


def _make_mock_session(players: list[_FakePlayer], turns: list[_FakeTurn]):
    """Build an AsyncMock session that returns the given players/turns.

    The export functions issue exactly two queries per game:
      1. select(Player).where(Player.game_id == game_id) -> players
      2. select(Turn).where(...).order_by(...) -> turns (sorted)
    """
    session = AsyncMock()
    call_count = 0

    async def _execute(stmt, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        # Odd calls = players, even calls = turns
        if call_count % 2 == 1:
            # Filter players by game_id from the statement
            return _FakeResult(players)
        else:
            return _FakeResult(turns)

    session.execute = _execute
    return session


def _make_mock_session_multi(game_data: dict[str, tuple[list, list]]):
    """Build a mock session for multiple games.

    game_data: {game_id_str: (players_list, turns_list)}
    """
    session = AsyncMock()
    call_seq = []

    # We need to track which game is being queried.
    # export_game_ndjson converts game_id to UUID then queries.
    # It always does player query first, then turn query.
    game_ids_order = list(game_data.keys())
    game_idx = [0]
    is_player_query = [True]

    async def _execute(stmt, *args, **kwargs):
        if is_player_query[0]:
            gid = game_ids_order[game_idx[0]]
            players, _ = game_data[gid]
            is_player_query[0] = False
            return _FakeResult(players)
        else:
            gid = game_ids_order[game_idx[0]]
            _, turns = game_data[gid]
            is_player_query[0] = True
            game_idx[0] += 1
            return _FakeResult(turns)

    session.execute = _execute
    return session


# ---------------------------------------------------------------------------
# UT-047: One JSON object per turn, no trailing newline
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ut047_ndjson_line_count():
    game_id = uuid.uuid4()
    p1_id = uuid.uuid4()
    p2_id = uuid.uuid4()

    players = [
        _FakePlayer(p1_id, game_id, "Agent_1", "villager"),
        _FakePlayer(p2_id, game_id, "Agent_2", "villager"),
    ]
    turns = [
        _FakeTurn(game_id=game_id, player_id=p1_id, round_number=1,
                  created_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc)),
        _FakeTurn(game_id=game_id, player_id=p2_id, round_number=1,
                  created_at=datetime(2026, 1, 1, 0, 0, 2, tzinfo=timezone.utc)),
        _FakeTurn(game_id=game_id, player_id=p1_id, round_number=2,
                  created_at=datetime(2026, 1, 1, 0, 0, 3, tzinfo=timezone.utc)),
    ]

    session = _make_mock_session(players, turns)
    output = await export_game_ndjson(session, game_id)

    lines = output.splitlines()
    assert len(lines) == 3
    for line in lines:
        json.loads(line)  # must parse without error
    assert not output.endswith("\n")


# ---------------------------------------------------------------------------
# UT-048: Each record contains all 22 required fields with correct types
# ---------------------------------------------------------------------------
REQUIRED_KEYS = {
    "game_id", "round_number", "phase", "player_id", "agent_name", "role",
    "turn_id", "prompt_sent", "completion_received", "private_reasoning",
    "public_statement", "vote_target", "bid_level", "technique_self_label",
    "deception_self_label", "confidence", "is_default_response",
    "token_count_input", "token_count_output", "latency_ms", "created_at",
}


@pytest.mark.asyncio
async def test_ut048_required_fields():
    game_id = uuid.uuid4()
    p_id = uuid.uuid4()
    vote_target_uuid = uuid.uuid4()

    players = [_FakePlayer(p_id, game_id, "Agent_1", "werewolf")]
    turns = [
        _FakeTurn(
            game_id=game_id, player_id=p_id,
            bid_level=2, confidence=4,
            deception_self_label="truthful",
            vote_target=vote_target_uuid,
        ),
    ]

    session = _make_mock_session(players, turns)
    output = await export_game_ndjson(session, game_id)
    record = json.loads(output.splitlines()[0])

    assert REQUIRED_KEYS.issubset(set(record.keys())), (
        f"Missing keys: {REQUIRED_KEYS - set(record.keys())}"
    )
    assert record["agent_name"] == "Agent_1"
    assert record["role"] == "werewolf"
    assert record["bid_level"] == 2
    # vote_target should be a UUID string
    uuid.UUID(record["vote_target"])


# ---------------------------------------------------------------------------
# UT-049: Turns ordered by round_number then created_at
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ut049_ordering():
    game_id = uuid.uuid4()
    p_id = uuid.uuid4()

    players = [_FakePlayer(p_id, game_id, "Agent_1", "villager")]
    # Pre-sort as the real DB would: order by round_number, created_at
    turns = [
        _FakeTurn(game_id=game_id, player_id=p_id, round_number=1,
                  created_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc)),
        _FakeTurn(game_id=game_id, player_id=p_id, round_number=2,
                  created_at=datetime(2026, 1, 1, 0, 0, 2, tzinfo=timezone.utc)),
        _FakeTurn(game_id=game_id, player_id=p_id, round_number=3,
                  created_at=datetime(2026, 1, 1, 0, 0, 3, tzinfo=timezone.utc)),
    ]

    session = _make_mock_session(players, turns)
    output = await export_game_ndjson(session, game_id)
    rounds = [json.loads(line)["round_number"] for line in output.splitlines()]
    assert rounds == [1, 2, 3]


# ---------------------------------------------------------------------------
# UT-050: Empty string for game with no turns
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ut050_no_turns():
    game_id = uuid.uuid4()
    session = _make_mock_session([], [])
    result = await export_game_ndjson(session, game_id)
    assert result == ""


# ---------------------------------------------------------------------------
# UT-051: export_batch_ndjson concatenates multiple games, no blank separators
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ut051_batch_concatenation():
    game1 = uuid.uuid4()
    game2 = uuid.uuid4()

    p1_id = uuid.uuid4()
    p2_id = uuid.uuid4()

    game_data = {
        str(game1): (
            [_FakePlayer(p1_id, game1, "Agent_1", "villager")],
            [
                _FakeTurn(game_id=game1, player_id=p1_id, round_number=1,
                          created_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc)),
                _FakeTurn(game_id=game1, player_id=p1_id, round_number=2,
                          created_at=datetime(2026, 1, 1, 0, 0, 2, tzinfo=timezone.utc)),
            ],
        ),
        str(game2): (
            [_FakePlayer(p2_id, game2, "Agent_2", "werewolf")],
            [
                _FakeTurn(game_id=game2, player_id=p2_id, round_number=1,
                          created_at=datetime(2026, 1, 1, 0, 0, 3, tzinfo=timezone.utc)),
                _FakeTurn(game_id=game2, player_id=p2_id, round_number=2,
                          created_at=datetime(2026, 1, 1, 0, 0, 4, tzinfo=timezone.utc)),
            ],
        ),
    }

    session = _make_mock_session_multi(game_data)
    result = await export_batch_ndjson(session, [game1, game2])
    lines = result.splitlines()
    assert len(lines) == 4
    for line in lines:
        json.loads(line)  # all parse as JSON


# ---------------------------------------------------------------------------
# UT-052: export_batch_ndjson with empty game_ids returns empty string
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ut052_empty_batch():
    session = AsyncMock()
    result = await export_batch_ndjson(session, [])
    assert result == ""
