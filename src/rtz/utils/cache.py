"""File-based cache utilities for storing model interaction results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .redact import redact


class FileCache:
    """Persist deterministic cache entries scoped by provider, model, and prompt."""

    def __init__(self, root: Path | str) -> None:
        """Initialize the cache at the provided root directory.

        Args:
            root: Filesystem location backing the cache entries.
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _key(self, provider: str, model: str, prompt: str) -> str:
        """Create a stable hash key for the cache entry.

        Args:
            provider: Identifier for the API provider.
            model: Model name or version string.
            prompt: Prompt text to hash (redacted prior to hashing).

        Returns:
            Hex-encoded SHA256 digest.
        """
        h = hashlib.sha256()
        h.update(provider.encode())
        h.update(b"::")
        h.update(model.encode())
        h.update(b"::")
        h.update(redact(prompt).encode())
        return h.hexdigest()

    def get(self, provider: str, model: str, prompt: str) -> object | None:
        """Retrieve a cached value if present.

        Args:
            provider: Identifier for the API provider.
            model: Model name or version string.
            prompt: Prompt text used during caching.

        Returns:
            Cached payload or ``None`` when no entry exists.
        """
        key = self._key(provider, model, prompt)
        p = self.root / f"{key}.json"
        if not p.exists():
            return None
        cached: object = json.loads(p.read_text(encoding="utf-8"))
        return cached

    def set(self, provider: str, model: str, prompt: str, value: object) -> None:
        """Store a value in the cache.

        Args:
            provider: Identifier for the API provider.
            model: Model name or version string.
            prompt: Prompt text used during caching.
            value: JSON-serializable payload to persist.
        """
        key = self._key(provider, model, prompt)
        p = self.root / f"{key}.json"
        p.write_text(json.dumps(value), encoding="utf-8")
