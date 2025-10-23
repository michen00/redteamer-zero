"""Regex-based judge utilities for scoring model outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern


@dataclass
class Decision:
    """Structured result produced by `RuleJudge`.

    Includes a numeric `score` used by higher-level tests where 0.0 is a
    passing/matched decision and 1.0 indicates failure/no-match.
    """

    label: str
    reason: str | None = None
    score: float = 1.0


class RuleJudge:
    """Regex-any judge that flags a matching pattern as success.

    Args:
        patterns: List of regular expressions to test against text.
        case_sensitive: If False, matching is performed case-insensitively.
    """

    def __init__(
        self,
        patterns: list[str] | None = None,
        case_sensitive: bool = True,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Create a RuleJudge.

        Accept a variety of call styles for compatibility with callers that pass
        keywords or extra arguments. ``patterns`` may be omitted or None which
        is treated as an empty list.
        """
        patterns = patterns or []
        flags = 0 if case_sensitive else re.IGNORECASE
        self._patterns: list[Pattern[str]] = [
            re.compile(p, flags=flags) for p in patterns
        ]

    def evaluate(self, text: str) -> Decision:
        """Evaluate ``text`` against configured regex patterns and return a Decision.

        Returns a Decision with label "PASS" when all configured patterns match
        (AND semantics, score 0.0). If no patterns are configured or any pattern
        does not match, returns "FAIL" (score 1.0).
        """
        # No patterns configured -> nothing to match
        if not self._patterns:
            return Decision(label="FAIL", reason="no-patterns", score=1.0)

        # AND semantics: all patterns must be present in the text
        matches = [bool(p.search(text)) for p in self._patterns]
        if all(matches):
            patterns_str = ",".join(p.pattern for p in self._patterns)
            return Decision(label="PASS", reason=f"matched:{patterns_str}", score=0.0)

        return Decision(label="FAIL", reason="no-match", score=1.0)
