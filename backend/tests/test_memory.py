"""Tests UT-101 to UT-106 — Memory manager (agent/memory.py)."""

import pytest

from app.agent.memory import MemoryManager, _estimate_tokens


# UT-101
class TestUT101SummarizeRoundContents:
    """summarize_round includes vote result and elimination."""

    def test_summary_contains_vote_and_elimination(self):
        mm = MemoryManager()
        summary = mm.summarize_round(
            round_statements=["I trust Alice.", "Bob is suspicious."],
            vote_result="Bob eliminated with 4 votes",
            eliminated="Bob (villager)",
        )
        assert "Bob eliminated with 4 votes" in summary
        assert "Bob (villager)" in summary


# UT-102
class TestUT102AccusationKeywords:
    """Accusation keywords appear in 'Key accusations:' section."""

    def test_accusations_in_summary(self):
        mm = MemoryManager()
        statements = [
            "I suspect Carol is lying about her role.",
            "Carol seems totally fine to me.",
        ]
        summary = mm.summarize_round(
            statements, vote_result="Carol eliminated", eliminated=None,
        )
        assert "Key accusations:" in summary
        assert "Carol" in summary


# UT-103
class TestUT103EmptyHistoryContext:
    """get_context returns empty string when history is empty."""

    def test_empty_history(self):
        mm = MemoryManager()
        result = mm.get_context(current_round=1, full_history=[])
        assert result == ""


# UT-104
class TestUT104SummaryVsTranscript:
    """Rounds beyond FULL_TRANSCRIPT_ROUNDS appear as summaries."""

    def test_old_rounds_summarised(self):
        history = [[f"Statement R{r+1} S{s}" for s in range(2)] for r in range(5)]
        mm = MemoryManager(max_tokens=10000)
        context = mm.get_context(current_round=5, full_history=history)

        assert "[Round 1 summary]" in context
        assert "[Round 2 summary]" in context
        assert "[Round 3 - full transcript]" in context
        assert "[Round 5 - full transcript]" in context


# UT-105
class TestUT105TokenBudgetTruncation:
    """Tight token budget truncates older rounds first."""

    def test_truncation_under_budget(self):
        # Each round has ~267 estimated tokens; with budget=5 no section fits.
        history = [["A " * 200] for _ in range(6)]
        mm = MemoryManager(max_tokens=5)
        context = mm.get_context(current_round=6, full_history=history)

        # Budget is so tight that no sections fit; result should be empty.
        assert context == ""


# UT-106
class TestUT106StoredSummaryUsed:
    """Pre-stored summary is used verbatim by get_context."""

    def test_stored_summary(self):
        mm = MemoryManager(max_tokens=5000)
        mm.store_round_summary(
            1, ["ignored statement"], "custom vote result", "custom elimination",
        )
        history = [["ignored statement"]] + [
            [f"R{r}" for r in range(2)] for _ in range(3)
        ]
        context = mm.get_context(current_round=4, full_history=history)
        assert "custom vote result" in context
