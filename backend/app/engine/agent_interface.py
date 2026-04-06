"""Stub agent interface and mock agent for testing the game loop.

Task 11 — AgentInterface ABC and MockAgent that returns random valid actions.
"""

from __future__ import annotations

import random
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentResponse:
    """Structured response from an agent."""

    private_reasoning: str = ""
    public_statement: str = ""
    vote_target: str | None = None
    bid_level: int | None = None
    technique_self_label: str | None = None
    deception_self_label: str | None = None
    confidence: int | None = None


class AgentInterface(ABC):
    """Abstract base class for all game agents.

    Every agent has a player_id, agent_name, and role assigned at game start.
    Subclasses implement the async action methods.
    """

    def __init__(self, player_id: str, agent_name: str, role: str) -> None:
        self.player_id = player_id
        self.agent_name = agent_name
        self.role = role

    @abstractmethod
    async def campaign(self, game_state: dict[str, Any]) -> AgentResponse:
        """Produce a mayor campaign speech."""
        ...

    @abstractmethod
    async def vote_for_mayor(
        self, game_state: dict[str, Any], candidates: list[str]
    ) -> str:
        """Return the player_id of the candidate this agent votes for."""
        ...

    @abstractmethod
    async def night_action(
        self, game_state: dict[str, Any], role: str
    ) -> str:
        """Return a target player_id for the night action (kill/investigate/protect)."""
        ...

    @abstractmethod
    async def bid(
        self, game_state: dict[str, Any], debate_history: list[str]
    ) -> int:
        """Return a bid level 0-4 for the current speaking slot."""
        ...

    @abstractmethod
    async def speak(
        self, game_state: dict[str, Any], debate_history: list[str]
    ) -> AgentResponse:
        """Deliver a speech during the day phase."""
        ...

    @abstractmethod
    async def vote(
        self, game_state: dict[str, Any], debate_history: list[str]
    ) -> AgentResponse:
        """Cast an elimination vote. vote_target must be set in the response."""
        ...


class MockAgent(AgentInterface):
    """Mock agent that returns random valid actions.

    Used for testing the full game loop without LLM calls.
    """

    _STATEMENTS = [
        "I think we should be careful.",
        "Let's focus on finding the wolves.",
        "Something feels off about the last round.",
        "We should pay attention to voting patterns.",
        "I have a feeling about who might be suspicious.",
    ]

    def _random_alive_target(self, game_state: dict[str, Any]) -> str:
        """Pick a random alive player that is not self."""
        alive: list[str] = [
            pid for pid in game_state.get("alive_players", [])
            if pid != self.player_id
        ]
        if not alive:
            # Fallback — should not happen in a well-formed game
            return self.player_id
        return random.choice(alive)

    async def campaign(self, game_state: dict[str, Any]) -> AgentResponse:
        return AgentResponse(
            private_reasoning="I want to become mayor for strategic advantage.",
            public_statement="I believe I can lead us to find the wolves. Vote for me!",
            deception_self_label="truthful",
            confidence=3,
        )

    async def vote_for_mayor(
        self, game_state: dict[str, Any], candidates: list[str]
    ) -> str:
        eligible = [c for c in candidates if c != self.player_id]
        if not eligible:
            eligible = candidates
        return random.choice(eligible)

    async def night_action(
        self, game_state: dict[str, Any], role: str
    ) -> str:
        return self._random_alive_target(game_state)

    async def bid(
        self, game_state: dict[str, Any], debate_history: list[str]
    ) -> int:
        return random.randint(0, 4)

    async def speak(
        self, game_state: dict[str, Any], debate_history: list[str]
    ) -> AgentResponse:
        return AgentResponse(
            private_reasoning="I'm trying to blend in and not draw attention.",
            public_statement=random.choice(self._STATEMENTS),
            deception_self_label="truthful",
            confidence=3,
        )

    async def vote(
        self, game_state: dict[str, Any], debate_history: list[str]
    ) -> AgentResponse:
        target = self._random_alive_target(game_state)
        return AgentResponse(
            private_reasoning=f"Voting for {target} based on gut feeling.",
            public_statement="I've made my decision.",
            vote_target=target,
            deception_self_label="truthful",
            confidence=3,
        )
