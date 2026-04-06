"""Tests UT-090 to UT-095 — Personas."""

from __future__ import annotations

import pytest

from app.agent.personas import (
    PERSONAS,
    assign_personas,
    get_persona_description,
)


# ===================================================================
# 14. Personas — agent/personas.py
# ===================================================================


class TestUT090_PersonasCount:
    """UT-090: PERSONAS dict contains exactly 7 entries with distinct keys."""

    def test_persona_count_and_keys(self):
        assert len(PERSONAS) == 7
        assert set(PERSONAS.keys()) == {
            "analytical", "aggressive", "quiet", "warm",
            "suspicious", "diplomatic", "blunt",
        }


class TestUT091_PersonaDescriptionsNonEmpty:
    """UT-091: Every persona description is a non-empty string."""

    @pytest.mark.parametrize("key", list(PERSONAS.keys()))
    def test_description_non_empty(self, key):
        v = PERSONAS[key]
        assert isinstance(v, str)
        assert len(v) > 0


class TestUT092_AssignPersonasUnique:
    """UT-092: assign_personas for 7 players produces all-unique assignments."""

    def test_all_unique(self):
        player_ids = [f"p{i}" for i in range(7)]
        result = assign_personas(player_ids)
        assert len(result) == 7
        assert len(set(result.values())) == 7


class TestUT093_AssignPersonasTooMany:
    """UT-093: assign_personas raises ValueError when called with more than 7 players."""

    def test_too_many_players(self):
        player_ids = [f"p{i}" for i in range(8)]
        with pytest.raises(ValueError, match=r"only \d+ are available"):
            assign_personas(player_ids)


class TestUT094_GetPersonaDescription:
    """UT-094: get_persona_description returns the correct description for each persona key."""

    @pytest.mark.parametrize("key", ["analytical", "blunt", "warm"])
    def test_description_matches(self, key):
        assert get_persona_description(key) == PERSONAS[key]


class TestUT095_GetPersonaDescriptionUnknown:
    """UT-095: get_persona_description raises KeyError for an unknown persona."""

    def test_unknown_persona(self):
        with pytest.raises(KeyError):
            get_persona_description("stoic")
