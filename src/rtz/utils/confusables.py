"""Utilities for detecting Unicode confusables in strings."""

from __future__ import annotations

import unicodedata as ud


def has_confusables(s: str) -> bool:
    """Return whether the supplied string contains Unicode confusables.

    Args:
        s: Text to analyze for potentially deceptive glyphs.

    Returns:
        ``True`` when the normalized variant introduces combining marks.
    """
    normalized = ud.normalize("NFKD", s)
    return normalized != s and any(ud.category(ch).startswith("M") for ch in normalized)
