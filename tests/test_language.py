"""Tests for the Telugu language detection and translation layer."""

import pytest

from checkup.language.detector import detect_language


class TestLanguageDetection:
    """Tests for detect_language()."""

    def test_telugu_script(self):
        """Should detect Telugu script characters."""
        assert detect_language("నాకు తలనొప్పి గా ఉంది") == "te"

    def test_telugu_script_mixed(self):
        """Should detect Telugu even when mixed with numbers."""
        assert detect_language("నాకు 2 రోజులుగా జ్వరం") == "te"

    def test_romanized_telugu(self):
        """Should detect Romanized Telugu from keyword hints."""
        assert detect_language("naaku tala noppi ga undi") == "te"

    def test_romanized_telugu_single_hint(self):
        """Should detect from a single Telugu keyword."""
        assert detect_language("amma is not feeling well") == "te"

    def test_english(self):
        """Should detect English text."""
        assert detect_language("I have a headache") == "en"

    def test_empty_string(self):
        """Should fallback to English for empty input."""
        assert detect_language("") == "en"

    def test_whitespace(self):
        """Should fallback to English for whitespace-only input."""
        assert detect_language("   ") == "en"

    def test_numbers_only(self):
        """Should fallback to English for numbers only."""
        assert detect_language("123 456") == "en"
