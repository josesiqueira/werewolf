"""Tests UT-071 to UT-089 — Output parser and werewolf leak detection."""

from __future__ import annotations

import json
import uuid

import pytest

from app.agent.output_parser import (
    check_werewolf_leaks,
    parse_agent_response,
    _GENERIC_REPLACEMENTS,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

P = [str(uuid.uuid4()) for _ in range(7)]
SELF_ID = P[0]
ALIVE_OTHERS = P[1:]


def _make_raw(**overrides: object) -> str:
    """Build a valid JSON payload with sensible defaults, then apply overrides."""
    base = {
        "private_reasoning": "thinking",
        "public_statement": "Hello.",
        "vote_target": P[2],
        "bid_level": 2,
        "technique_self_label": "none",
        "deception_self_label": "truthful",
        "confidence": 3,
    }
    base.update(overrides)
    return json.dumps(base)


# ===================================================================
# 12. Output Parser — agent/output_parser.py
# ===================================================================


class TestUT071_ValidJSON:
    """UT-071: Valid JSON parses to correct AgentResponse fields."""

    def test_valid_json_parses_correctly(self):
        raw = json.dumps({
            "private_reasoning": "I suspect P[1].",
            "public_statement": "Let's vote carefully.",
            "vote_target": P[2],
            "bid_level": 3,
            "technique_self_label": "Core Principle",
            "deception_self_label": "omission",
            "confidence": 5,
        })
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=["Core Principle"])
        assert result.public_statement == "Let's vote carefully."
        assert result.bid_level == 3
        assert result.deception_self_label == "omission"
        assert result.confidence == 5
        assert result.vote_target == P[2]


class TestUT072_MarkdownFences:
    """UT-072: Markdown-fenced JSON is stripped and parsed successfully."""

    def test_markdown_fenced_json(self):
        raw = "```json\n" + json.dumps({
            "private_reasoning": "hidden",
            "public_statement": "Hello village.",
            "vote_target": None,
            "bid_level": 1,
            "technique_self_label": "none",
            "deception_self_label": "truthful",
            "confidence": 3,
        }) + "\n```"
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.public_statement == "Hello village."


class TestUT073_TrailingComma:
    """UT-073: Trailing-comma JSON is repaired and parsed."""

    def test_trailing_comma_repaired(self):
        raw = """{
  "private_reasoning": "thinking",
  "public_statement": "I agree.",
  "vote_target": null,
  "bid_level": 1,
  "technique_self_label": "none",
  "deception_self_label": "truthful",
  "confidence": 3,
}"""
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.public_statement == "I agree."
        assert result.public_statement != "I need more time to think about this."


class TestUT074_InvalidTextDefaults:
    """UT-074: Completely invalid text falls back to conservative defaults."""

    def test_invalid_text_defaults(self):
        raw = "Sorry, I cannot assist with that request."
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.private_reasoning == "[parse failure — using defaults]"
        assert result.public_statement == "I need more time to think about this."
        assert result.bid_level == 1
        assert result.deception_self_label == "truthful"
        assert result.confidence == 3
        assert result.vote_target in P[1:]


class TestUT075_VoteTargetSelf:
    """UT-075: vote_target pointing to self is auto-corrected."""

    def test_self_vote_corrected(self):
        raw = _make_raw(vote_target=P[0])
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.vote_target != P[0]
        assert result.vote_target in P[1:]


class TestUT076_VoteTargetDead:
    """UT-076: vote_target for an eliminated player is auto-corrected."""

    def test_dead_player_vote_corrected(self):
        dead_player = str(uuid.uuid4())
        raw = _make_raw(vote_target=dead_player)
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.vote_target in P[1:]


class TestUT077_BidClampHigh:
    """UT-077: bid_level above 4 is clamped to 4."""

    def test_bid_clamped_high(self):
        raw = _make_raw(bid_level=99)
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.bid_level == 4


class TestUT078_BidClampNegative:
    """UT-078: Negative bid_level is clamped to 0."""

    def test_bid_clamped_negative(self):
        raw = _make_raw(bid_level=-5)
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.bid_level == 0


