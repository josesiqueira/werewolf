"""Task 7 — Memory manager for conversation context.

Last 2-3 rounds: full dialogue transcript.
Earlier rounds: summarized to key events.

Uses simple word-count approximation for token counting (1 token ~ 0.75 words).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Approximate tokens per word ratio
_WORDS_PER_TOKEN = 0.75


def _estimate_tokens(text: str) -> int:
    """Estimate token count using word-count approximation.

    1 token ~ 0.75 words, so tokens ~ word_count / 0.75.
    """
    word_count = len(text.split())
    return int(word_count / _WORDS_PER_TOKEN)


class MemoryManager:
    """Manages conversation memory with summarization of older rounds.

    Recent rounds (last 2-3) are kept as full transcripts.
    Older rounds are summarized to key events.
    """

    # How many recent rounds to keep in full
    FULL_TRANSCRIPT_ROUNDS = 3

    def __init__(self, max_tokens: int = 2000) -> None:
        self.max_tokens = max_tokens
        self._round_summaries: dict[int, str] = {}

    def summarize_round(
        self,
        round_statements: list[str],
        vote_result: str,
        eliminated: str | None = None,
    ) -> str:
        """Summarize a round into key events.

        Extracts:
          - Who accused whom (looks for accusation keywords)
          - Vote result
          - Who was eliminated and their role

        Parameters
        ----------
        round_statements:
            List of public statements from the round.
        vote_result:
            Description of the vote outcome.
        eliminated:
            Description of who was eliminated (e.g. "Player3 (werewolf)"),
            or None if no elimination.

        Returns
        -------
        str
            A concise summary of the round.
        """
        summary_parts: list[str] = []

        # Extract accusations from statements
        accusation_keywords = [
            "suspect", "suspicious", "accuse", "lying", "werewolf",
            "wolf", "guilty", "voted against", "blame", "don't trust",
            "untrustworthy", "deceiving",
        ]
        accusations: list[str] = []
        for statement in round_statements:
            lower = statement.lower()
            if any(kw in lower for kw in accusation_keywords):
                # Truncate long statements for the summary
                truncated = statement[:120] + "..." if len(statement) > 120 else statement
                accusations.append(truncated)

        if accusations:
            summary_parts.append(
                "Key accusations: " + " | ".join(accusations[:3])
            )

        # Vote result
        summary_parts.append(f"Vote: {vote_result}")

        # Elimination
        if eliminated:
            summary_parts.append(f"Eliminated: {eliminated}")
        else:
            summary_parts.append("No elimination this round.")

        return " ".join(summary_parts)

    def get_context(
        self,
        current_round: int,
        full_history: list[list[str]],
        max_tokens: int | None = None,
    ) -> str:
        """Return conversation context under the token limit.

        Parameters
        ----------
        current_round:
            The current round number (1-indexed).
        full_history:
            List of rounds, each containing a list of public statements.
            Index 0 = round 1, etc.
        max_tokens:
            Override for the maximum token budget. Uses self.max_tokens
            if not provided.

        Returns
        -------
        str
            Formatted conversation context string.
        """
        budget = max_tokens if max_tokens is not None else self.max_tokens
        sections: list[str] = []
        total_tokens = 0

        if not full_history:
            return ""

        num_rounds = len(full_history)

        # Determine which rounds get full transcripts vs summaries
        # Recent rounds (last FULL_TRANSCRIPT_ROUNDS) get full text
        full_start = max(0, num_rounds - self.FULL_TRANSCRIPT_ROUNDS)

        # Build sections in chronological order

        # Older rounds: use summaries
        for round_idx in range(0, min(full_start, num_rounds)):
            round_num = round_idx + 1
            if round_num in self._round_summaries:
                summary = self._round_summaries[round_num]
            else:
                # Generate summary on the fly
                statements = full_history[round_idx]
                summary = self.summarize_round(
                    statements,
                    vote_result="(see game state)",
                    eliminated=None,
                )
                self._round_summaries[round_num] = summary

            section = f"[Round {round_num} summary] {summary}"
            section_tokens = _estimate_tokens(section)

            if total_tokens + section_tokens > budget:
                break
            sections.append(section)
            total_tokens += section_tokens

        # Recent rounds: full transcript
        for round_idx in range(full_start, num_rounds):
            round_num = round_idx + 1
            statements = full_history[round_idx]

            round_lines = [f"[Round {round_num} - full transcript]"]
            for i, stmt in enumerate(statements, 1):
                round_lines.append(f"  Speaker {i}: {stmt}")

            section = "\n".join(round_lines)
            section_tokens = _estimate_tokens(section)

            if total_tokens + section_tokens > budget:
                # Try to fit partial transcript
                partial_lines = [f"[Round {round_num} - partial transcript]"]
                for i, stmt in enumerate(statements, 1):
                    line = f"  Speaker {i}: {stmt}"
                    line_tokens = _estimate_tokens(line)
                    if total_tokens + line_tokens > budget:
                        break
                    partial_lines.append(line)
                    total_tokens += line_tokens

                if len(partial_lines) > 1:
                    sections.append("\n".join(partial_lines))
                break

            sections.append(section)
            total_tokens += section_tokens

        if not sections:
            return ""

        header = "=== PREVIOUS ROUNDS ===\n"
        footer = "\n=== END PREVIOUS ROUNDS ==="
        return header + "\n".join(sections) + footer

    def store_round_summary(
        self,
        round_number: int,
        round_statements: list[str],
        vote_result: str,
        eliminated: str | None = None,
    ) -> None:
        """Pre-compute and store a round summary for later retrieval."""
        self._round_summaries[round_number] = self.summarize_round(
            round_statements, vote_result, eliminated,
        )
