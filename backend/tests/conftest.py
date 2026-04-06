"""Shared fixtures for Werewolf engine unit tests."""

import uuid

import pytest

from app.engine.game_state import GameStateMachine, PlayerInfo

# Canonical 7-player ID set reused across tests
P = [str(uuid.uuid4()) for _ in range(7)]
# P[0]=wolf1, P[1]=wolf2, P[2]=seer, P[3]=doctor,
# P[4]=villager1, P[5]=villager2, P[6]=villager3

FIXED_ROLES = {
    P[0]: "werewolf", P[1]: "werewolf",
    P[2]: "seer",     P[3]: "doctor",
    P[4]: "villager", P[5]: "villager", P[6]: "villager",
}


def make_players(player_ids=None, roles=None):
    """Create PlayerInfo list from FIXED_ROLES or custom mapping."""
    if player_ids is None:
        player_ids = P
    if roles is None:
        roles = FIXED_ROLES
    return [PlayerInfo(player_id=pid, role=roles[pid]) for pid in player_ids]


@pytest.fixture
def game_state():
    """Fresh GameStateMachine with 7 canonical players."""
    return GameStateMachine(players=make_players())
