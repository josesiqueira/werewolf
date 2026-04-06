"""Persuasion technique loader.

Task 5 — Load the 6 technique files from ``persuasion-techniques/``,
cache them in memory, and provide lookup by profile name.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Profile -> filename mapping
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/app/agent -> project root
_TECHNIQUES_DIR = _PROJECT_ROOT / "persuasion-techniques"

PROFILE_FILE_MAP: dict[str, str] = {
    "ethos": "TECHNIQUE-ETHOS.md",
    "pathos": "TECHNIQUE-PATHOS.md",
    "logos": "TECHNIQUE-LOGOS.md",
    "authority_socialproof": "TECHNIQUE-AUTHORITY-SOCIALPROOF.md",
    "reciprocity_liking": "TECHNIQUE-RECIPROCITY-LIKING.md",
    "scarcity_commitment": "TECHNIQUE-SCARCITY-COMMITMENT.md",
}

ALL_PROFILES: list[str] = list(PROFILE_FILE_MAP.keys()) + ["baseline"]

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

_cache: dict[str, str] = {}
_sections_cache: dict[str, list[str]] = {}


def _ensure_loaded(profile: str) -> None:
    """Load and cache a technique file if not already cached."""
    if profile in _cache:
        return

    filename = PROFILE_FILE_MAP.get(profile)
    if filename is None:
        return  # baseline or unknown — nothing to load

    filepath = _TECHNIQUES_DIR / filename
    if not filepath.exists():
        logger.error("Technique file not found: %s", filepath)
        return

    text = filepath.read_text(encoding="utf-8")
    _cache[profile] = text

    # Extract section names (lines starting with "## ")
    sections = re.findall(r"^## (.+)$", text, re.MULTILINE)
    _sections_cache[profile] = sections

    logger.info("Loaded technique file for profile '%s': %s", profile, filename)


def load_technique(profile: str) -> str | None:
    """Return the full technique document for a profile.

    Parameters
    ----------
    profile : str
        One of: ethos, pathos, logos, authority_socialproof,
        reciprocity_liking, scarcity_commitment, baseline.

    Returns
    -------
    str | None
        The file content, or ``None`` for baseline / unknown profiles.
    """
    if profile == "baseline":
        return None

    _ensure_loaded(profile)
    return _cache.get(profile)


def get_technique_sections(profile: str) -> list[str]:
    """Return the ``## ``-level section names from a technique file.

    Useful for validating ``technique_self_label`` values.

    Parameters
    ----------
    profile : str
        Profile name.

    Returns
    -------
    list[str]
        Section headings (without the ``## `` prefix), e.g.
        ``["Core Principle", "When Accusing", ...]``.
        Empty list for baseline or unknown profiles.
    """
    if profile == "baseline":
        return []

    _ensure_loaded(profile)
    return _sections_cache.get(profile, [])


def preload_all() -> None:
    """Eagerly load all technique files into the cache."""
    for profile in PROFILE_FILE_MAP:
        _ensure_loaded(profile)


def clear_cache() -> None:
    """Clear the in-memory technique cache."""
    _cache.clear()
    _sections_cache.clear()
