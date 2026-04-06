"""System message builder for LLM agents.

Task 3 — Construct the ~750 token system message cached per agent per game.
Sections: game rules, role assignment, persona, JSON output format, behavioral instructions.
"""

from __future__ import annotations

import json
from functools import lru_cache

# ---------------------------------------------------------------------------
# Section templates
# ---------------------------------------------------------------------------

GAME_RULES = """\
You are playing Werewolf, a social deduction game with 7 players.

Roles: 2 Werewolves, 1 Seer, 1 Doctor, 3 Villagers.
- Werewolves know each other and secretly eliminate one player each night.
- The Seer investigates one player per night to learn their role.
- The Doctor protects one player per night from elimination.
- Villagers have no special ability.

Game flow each round:
1. Night: Werewolves choose a kill target; Seer investigates; Doctor protects.
2. Day: Players bid for speaking turns (bid 0-4), then debate (up to 10 turns).
3. Vote: All living players vote to eliminate one player. Majority wins; the Mayor breaks ties.

The game ends when all Werewolves are eliminated (Village wins) or Werewolves equal or outnumber Villagers (Werewolves win). Maximum 10 rounds.\
"""

OUTPUT_FORMAT_INSTRUCTIONS = """\
You MUST respond with a single JSON object containing exactly these fields:
{
  "private_reasoning": "Your hidden chain-of-thought (not seen by others)",
  "public_statement": "What you say aloud to the group",
  "vote_target": "player_id you vote to eliminate (or null)",
  "bid_level": 0-4,
  "technique_self_label": "which persuasion section you used (or null)",
  "deception_self_label": "truthful|omission|distortion|fabrication|misdirection",
  "confidence": 1-5
}
Do NOT include any text outside the JSON object.\
"""

BEHAVIORAL_INSTRUCTIONS = """\
Adapt your persuasion techniques to the current situation. Do not copy example phrases verbatim. \
Vary your language and reasoning across turns. Stay in character at all times. \
Never reveal private information (night actions, teammate identities) in your public statement.\
"""


def _build_role_section(
    role: str,
    player_id: str,
    teammates: list[str] | None = None,
) -> str:
    """Build the role-assignment section with private info."""
    lines = [f"You are Player {player_id}. Your role is **{role.capitalize()}**."]

    if role == "werewolf" and teammates:
        teammate_str = ", ".join(f"Player {t}" for t in teammates)
        lines.append(f"Your werewolf teammate(s): {teammate_str}.")
        lines.append("Coordinate kills at night. Hide your identity during the day.")
    elif role == "seer":
        lines.append(
            "Each night you investigate one player to learn their true role. "
            "Use this information wisely during debates."
        )
    elif role == "doctor":
        lines.append(
            "Each night you protect one player from being killed. "
            "You may protect yourself. Try to anticipate the werewolf target."
        )
    else:
        lines.append(
            "You have no special night ability. Use discussion and voting "
            "to identify and eliminate the werewolves."
        )

    return "\n".join(lines)


def build_system_message(
    role: str,
    player_id: str,
    persona_description: str,
    teammates: list[str] | None = None,
) -> str:
    """Construct the full system message for an LLM agent.

    Parameters
    ----------
    role : str
        The player's role (werewolf, seer, doctor, villager).
    player_id : str
        This player's identifier.
    persona_description : str
        The assigned persona text (~200 tokens).
    teammates : list[str] | None
        Werewolf teammate player IDs (only for werewolves).

    Returns
    -------
    str
        The assembled system message (~750 tokens).
    """
    role_section = _build_role_section(role, player_id, teammates)

    sections = [
        GAME_RULES,
        role_section,
        f"**Your Persona:**\n{persona_description}",
        OUTPUT_FORMAT_INSTRUCTIONS,
        BEHAVIORAL_INSTRUCTIONS,
    ]

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Cache: one system message per (player_id, game_id) pair
# ---------------------------------------------------------------------------

_system_message_cache: dict[tuple[str, str], str] = {}


def get_or_build_system_message(
    game_id: str,
    player_id: str,
    role: str,
    persona_description: str,
    teammates: list[str] | None = None,
) -> str:
    """Return a cached system message, building it on first call.

    The system message is the same across all turns for a given agent
    within a single game, so we cache it by ``(game_id, player_id)``.
    """
    key = (game_id, player_id)
    if key not in _system_message_cache:
        _system_message_cache[key] = build_system_message(
            role=role,
            player_id=player_id,
            persona_description=persona_description,
            teammates=teammates,
        )
    return _system_message_cache[key]


def clear_cache(game_id: str | None = None) -> None:
    """Clear cached system messages.

    Parameters
    ----------
    game_id : str | None
        If provided, only clear entries for that game.
        If None, clear the entire cache.
    """
    if game_id is None:
        _system_message_cache.clear()
    else:
        keys_to_remove = [k for k in _system_message_cache if k[0] == game_id]
        for k in keys_to_remove:
            del _system_message_cache[k]
