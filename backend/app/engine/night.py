"""Night phase resolution for Werewolf AI Agents.

Pure logic — no database calls, no LLM calls.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.game_state import GameStateMachine


@dataclass
class NightResult:
    """Outcome of a single night phase."""
    killed_player: str | None
    seer_result: dict | None  # {"target_id": str, "role": str} or None
    kill_successful: bool


def resolve_night(
    wolf_target: str | None,
    seer_target: str | None,
    doctor_target: str | None,
    game_state: GameStateMachine,
) -> NightResult:
    """Resolve all night actions and return the result.

    Rules:
        - If doctor_target == wolf_target the kill is blocked.
        - Otherwise the wolf_target is eliminated.
        - The seer learns the true role of seer_target.

    Args:
        wolf_target: Player targeted by the werewolves (None if no target).
        seer_target: Player investigated by the seer (None if seer is dead).
        doctor_target: Player protected by the doctor (None if doctor is dead).
        game_state: Current game state (used to look up roles and apply
            eliminations).

    Returns:
        NightResult describing what happened.
    """
    # Seer investigation
    seer_result: dict | None = None
    if seer_target is not None:
        target_role = game_state._player_roles.get(seer_target, "unknown")
        seer_result = {"target_id": seer_target, "role": target_role}

    # Werewolf kill
    if wolf_target is None:
        return NightResult(
            killed_player=None,
            seer_result=seer_result,
            kill_successful=False,
        )

    if doctor_target == wolf_target:
        # Doctor saved the target
        return NightResult(
            killed_player=None,
            seer_result=seer_result,
            kill_successful=False,
        )

    # Kill succeeds
    game_state.eliminate_player(wolf_target)
    return NightResult(
        killed_player=wolf_target,
        seer_result=seer_result,
        kill_successful=True,
    )
