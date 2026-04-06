"""Async unit tests for MockAgent (UT-043 to UT-046)."""

import pytest

from app.engine.agent_interface import AgentResponse, MockAgent
from tests.conftest import P


@pytest.fixture
def mock_agent() -> MockAgent:
    """MockAgent with P[0] as player_id."""
    return MockAgent(player_id=P[0], agent_name="TestAgent", role="villager")


# UT-043: MockAgent campaign always returns a non-empty public_statement
@pytest.mark.asyncio
async def test_ut043_campaign_non_empty(mock_agent):
    result = await mock_agent.campaign({"alive_players": [P[0], P[1], P[2]]})
    assert isinstance(result.public_statement, str)
    assert len(result.public_statement) > 0


# UT-044: MockAgent.vote_for_mayor never returns agent's own ID when others exist
@pytest.mark.asyncio
async def test_ut044_vote_for_mayor_excludes_self(mock_agent):
    for _ in range(50):
        result = await mock_agent.vote_for_mayor(
            {}, candidates=[P[0], P[1], P[2]]
        )
        assert result in [P[1], P[2]]
        assert result != P[0]


# UT-045: MockAgent.bid always returns a value in [0, 4]
@pytest.mark.asyncio
async def test_ut045_bid_range(mock_agent):
    for _ in range(50):
        result = await mock_agent.bid({}, [])
        assert 0 <= result <= 4


# UT-046: MockAgent.vote sets a non-None vote_target pointing to an alive opponent
@pytest.mark.asyncio
async def test_ut046_vote_target_valid(mock_agent):
    game_state = {"alive_players": [P[0], P[1], P[2]]}
    for _ in range(50):
        result = await mock_agent.vote(game_state, [])
        assert result.vote_target in [P[1], P[2]]
        assert result.vote_target is not None
        assert result.vote_target != P[0]
