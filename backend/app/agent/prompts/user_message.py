"""Task 6 — Build the dynamic user message per turn.

Sections:
  1. Persuasion technique document (if not baseline, ~800-1200 tokens)
  2. Current game state as structured text (~300-500 tokens)
  3. Conversation history (from debate_history list)
  4. Turn instruction (varies by phase)

Target total: ~1600-3700 tokens.
"""

from __future__ import annotations

from typing import Any


# Phase -> instruction text mapping
_TURN_INSTRUCTIONS: dict[str, str] = {
    "mayor_campaign": (
        "Campaign for mayor. Explain why the village should trust you "
        "with leadership. Make a compelling public statement."
    ),
    "mayor_vote": (
        "Vote for mayor. Choose one of the candidates to lead the village. "
        "Set vote_target to the player_id of your chosen candidate."
    ),
    "night_kill": (
        "Choose a target to eliminate tonight. Select a non-werewolf player "
        "who you believe poses the greatest threat. Set vote_target to their player_id."
    ),
    "night_investigate": (
        "Choose a player to investigate tonight. You will learn their true role. "
        "Set vote_target to the player_id you want to investigate."
    ),
    "night_protect": (
        "Choose a player to protect tonight. If the werewolves target this player, "
        "the kill will be prevented. Set vote_target to their player_id."
    ),
    "day_bid": (
        "Place your bid to speak (0-4). Higher bids give you priority to speak next. "
        "0 means you pass; 4 means you urgently need to say something. "
        "Set bid_level to your chosen value."
    ),
    "day_speech": (
        "Make your statement to the village. This is your chance to persuade, "
        "accuse, defend, or share information. Craft a compelling public_statement."
    ),
    "vote": (
        "Vote to eliminate a player. Based on the discussion, choose who you "
        "believe is a werewolf (or who should be eliminated for strategic reasons). "
        "Set vote_target to their player_id."
    ),
}


def _format_game_state(game_state: dict[str, Any]) -> str:
    """Format the current game state as structured text (~300-500 tokens)."""
    lines: list[str] = []
    lines.append("=== CURRENT GAME STATE ===")
    lines.append(f"Round: {game_state.get('current_round', '?')}")
    lines.append(f"Phase: {game_state.get('current_phase', '?')}")

    # Mayor
    mayor = game_state.get("mayor_id") or game_state.get("mayor")
    if mayor:
        lines.append(f"Mayor: {mayor}")
    else:
        lines.append("Mayor: not yet elected")

    # Alive players
    alive = game_state.get("alive_players", [])
    lines.append(f"\nAlive players ({len(alive)}):")
    for pid in alive:
        lines.append(f"  - {pid}")

    # Eliminated players with roles
    eliminated = game_state.get("eliminated_players", [])
    if eliminated:
        lines.append(f"\nEliminated players ({len(eliminated)}):")
        for ep in eliminated:
            if isinstance(ep, dict):
                name = ep.get("agent_name", ep.get("player_id", "?"))
                role = ep.get("role", "?")
                rnd = ep.get("round", ep.get("eliminated_round", "?"))
                lines.append(f"  - {name} (role: {role}, eliminated round {rnd})")
            else:
                lines.append(f"  - {ep}")

    # Night results (if available in game state)
    night_results = game_state.get("night_results")
    if night_results:
        lines.append("\nLast night:")
        if isinstance(night_results, dict):
            if night_results.get("kill_successful"):
                lines.append(
                    f"  - {night_results.get('killed_player', 'someone')} was killed"
                )
            else:
                lines.append("  - No one was killed (doctor saved)")
        elif isinstance(night_results, str):
            lines.append(f"  - {night_results}")

    # Voting history
    voting_history = game_state.get("voting_history")
    if voting_history:
        lines.append("\nRecent voting history:")
        if isinstance(voting_history, list):
            for entry in voting_history[-3:]:  # last 3 rounds
                lines.append(f"  - {entry}")
        elif isinstance(voting_history, str):
            lines.append(f"  - {voting_history}")

    # Private info (role-specific)
    private_info = game_state.get("private_info")
    if private_info:
        lines.append("\n=== YOUR PRIVATE INFORMATION ===")
        if isinstance(private_info, dict):
            for key, value in private_info.items():
                lines.append(f"  {key}: {value}")
        elif isinstance(private_info, str):
            lines.append(f"  {private_info}")

    lines.append("=== END GAME STATE ===")
    return "\n".join(lines)


def _format_conversation_history(debate_history: list[str]) -> str:
    """Format conversation history from the debate."""
    if not debate_history:
        return ""

    lines: list[str] = ["=== CONVERSATION HISTORY ==="]
    for i, statement in enumerate(debate_history, 1):
        lines.append(f"[Turn {i}] {statement}")
    lines.append("=== END CONVERSATION HISTORY ===")
    return "\n".join(lines)


def build_user_message(
    phase: str,
    game_state: dict[str, Any],
    debate_history: list[str] | None = None,
    technique_text: str | None = None,
    memory_context: str | None = None,
) -> str:
    """Construct the dynamic user message for a specific turn.

    Parameters
    ----------
    phase:
        The current phase (e.g. "mayor_campaign", "vote", "day_speech").
    game_state:
        The game state dict visible to this agent.
    debate_history:
        List of public statements from the current round's debate.
    technique_text:
        The persuasion technique document text (None for baseline agents).
    memory_context:
        Pre-formatted conversation context from the MemoryManager.

    Returns
    -------
    str
        The complete user message string (~1600-3700 tokens).
    """
    sections: list[str] = []

    # Section 1: Persuasion technique document (~800-1200 tokens)
    if technique_text:
        sections.append("=== PERSUASION TECHNIQUE GUIDE ===")
        sections.append(technique_text)
        sections.append("=== END PERSUASION TECHNIQUE GUIDE ===")
        sections.append("")

    # Section 2: Current game state (~300-500 tokens)
    sections.append(_format_game_state(game_state))
    sections.append("")

    # Section 3: Conversation history
    if memory_context:
        sections.append(memory_context)
        sections.append("")

    if debate_history:
        sections.append(_format_conversation_history(debate_history))
        sections.append("")

    # Section 4: Turn instruction
    instruction = _TURN_INSTRUCTIONS.get(phase, _TURN_INSTRUCTIONS.get("vote", ""))
    sections.append("=== YOUR TASK ===")
    sections.append(instruction)
    sections.append("")
    sections.append(
        "Respond with a JSON object containing: private_reasoning, "
        "public_statement, vote_target (if applicable), bid_level (if applicable), "
        "technique_self_label, deception_self_label, confidence (1-5)."
    )

    return "\n".join(sections)
