"""Tests UT-096 to UT-100 — Technique loader (agent/techniques.py)."""

import pytest

from app.agent.techniques import (
    PROFILE_FILE_MAP,
    clear_cache,
    get_technique_sections,
    load_technique,
    preload_all,
)


@pytest.fixture(autouse=True)
def _cold_cache():
    """Ensure a fresh cache for every test."""
    clear_cache()
    yield
    clear_cache()


# UT-096
class TestUT096AllTechniqueFilesLoad:
    """All 6 non-baseline technique files load without error."""

    def test_preload_all_populates_cache(self):
        preload_all()
        for profile in PROFILE_FILE_MAP:
            text = load_technique(profile)
            assert isinstance(text, str), f"Expected str for {profile}"
            assert len(text) > 0, f"Expected non-empty text for {profile}"


# UT-097
class TestUT097BaselineReturnsNone:
    """load_technique('baseline') returns None."""

    def test_baseline_returns_none(self):
        result = load_technique("baseline")
        assert result is None


# UT-098
class TestUT098EthosSections:
    """get_technique_sections('ethos') returns expected section headings."""

    def test_ethos_sections(self):
        sections = get_technique_sections("ethos")
        assert isinstance(sections, list)
        assert len(sections) >= 1
        assert "Core Principle" in sections
        assert "When Accusing" in sections
        assert "When Defending" in sections


# UT-099
class TestUT099BaselineSectionsEmpty:
    """get_technique_sections('baseline') returns an empty list."""

    def test_baseline_sections(self):
        result = get_technique_sections("baseline")
        assert result == []


# UT-100
class TestUT100IdempotentCacheHit:
    """Second load_technique call hits cache, returns identical content."""

    def test_idempotent(self):
        first = load_technique("pathos")
        second = load_technique("pathos")
        assert first == second
        assert first is not None