class TestUT079_InvalidDeceptionLabel:
    """UT-079: Unrecognised deception_self_label is auto-corrected to 'truthful'."""

    @pytest.mark.parametrize("bad_label", ["lying", "honest", "DECEIVING", ""])
    def test_invalid_deception_corrected(self, bad_label):
        raw = _make_raw(deception_self_label=bad_label)
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.deception_self_label == "truthful"


class TestUT080_ValidDeceptionLabels:
    """UT-080: Valid deception_self_label values are preserved exactly."""

    @pytest.mark.parametrize("label", [
        "truthful", "omission", "distortion", "fabrication", "misdirection",
    ])
    def test_valid_deception_preserved(self, label):
        raw = _make_raw(deception_self_label=label)
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.deception_self_label == label


class TestUT081_MissingBidDefault:
    """UT-081: Missing bid_level key defaults to 1."""

    def test_missing_bid_defaults_to_1(self):
        payload = {
            "private_reasoning": "thinking",
            "public_statement": "hi",
            "vote_target": P[2],
            "technique_self_label": "none",
            "deception_self_label": "truthful",
            "confidence": 3,
        }
        raw = json.dumps(payload)
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.bid_level == 1


class TestUT082_MissingConfidenceDefault:
    """UT-082: Missing confidence key defaults to 3."""

    def test_missing_confidence_defaults_to_3(self):
        payload = {
            "private_reasoning": "thinking",
            "public_statement": "hi",
            "vote_target": P[2],
            "bid_level": 2,
            "technique_self_label": "none",
            "deception_self_label": "truthful",
        }
        raw = json.dumps(payload)
        result = parse_agent_response(raw, alive_players=P, self_id=P[0],
                                      technique_sections=[])
        assert result.confidence == 3


# ===================================================================
# 13. Werewolf Leak Detection — agent/output_parser.py
# ===================================================================


class TestUT083_ExplicitRoleAdmission:
    """UT-083: Explicit role admission triggers leak detection."""

    def test_im_a_werewolf_leak(self):
        statement = "Trust me everyone — I'm a werewolf and I chose to save you."
        has_leak, cleaned = check_werewolf_leaks(statement)
        assert has_leak is True
        assert cleaned != statement
        assert cleaned in _GENERIC_REPLACEMENTS


class TestUT084_NightKillAdmission:
    """UT-084: Direct night-kill admission triggers leak detection."""

    def test_we_killed_last_night(self):
        statement = "We killed Alice last night to protect ourselves."
        has_leak, cleaned = check_werewolf_leaks(statement)
        assert has_leak is True
        assert cleaned != statement


class TestUT085_WolfTeammateReference:
    """UT-085: Wolf teammate reference triggers leak detection."""

    def test_wolf_partner(self):
        statement = "My wolf partner and I discussed this."
        has_leak, cleaned = check_werewolf_leaks(statement)
        assert has_leak is True
        assert cleaned in _GENERIC_REPLACEMENTS


class TestUT086_InnocentWolfLanguage:
    """UT-086: Innocent wolf-themed language does NOT trigger leak detection."""

    @pytest.mark.parametrize("statement", [
        "I think there's a wolf among us, let's be careful.",
        "The wolves will win if we don't vote correctly.",
        "We should hunt the wolf down.",
    ])
    def test_innocent_wolf_language_no_leak(self, statement):
        has_leak, cleaned = check_werewolf_leaks(statement)
        assert has_leak is False
        assert cleaned == statement


class TestUT087_EmptyStatement:
    """UT-087: Empty statement is returned unchanged with has_leak == False."""

    def test_empty_statement(self):
        has_leak, cleaned = check_werewolf_leaks("")
        assert has_leak is False
        assert cleaned == ""


class TestUT088_OurKill:
    """UT-088: 'Our kill' phrase triggers leak detection."""

    def test_our_kill_leak(self):
        statement = "We need to be careful — our kill last night raised suspicion."
        has_leak, cleaned = check_werewolf_leaks(statement)
        assert has_leak is True


class TestUT089_AsAWerewolf:
    """UT-089: 'As a werewolf' phrase triggers leak detection."""

    def test_as_a_werewolf_leak(self):
        statement = "As a werewolf, I obviously want to mislead you."
        has_leak, cleaned = check_werewolf_leaks(statement)
        assert has_leak is True
        assert cleaned in _GENERIC_REPLACEMENTS
