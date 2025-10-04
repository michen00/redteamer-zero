"""Regex-based judge utilities for scoring model outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern


@dataclass
class Decision:
    """Structured result produced by `RuleJudge`."""

    label: str
    reason: str | None = None


class RuleJudge:
    """Simple regex-any judge that flags the first matching pattern as success."""

    def __init__(self, patterns: list[str]) -> None:
        """Compile input patterns for later evaluation.

        Args:
            patterns: List of regular expressions to test against text.
        """
        self._patterns: list[Pattern[str]] = [re.compile(p) for p in patterns]

    def evaluate(self, text: str) -> Decision:
        """Evaluate ``text`` against configured regex patterns.

        Args:
            text: Candidate response to inspect.

        Returns:
            `Decision` describing whether a pattern matched.
        """
        for pat in self._patterns:
            if pat.search(text):
                return Decision(label="SUCCESS", reason=f"matched:{pat.pattern}")
        return Decision(label="FAIL", reason="no-match")
