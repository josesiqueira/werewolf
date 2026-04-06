"""Tests UT-107 to UT-115 — System and user message builders."""

import uuid

import pytest

from app.agent.prompts.system_message import (
    build_system_message,
    clear_cache,
    get_or_build_system_message,
)
from app.agent.prompts.user_message import build_user_message

# Canonical player IDs
P = [str(uuid.uuid4()) for _ in range(7)]


# =========================================================================
# System message builder (UT-107 to UT-110)
# =========================================================================


# UT-107
class TestUT107VillagerSystemMessage:
    """System message for a villager contains all five required sections."""

    def test_villager_sections(self):
        msg = build_system_message(
            role="villager",
            player_id=P[0],
            persona_description="You are reserved and careful.",
        )
        assert "Werewolf" in msg
        assert f"Player {P[0]}" in msg
        assert "Villager" in msg
        assert "Your Persona:" in msg
        assert "private_reasoning" in msg
        assert "Never reveal private information" in msg


# UT-108
class TestUT108WerewolfTeammates:
    """Werewolf system message includes teammate IDs."""

    def test_werewolf_teammates(self):
        msg = build_system_message(
            role="werewolf",
            player_id=P[0],
            persona_description="Bold and aggressive.",
            teammates=[P[1], P[2]],
        )
        assert f"Player {P[1]}" in msg
        assert f"Player {P[2]}" in msg
        assert "werewolf teammate" in msg.lower()


# UT-109
class TestUT109SeerInvestigate:
    """Seer system message references investigation ability."""

    def test_seer_investigate(self):
        msg = build_system_message(
            role="seer",
            player_id=P[2],
            persona_description="Quiet observer.",
        )
        assert "investigate" in msg.lower()


# UT-110
class TestUT110SystemMessageCache:
    """get_or_build_system_message returns identical string on second call."""

    def test_cache_hit(self):
        clear_cache()
        game_id = "test-game-1"
        first = get_or_build_system_message(game_id, P[0], "villager", "Careful thinker.")
        second = get_or_build_system_message(game_id, P[0], "villager", "Careful thinker.")
        assert first == second
        clear_cache()


# =========================================================================
# User message builder (UT-111 to UT-115)
# =========================================================================

_MINIMAL_STATE = {
    "current_round": 1,
    "current_phase": "DAY_SPEECH",
    "alive_players": P,
}


# UT-111
class TestUT111TechniqueIncluded:
    """Non-baseline user message includes the persuasion technique section."""

    def test_technique_section(self):
        msg = build_user_message(
            phase="day_speech",
            game_state=_MINIMAL_STATE,
            technique_text="Ethos content here.",
        )
        assert "=== PERSUASION TECHNIQUE GUIDE ===" in msg
        assert "Ethos content here." in msg
        assert "=== END PERSUASION TECHNIQUE GUIDE ===" in msg


# UT-112
class TestUT112BaselineOmitsTechnique:
    """Baseline agent user message omits the persuasion technique section."""

    def test_no_technique_section(self):
        msg = build_user_message(
            phase="vote",
            game_state={
                "current_round": 2,
                "current_phase": "VOTE",
                "alive_players": P,
            },
            technique_text=None,
        )
        assert "PERSUASION TECHNIQUE GUIDE" not in msg
        assert "=== CURRENT GAME STATE ===" in msg


# UT-113
class TestUT113AlivePlayers:
    """Game state section lists all alive players."""

    def test_all_alive_listed(self):
        msg = build_user_message(
            phase="day_bid",
            game_state={
                "current_round": 1,
                "current_phase": "DAY_BID",
                "alive_players": [P[0], P[1], P[2]],
            },
        )
        assert P[0] in msg
        assert P[1] in msg
        assert P[2] in msg


# UT-114
class TestUT114DebateHistory:
    """Debate history appears in user message with turn numbers."""

    def test_debate_turns(self):
        msg = build_user_message(
            phase="day_speech",
            game_state=_MINIMAL_STATE,
            debate_history=["Alice said something.", "Bob replied."],
        )
        assert "=== CONVERSATION HISTORY ===" in msg
        assert "[Turn 1] Alice said something." in msg
        assert "[Turn 2] Bob replied." in msg


# UT-115
class TestUT115PhaseInstructions:
    """Correct phase instruction is injected for each of the 8 phases."""

    @pytest.mark.parametrize(
        "phase, expected_phrase",
        [
            ("mayor_campaign", "Campaign for mayor"),
            ("mayor_vote", "Vote for mayor"),
            ("night_kill", "eliminate tonight"),
            ("night_investigate", "investigate tonight"),
            ("night_protect", "protect tonight"),
            ("day_bid", "bid"),
            ("day_speech", "persuade"),
            ("vote", "Vote to eliminate"),
        ],
    )
    def test_phase_instruction(self, phase, expected_phrase):
        msg = build_user_message(
            phase=phase,
            game_state=_MINIMAL_STATE,
        )
        assert expected_phrase in msg
