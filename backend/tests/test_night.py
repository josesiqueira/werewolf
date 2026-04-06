"""Tests UT-018 to UT-022 — Night Phase Resolution."""

import pytest

from app.engine.game_state import GameStateMachine, PlayerInfo
from app.engine.night import resolve_night
from tests.conftest import P, FIXED_ROLES, make_players


# UT-018: Wolf kill succeeds when doctor protects a different player
class TestUT018:
    def test_wolf_kill_succeeds(self, game_state):
        result = resolve_night(
            wolf_target=P[4],
            seer_target=None,
            doctor_target=P[3],
            game_state=game_state,
        )
        assert result.kill_successful is True
        assert result.killed_player == P[4]
        assert P[4] not in game_state.alive_players


# UT-019: Doctor save blocks wolf kill when targets match
class TestUT019:
    def test_doctor_save_blocks_kill(self, game_state):
        result = resolve_night(
            wolf_target=P[4],
            seer_target=None,
            doctor_target=P[4],
            game_state=game_state,
        )
        assert result.kill_successful is False
        assert result.killed_player is None
        assert P[4] in game_state.alive_players


# UT-020: Seer investigation returns correct role
class TestUT020:
    def test_seer_finds_werewolf(self, game_state):
        result = resolve_night(
            wolf_target=P[4],
            seer_target=P[1],
            doctor_target=P[3],
            game_state=game_state,
        )
        assert result.seer_result == {"target_id": P[1], "role": "werewolf"}


# UT-021: No wolf target produces no kill
class TestUT021:
    def test_no_wolf_target_no_kill(self, game_state):
        alive_before = list(game_state.alive_players)
        result = resolve_night(
            wolf_target=None,
            seer_target=P[2],
            doctor_target=P[4],
            game_state=game_state,
        )
        assert result.killed_player is None
        assert result.kill_successful is False
        assert game_state.alive_players == alive_before


# UT-022: Seer investigates a villager
class TestUT022:
    def test_seer_finds_villager(self, game_state):
        result = resolve_night(
            wolf_target=None,
            seer_target=P[4],
            doctor_target=None,
            game_state=game_state,
        )
        assert result.seer_result == {"target_id": P[4], "role": "villager"}
