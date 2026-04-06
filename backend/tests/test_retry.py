"""Tests UT-116 to UT-120 — Retry and fallback (agent/retry.py)."""

import uuid

import pytest
from unittest.mock import AsyncMock

from app.agent.retry import build_default_response, call_with_retry_and_fallback

P = [str(uuid.uuid4()) for _ in range(7)]


# UT-116
class TestUT116SuccessFirstAttempt:
    """Successful LLM call on first attempt returns result with is_default == False."""

    @pytest.mark.asyncio
    async def test_immediate_success(self):
        mock_result = object()
        coro = AsyncMock(return_value=mock_result)
        result, is_default = await call_with_retry_and_fallback(
            coro, alive_players=P, player_id=P[0],
        )
        assert result is mock_result
        assert is_default is False
        assert coro.call_count == 1


# UT-117
class TestUT117TransientFailureThenSuccess:
    """Transient failure followed by success returns real result on retry."""

    @pytest.mark.asyncio
    async def test_retry_then_success(self):
        mock_result = object()
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("timeout")
            return mock_result

        result, is_default = await call_with_retry_and_fallback(
            flaky, alive_players=P, player_id=P[0],
        )
        assert result is mock_result
        assert is_default is False
        assert call_count == 2


# UT-118
class TestUT118AllAttemptsFail:
    """All attempts fail — fallback AgentResponse returned with is_default == True."""

    @pytest.mark.asyncio
    async def test_exhausted_retries(self):
        async def always_fails():
            raise RuntimeError("LLM down")

        result, is_default = await call_with_retry_and_fallback(
            always_fails, alive_players=P, player_id=P[0],
        )
        assert is_default is True
        assert result.private_reasoning == "[DEFAULT] All LLM retries exhausted."
        assert result.public_statement == "I need more time to think about this."
        assert result.bid_level == 1
        assert result.vote_target in P[1:]


# UT-119
class TestUT119DefaultResponseExcludesSelf:
    """build_default_response vote_target excludes the requesting player."""

    def test_excludes_self(self):
        response = build_default_response(alive_players=P, player_id=P[0])
        assert response.vote_target != P[0]
        assert response.vote_target in P[1:]


# UT-120
class TestUT120DefaultResponseNoOtherPlayers:
    """build_default_response with only self alive sets vote_target to None."""

    def test_solo_player(self):
        response = build_default_response(alive_players=[P[0]], player_id=P[0])
        assert response.vote_target is None
