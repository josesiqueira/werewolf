"""Task 10 — LLM agent implementation.

LLMAgent extends AgentInterface, wiring together:
  - System message builder (cached after first call)
  - User message builder (per turn)
  - LLM client with retry
  - Output parser and validator
  - Werewolf leak detection
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from app.engine.agent_interface import AgentInterface, AgentResponse

# These modules are created by Agent A — imported at runtime
from app.agent.llm_client import LLMClient
from app.agent.memory import MemoryManager
from app.agent.output_parser import check_werewolf_leaks, parse_agent_response
from app.agent.personas import get_persona_description
from app.agent.prompts.system_message import build_system_message
from app.agent.prompts.user_message import build_user_message
from app.agent.retry import call_with_retry_and_fallback, build_default_response
from app.agent.techniques import get_technique_sections, load_technique

logger = logging.getLogger(__name__)


@dataclass
class TurnMetadata:
    """Metadata tracked per turn for diagnostics."""

    token_count_input: int = 0
    token_count_output: int = 0
    latency_ms: int = 0
    is_default_response: bool = False


class LLMAgent(AgentInterface):
    """LLM-backed agent that uses GPT to play Werewolf.

    Parameters
    ----------
    player_id:
        Unique player identifier (UUID string).
    agent_name:
        Human-readable agent name.
    role:
        Assigned role (werewolf, seer, doctor, villager).
    persona:
        Persona name for personality/style.
    persuasion_profile:
        Technique profile name (e.g. "ethos", "baseline").
    config:
        Application settings or config dict.
    """

    def __init__(
        self,
        player_id: str,
        agent_name: str,
        role: str,
        persona: str = "analytical",
        persuasion_profile: str = "baseline",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(player_id, agent_name, role)
        self.persona = persona
        self.persuasion_profile = persuasion_profile
        self.config = config or {}

        # LLM client
        self._llm_client = LLMClient(
            model=self.config.get("openai_model", "gpt-4o"),
            timeout=self.config.get("llm_timeout", 60),
        )

        # Memory manager
        self._memory = MemoryManager(
            max_tokens=self.config.get("memory_max_tokens", 2000),
        )

        # Cached values
        self._system_message: str | None = None
        self._technique_text: str | None = None
        self._technique_sections: list[str] = []
        self._persona_description: str = ""

        # Turn tracking
        self._round_history: list[list[str]] = []
        self.last_turn_metadata: TurnMetadata = TurnMetadata()

    # ------------------------------------------------------------------
    # Lazy initialization
    # ------------------------------------------------------------------

    def _ensure_initialized(self) -> None:
        """Build and cache the system message and technique data."""
        if self._system_message is not None:
            return

        # Load persona
        self._persona_description = get_persona_description(self.persona)

        # Load technique
        if self.persuasion_profile and self.persuasion_profile != "baseline":
            self._technique_text = load_technique(self.persuasion_profile)
            self._technique_sections = get_technique_sections(
                self.persuasion_profile
            )
        else:
            self._technique_text = None
            self._technique_sections = []

        # Build system message (cached for the rest of the game)
        self._system_message = build_system_message(
            role=self.role,
            player_id=self.player_id,
            persona_description=self._persona_description,
        )

    # ------------------------------------------------------------------
    # Core LLM call pipeline
    # ------------------------------------------------------------------

    async def _call_llm(
        self,
        phase: str,
        game_state: dict[str, Any],
        debate_history: list[str] | None = None,
    ) -> AgentResponse:
        """Execute the full LLM pipeline for a single turn.

        1. Build system message (cached)
        2. Build user message
        3. Call LLM with retry
        4. Parse and validate response
        5. Check for werewolf leaks (if applicable)
        6. Return AgentResponse
        """
        self._ensure_initialized()

        # Build memory context from round history
        memory_context: str | None = None
        if self._round_history:
            memory_context = self._memory.get_context(
                current_round=game_state.get("current_round", 1),
                full_history=self._round_history,
            )

        # Build user message
        user_message = build_user_message(
            phase=phase,
            game_state=game_state,
            debate_history=debate_history,
            technique_text=self._technique_text,
            memory_context=memory_context,
        )

        # Call LLM with retry
        metadata = TurnMetadata()
        start_time = time.monotonic()

        alive_players = game_state.get("alive_players", [])
        sys_msg = self._system_message

        llm_result, is_default = await call_with_retry_and_fallback(
            lambda: self._llm_client.complete(sys_msg, user_message),
            alive_players,
            self.player_id,
        )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        if is_default:
            metadata.latency_ms = elapsed_ms
            metadata.is_default_response = True
            self.last_turn_metadata = metadata
            return llm_result

        llm_response = llm_result
        metadata.token_count_input = llm_response.token_count_input
        metadata.token_count_output = llm_response.token_count_output
        metadata.latency_ms = llm_response.latency_ms
        raw_text = llm_response.text

        # Parse and validate response
        response = parse_agent_response(
            raw_text=raw_text,
            alive_players=alive_players,
            self_id=self.player_id,
            technique_sections=self._technique_sections,
        )

        # Check if we got defaults from parse failure
        if response.private_reasoning == "[parse failure — using defaults]":
            metadata.is_default_response = True

        # Werewolf leak detection (Task 9)
        if self.role == "werewolf" and response.public_statement:
            has_leak, cleaned = check_werewolf_leaks(response.public_statement)
            if has_leak:
                response.public_statement = cleaned

        self.last_turn_metadata = metadata
        return response

    # ------------------------------------------------------------------
    # AgentInterface methods
    # ------------------------------------------------------------------

    async def campaign(self, game_state: dict[str, Any]) -> AgentResponse:
        """Produce a mayor campaign speech."""
        return await self._call_llm("mayor_campaign", game_state)

    async def vote_for_mayor(
        self, game_state: dict[str, Any], candidates: list[str]
    ) -> str:
        """Return the player_id of the candidate this agent votes for."""
        # Add candidates to game state for context
        state = dict(game_state)
        state["candidates"] = candidates

        response = await self._call_llm("mayor_vote", state)
        target = response.vote_target

        # Validate: must be a candidate and not self
        if target and target in candidates and target != self.player_id:
            return target

        # Fallback: pick a valid candidate
        eligible = [c for c in candidates if c != self.player_id]
        if not eligible:
            eligible = candidates
        import random
        return random.choice(eligible)

    async def night_action(
        self, game_state: dict[str, Any], role: str
    ) -> str:
        """Return a target player_id for the night action."""
        phase_map = {
            "werewolf": "night_kill",
            "seer": "night_investigate",
            "doctor": "night_protect",
        }
        phase = phase_map.get(role, "night_kill")
        response = await self._call_llm(phase, game_state)

        target = response.vote_target
        alive = game_state.get("alive_players", [])

        if target and target in alive and target != self.player_id:
            return target

        # Fallback: random alive target (not self)
        import random
        valid = [p for p in alive if p != self.player_id]
        return random.choice(valid) if valid else self.player_id

    async def bid(
        self, game_state: dict[str, Any], debate_history: list[str]
    ) -> int:
        """Return a bid level 0-4."""
        response = await self._call_llm("day_bid", game_state, debate_history)
        bid = response.bid_level
        if bid is not None:
            return max(0, min(4, bid))
        return 1  # conservative default

    async def speak(
        self, game_state: dict[str, Any], debate_history: list[str]
    ) -> AgentResponse:
        """Deliver a speech during the day phase."""
        return await self._call_llm("day_speech", game_state, debate_history)

    async def vote(
        self, game_state: dict[str, Any], debate_history: list[str]
    ) -> AgentResponse:
        """Cast an elimination vote."""
        return await self._call_llm("vote", game_state, debate_history)

    # ------------------------------------------------------------------
    # Memory management
    # ------------------------------------------------------------------

    def update_round_history(
        self,
        round_statements: list[str],
        vote_result: str = "",
        eliminated: str | None = None,
    ) -> None:
        """Add a completed round's data to the memory manager.

        Called by the game loop after each round completes.
        """
        self._round_history.append(round_statements)

        round_num = len(self._round_history)
        self._memory.store_round_summary(
            round_number=round_num,
            round_statements=round_statements,
            vote_result=vote_result,
            eliminated=eliminated,
        )
