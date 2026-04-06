"""Unit tests UT-066 to UT-070: Schema validation."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.agent import AgentResponse, DeceptionLabel
from app.schemas.game import GameCreate
from app.schemas.player import PlayerResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_agent_kwargs(**overrides) -> dict:
    """Return minimal valid kwargs for AgentResponse, with optional overrides."""
    base = {
        "private_reasoning": "thinking",
        "public_statement": "I am innocent",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# UT-066: bid_level bounds (0-4)
# ---------------------------------------------------------------------------

class TestUT066BidLevelBounds:
    """AgentResponse schema rejects bid_level outside 0-4."""

    def test_bid_level_above_max_rejected(self):
        with pytest.raises(ValidationError):
            AgentResponse(**_valid_agent_kwargs(bid_level=5))

    def test_bid_level_below_min_rejected(self):
        with pytest.raises(ValidationError):
            AgentResponse(**_valid_agent_kwargs(bid_level=-1))

    def test_bid_level_boundary_zero_accepted(self):
        obj = AgentResponse(**_valid_agent_kwargs(bid_level=0))
        assert obj.bid_level == 0

    def test_bid_level_boundary_four_accepted(self):
        obj = AgentResponse(**_valid_agent_kwargs(bid_level=4))
        assert obj.bid_level == 4


# ---------------------------------------------------------------------------
# UT-067: deception_self_label enum validation
# ---------------------------------------------------------------------------

class TestUT067DeceptionSelfLabel:
    """AgentResponse schema rejects invalid deception_self_label values."""

    def test_invalid_label_rejected(self):
        with pytest.raises(ValidationError):
            AgentResponse(**_valid_agent_kwargs(deception_self_label="lying"))

    def test_valid_labels_accepted(self):
        for label in DeceptionLabel:
            obj = AgentResponse(**_valid_agent_kwargs(deception_self_label=label.value))
            assert obj.deception_self_label == label


# ---------------------------------------------------------------------------
# UT-068: confidence bounds (1-5)
# ---------------------------------------------------------------------------

class TestUT068ConfidenceBounds:
    """AgentResponse schema rejects confidence outside 1-5."""

    def test_confidence_zero_rejected(self):
        with pytest.raises(ValidationError):
            AgentResponse(**_valid_agent_kwargs(confidence=0))

    def test_confidence_six_rejected(self):
        with pytest.raises(ValidationError):
            AgentResponse(**_valid_agent_kwargs(confidence=6))

    def test_confidence_boundary_one_accepted(self):
        obj = AgentResponse(**_valid_agent_kwargs(confidence=1))
        assert obj.confidence == 1

    def test_confidence_boundary_five_accepted(self):
        obj = AgentResponse(**_valid_agent_kwargs(confidence=5))
        assert obj.confidence == 5


# ---------------------------------------------------------------------------
# UT-069: GameCreate accepts None config
# ---------------------------------------------------------------------------

class TestUT069GameCreateNullableConfig:
    """GameCreate accepts None config gracefully."""

    def test_empty_body_parses_to_none_config(self):
        obj = GameCreate.model_validate({})
        assert obj.config is None

    def test_explicit_none_config(self):
        obj = GameCreate.model_validate({"config": None})
        assert obj.config is None

    def test_dict_config_accepted(self):
        obj = GameCreate.model_validate({"config": {"max_rounds": 1}})
        assert obj.config == {"max_rounds": 1}


# ---------------------------------------------------------------------------
# UT-070: PlayerResponse boolean type preservation
# ---------------------------------------------------------------------------

class TestUT070PlayerResponseBooleans:
    """PlayerResponse serialises is_mayor and survived as booleans."""

    @staticmethod
    def _make_player_obj(**overrides):
        """Create a mock object that behaves like an ORM model."""

        class FakePlayer:
            id = overrides.get("id", uuid.uuid4())
            game_id = overrides.get("game_id", uuid.uuid4())
            agent_name = overrides.get("agent_name", "Agent_1")
            role = overrides.get("role", "villager")
            persona = overrides.get("persona", None)
            persuasion_profile = overrides.get("persuasion_profile", None)
            is_mayor = overrides.get("is_mayor", False)
            eliminated_round = overrides.get("eliminated_round", None)
            survived = overrides.get("survived", True)
            character_image = overrides.get("character_image", None)

        return FakePlayer()

    def test_booleans_are_bool_type(self):
        player = self._make_player_obj(is_mayor=False, survived=True)
        resp = PlayerResponse.model_validate(player, from_attributes=True)
        assert resp.is_mayor is False
        assert resp.survived is True
        assert isinstance(resp.is_mayor, bool)
        assert isinstance(resp.survived, bool)

    def test_booleans_true_mayor(self):
        player = self._make_player_obj(is_mayor=True, survived=False)
        resp = PlayerResponse.model_validate(player, from_attributes=True)
        assert resp.is_mayor is True
        assert resp.survived is False
        assert isinstance(resp.is_mayor, bool)
        assert isinstance(resp.survived, bool)
