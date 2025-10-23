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

    def __init__(self, patterns: list[str], case_sensitive: bool = True) -> None:
        flags = 0 if case_sensitive else re.IGNORECASE
        self._patterns: list[Pattern[str]] = [
            re.compile(p, flags=flags) for p in patterns
        ]

    def evaluate(self, text: str) -> Decision:
        """Evaluate ``text`` against configured regex patterns and return a Decision.

        Returns a Decision with label "SUCCESS" on first match (score 0.0) or
        "FAIL" when no pattern matches (score 1.0).
        """
        for pat in self._patterns:
            if pat.search(text):
                return Decision(
                    label="SUCCESS", reason=f"matched:{pat.pattern}", score=0.0
                )
        return Decision(label="FAIL", reason="no-match", score=1.0)
