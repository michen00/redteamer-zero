"""RedTeamer Zero stub model implementations for deterministic testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GenerationResult:
    """Container for deterministic generation outputs."""

    text: str
    raw: dict[str, Any]


class StubModel:
    """Deterministic echo model for tests and golden runs."""

    name: str = "stub:echo"

    def generate(self, prompt: str, **_: dict[str, Any]) -> str:
        """Return a stubbed response for the supplied prompt.

        Args:
            prompt: User input to echo in the response.

        Returns:
            String containing the `prompt` annotated with the stub name.
        """
        return f"[stub:{self.name}] {prompt}"
