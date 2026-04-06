"""OpenAI API client wrapper for GPT 5.4.

Task 1 — Async wrapper with timeout, token tracking, and latency measurement.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import settings


@dataclass
class LLMResponse:
    """Raw completion result with usage metrics."""

    text: str
    token_count_input: int
    token_count_output: int
    latency_ms: float


class LLMClient:
    """Async wrapper around the OpenAI chat completions API.

    Parameters
    ----------
    model : str
        Model identifier (default from settings, e.g. ``gpt-4o``).
    timeout : float
        Request timeout in seconds (default 60).
    temperature : float
        Sampling temperature (default 0.7).
    """

    def __init__(
        self,
        model: str | None = None,
        timeout: float = 60.0,
        temperature: float = 0.7,
    ) -> None:
        self._model = model or settings.OPENAI_MODEL
        self._timeout = timeout
        self._temperature = temperature
        self._client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=self._timeout,
        )

    async def complete(
        self,
        system_message: str,
        user_message: str,
    ) -> LLMResponse:
        """Send a chat completion request and return an ``LLMResponse``.

        Parameters
        ----------
        system_message : str
            The cached system prompt (game rules, role, persona, format).
        user_message : str
            The per-turn dynamic prompt (game state, history, instruction).

        Returns
        -------
        LLMResponse
            Contains the raw text, token counts, and latency.
        """
        start = time.perf_counter()

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=self._temperature,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            text=choice.message.content or "",
            token_count_input=usage.prompt_tokens if usage else 0,
            token_count_output=usage.completion_tokens if usage else 0,
            latency_ms=round(elapsed_ms, 2),
        )
