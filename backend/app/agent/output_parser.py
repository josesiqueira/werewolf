"""Tasks 8 & 9 — Output parser, validator, and werewolf leak detection.

Parse JSON from LLM response with repair for common issues.
Validate against game state and auto-correct invalid values.
Detect werewolf leaks in public statements.
"""

from __future__ import annotations

import json
import logging
import random
import re
from typing import Any

from app.engine.agent_interface import AgentResponse

logger = logging.getLogger(__name__)

# Valid deception self-labels
VALID_DECEPTION_LABELS = {
    "truthful", "omission", "distortion", "fabrication", "misdirection",
}

# ---------------------------------------------------------------------------
# Task 9: Werewolf leak detection patterns
# ---------------------------------------------------------------------------

_LEAK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bi\s+targeted\b.*\b(?:last\s+night|during\s+the\s+night|for\s+(?:the\s+)?kill)\b", re.IGNORECASE),
    re.compile(r"\bmy\s+(?:wolf|werewolf)\s+partner\b", re.IGNORECASE),
    re.compile(r"\bwe\s+chose\s+(?:to\s+kill|.*target)", re.IGNORECASE),
    re.compile(r"\bwolf\s+teammate\b", re.IGNORECASE),
    re.compile(r"\bkill\s+last\s+night\b", re.IGNORECASE),
    re.compile(r"\bi['\u2019]?m\s+a\s+werewolf\b", re.IGNORECASE),
    re.compile(r"\bi\s+am\s+a\s+werewolf\b", re.IGNORECASE),
    re.compile(r"\bwe\s+werewolves\b", re.IGNORECASE),
    re.compile(r"\bmy\s+wolf\b", re.IGNORECASE),
    re.compile(r"\bour\s+kill\b", re.IGNORECASE),
    re.compile(r"\bwe\s+killed\b.*\b(?:last\s+night|during\s+the\s+night)\b", re.IGNORECASE),
    re.compile(r"\bi\s+killed\b.*\b(?:last\s+night|during\s+the\s+night)\b", re.IGNORECASE),
    re.compile(r"\bmy\s+(?:werewolf|wolf)\s+teammate\b", re.IGNORECASE),
    re.compile(r"\bas\s+a\s+werewolf\b", re.IGNORECASE),
    re.compile(r"\bfellow\s+wolf\b", re.IGNORECASE),
    re.compile(r"\bfellow\s+werewolf\b", re.IGNORECASE),
    re.compile(r"\bwe\s+attacked\b.*\b(?:last\s+night|during\s+the\s+night)\b", re.IGNORECASE),
    re.compile(r"\bour\s+target\s+last\s+night\b", re.IGNORECASE),
    re.compile(r"\bwolf\s+partner\b", re.IGNORECASE),
    re.compile(r"\bmy\s+partner\b.*\bwerewol(?:f|ves)\b", re.IGNORECASE),
]

_GENERIC_REPLACEMENTS = [
    "I think we need to be more careful about who we trust.",
    "Let's focus on the evidence and make a rational decision.",
    "I've been observing everyone closely and I have concerns.",
    "We should consider all the possibilities before voting.",
    "Something doesn't add up from the last discussion.",
]


def check_werewolf_leaks(statement: str) -> tuple[bool, str]:
    """Check a werewolf's public statement for leaks of night-phase info.

    Parameters
    ----------
    statement:
        The public statement to check.

    Returns
    -------
    tuple[bool, str]
        (has_leak, cleaned_statement) — if a leak is detected, the
        statement is replaced with generic text.
    """
    if not statement:
        return False, statement

    for pattern in _LEAK_PATTERNS:
        if pattern.search(statement):
            logger.warning(
                "Werewolf leak detected (pattern: %s) in statement: %s",
                pattern.pattern,
                statement[:100],
            )
            return True, random.choice(_GENERIC_REPLACEMENTS)

    return False, statement


# ---------------------------------------------------------------------------
# Task 8: JSON repair utilities
# ---------------------------------------------------------------------------

def _strip_markdown_fences(text: str) -> str:
    """Strip ```json ... ``` or ``` ... ``` fences from LLM output."""
    text = text.strip()

    # Match ```json ... ``` or ```JSON ... ``` or ``` ... ```
    fence_pattern = re.compile(
        r"^```(?:json|JSON)?\s*\n?(.*?)\n?\s*```$",
        re.DOTALL,
    )
    match = fence_pattern.match(text)
    if match:
        return match.group(1).strip()

    # Also handle case where ``` appears but not as wrapping
    if text.startswith("```"):
        # Remove first line
        lines = text.split("\n", 1)
        if len(lines) > 1:
            text = lines[1]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    return text


def _fix_trailing_commas(text: str) -> str:
    """Remove trailing commas before } or ]."""
    # Remove trailing commas before closing brace/bracket
    return re.sub(r",\s*([}\]])", r"\1", text)


