"""Tests UT-014 to UT-017 — Role Assignment."""

from collections import Counter

import pytest

from app.engine.roles import assign_roles, get_private_info
from tests.conftest import P, FIXED_ROLES


# UT-014: assign_roles produces exactly the fixed distribution for 7 players
class TestUT014:
    def test_assign_roles_distribution(self):
        player_ids = [f"p{i}" for i in range(7)]
        result = assign_roles(player_ids)
        assert Counter(result.values()) == {
            "werewolf": 2,
            "seer": 1,
            "doctor": 1,
            "villager": 3,
        }


# UT-015: assign_roles raises ValueError for wrong player count
class TestUT015:
    def test_assign_roles_too_few(self):
        with pytest.raises(ValueError, match="Expected 7 players"):
            assign_roles([f"p{i}" for i in range(6)])

    def test_assign_roles_too_many(self):
        with pytest.raises(ValueError, match="Expected 7 players"):
            assign_roles([f"p{i}" for i in range(8)])


# UT-016: get_private_info — werewolf receives teammate list
class TestUT016:
    def test_werewolf_private_info(self):
        info = get_private_info(P[0], "werewolf", FIXED_ROLES)
        assert info == {"role": "werewolf", "teammates": [P[1]]}


# UT-017: get_private_info — non-werewolf roles receive only their role
class TestUT017:
    def test_seer_private_info(self):
        info = get_private_info(P[2], "seer", FIXED_ROLES)
        assert info == {"role": "seer"}
        assert "teammates" not in info

    def test_doctor_private_info(self):
        info = get_private_info(P[3], "doctor", FIXED_ROLES)
        assert info == {"role": "doctor"}
        assert "teammates" not in info

    def test_villager_private_info(self):
        info = get_private_info(P[4], "villager", FIXED_ROLES)
        assert info == {"role": "villager"}
        assert "teammates" not in info
