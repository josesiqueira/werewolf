"""Retry and fallback logic for LLM agent calls.

Task 2 — 3 retries with exponential backoff (1s, 3s, 9s).
After all retries fail, return conservative defaults.
"""

from __future__ import annotations

import logging
import random
from typing import Any, Awaitable, Callable

from tenacity import (
    RetryCallState,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from app.engine.agent_interface import AgentResponse

logger = logging.getLogger(__name__)


def _log_retry(retry_state: RetryCallState) -> None:
    """Log each retry attempt."""
    attempt = retry_state.attempt_number
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "LLM call attempt %d failed: %s",
        attempt,
        exc,
    )


def build_default_response(
    alive_players: list[str],
    player_id: str,
) -> AgentResponse:
    """Return conservative fallback defaults when all retries are exhausted.

    Parameters
    ----------
    alive_players : list[str]
        Currently alive player IDs.
    player_id : str
        The requesting agent's own player ID (excluded from vote targets).

    Returns
    -------
    AgentResponse
        Safe defaults: bid=1, generic statement, random vote target,
        deception_self_label="truthful", confidence=3.
    """
    valid_targets = [pid for pid in alive_players if pid != player_id]
    vote_target = random.choice(valid_targets) if valid_targets else None

    return AgentResponse(
        private_reasoning="[DEFAULT] All LLM retries exhausted.",
        public_statement="I need more time to think about this.",
        vote_target=vote_target,
        bid_level=1,
        technique_self_label="none",
        deception_self_label="truthful",
        confidence=3,
    )


# Tenacity retry decorator: 3 attempts, exponential backoff 1s -> 3s -> 9s
retry_llm_call = retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=9, exp_base=3),
    before_sleep=_log_retry,
    reraise=True,
)


async def call_with_retry_and_fallback(
    llm_coroutine: Callable[[], Awaitable[Any]],
    alive_players: list[str],
    player_id: str,
) -> tuple[Any, bool]:
    """Execute an LLM call with retries and fallback on total failure.

    Parameters
    ----------
    llm_coroutine : Callable
        A zero-argument async callable that performs the LLM request.
    alive_players : list[str]
        Currently alive player IDs (for fallback vote target).
    player_id : str
        The requesting agent's own player ID.

    Returns
    -------
    tuple[Any, bool]
        ``(result, is_default)`` — the LLM result or a default
        ``AgentResponse``, and whether the default was used.
    """

    @retry_llm_call
    async def _attempt() -> Any:
        return await llm_coroutine()

    try:
        result = await _attempt()
        return result, False
    except Exception:
        logger.error(
            "All LLM retries exhausted for player %s. Using defaults.",
            player_id,
        )
        return build_default_response(alive_players, player_id), True