def _fix_missing_key_quotes(text: str) -> str:
    """Add quotes around unquoted JSON keys."""
    # Match unquoted keys like  key: value  ->  "key": value
    return re.sub(
        r'(?<=\{|,)\s*(\w+)\s*:',
        r' "\1":',
        text,
    )


def _repair_json(raw_text: str) -> str:
    """Apply all JSON repair strategies."""
    text = _strip_markdown_fences(raw_text)
    text = _fix_trailing_commas(text)
    text = _fix_missing_key_quotes(text)
    return text


def _try_parse_json(raw_text: str) -> dict[str, Any] | None:
    """Attempt to parse JSON, with repair fallbacks."""
    # Try direct parse first
    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try with repairs
    repaired = _repair_json(raw_text)
    try:
        return json.loads(repaired)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try to extract JSON object from text
    # Look for the first { ... } block
    brace_match = re.search(r"\{.*\}", repaired, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# ---------------------------------------------------------------------------
# Task 8: Main parse and validate function
# ---------------------------------------------------------------------------

def parse_agent_response(
    raw_text: str,
    alive_players: list[str],
    self_id: str,
    technique_sections: list[str],
) -> AgentResponse:
    """Parse and validate an LLM response into an AgentResponse.

    Parameters
    ----------
    raw_text:
        Raw text from the LLM completion.
    alive_players:
        List of player IDs currently alive.
    self_id:
        The player ID of the agent that produced this response.
    technique_sections:
        List of valid technique section names for the agent's profile.
        Empty list for baseline agents.

    Returns
    -------
    AgentResponse
        Validated and auto-corrected response.
    """
    data = _try_parse_json(raw_text)

    if data is None:
        logger.warning(
            "Failed to parse JSON from LLM response (player %s), "
            "using conservative defaults. Raw: %s",
            self_id,
            raw_text[:200],
        )
        return _get_conservative_defaults(alive_players, self_id)

    # Extract and validate each field
    private_reasoning = str(data.get("private_reasoning", ""))
    public_statement = str(data.get("public_statement", ""))

    # vote_target: must be alive and not self
    vote_target = data.get("vote_target")
    if vote_target is not None:
        vote_target = str(vote_target)
        if vote_target not in alive_players or vote_target == self_id:
            valid_targets = [p for p in alive_players if p != self_id]
            if valid_targets:
                vote_target = random.choice(valid_targets)
                logger.info(
                    "Auto-corrected invalid vote_target for player %s -> %s",
                    self_id, vote_target,
                )
            else:
                vote_target = None

    # bid_level: clamp to 0-4, default to 1 if missing
    bid_level = data.get("bid_level")
    if bid_level is not None:
        try:
            bid_level = int(bid_level)
            bid_level = max(0, min(4, bid_level))
        except (ValueError, TypeError):
            bid_level = 1  # conservative default
    else:
        bid_level = 1  # conservative default when missing

    # deception_self_label: must be valid
    deception_self_label = data.get("deception_self_label")
    if deception_self_label is not None:
        deception_self_label = str(deception_self_label).lower().strip()
        if deception_self_label not in VALID_DECEPTION_LABELS:
            logger.info(
                "Auto-corrected invalid deception_self_label '%s' -> 'truthful'",
                deception_self_label,
            )
            deception_self_label = "truthful"
    else:
        deception_self_label = "truthful"

    # technique_self_label: must reference assigned sections or "none"
    technique_self_label = data.get("technique_self_label")
    if technique_self_label is not None:
        technique_self_label = str(technique_self_label).strip()
        if technique_sections:
            # Check if the label references any valid section
            label_lower = technique_self_label.lower()
            valid = any(
                section.lower() in label_lower or label_lower in section.lower()
                for section in technique_sections
            )
            if not valid and label_lower != "none":
                logger.info(
                    "Auto-corrected invalid technique_self_label '%s' -> 'none'",
                    technique_self_label,
                )
                technique_self_label = "none"
        else:
            # Baseline agent — must be "none"
            if technique_self_label.lower() != "none":
                technique_self_label = "none"

    # confidence: clamp to 1-5
    confidence = data.get("confidence")
    if confidence is not None:
        try:
            confidence = int(confidence)
            confidence = max(1, min(5, confidence))
        except (ValueError, TypeError):
            confidence = 3
    else:
        confidence = 3

    return AgentResponse(
        private_reasoning=private_reasoning,
        public_statement=public_statement,
        vote_target=vote_target,
        bid_level=bid_level,
        technique_self_label=technique_self_label,
        deception_self_label=deception_self_label,
        confidence=confidence,
    )


def _get_conservative_defaults(
    alive_players: list[str],
    self_id: str,
) -> AgentResponse:
    """Return conservative defaults when parsing completely fails."""
    valid_targets = [p for p in alive_players if p != self_id]
    vote_target = random.choice(valid_targets) if valid_targets else None

    return AgentResponse(
        private_reasoning="[parse failure — using defaults]",
        public_statement="I need more time to think about this.",
        vote_target=vote_target,
        bid_level=1,
        technique_self_label="none",
        deception_self_label="truthful",
        confidence=3,
    )
