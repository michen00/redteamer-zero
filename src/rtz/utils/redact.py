"""Helpers to redact sensitive information from text snippets."""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://\\S+")
SECRET_RE = re.compile(r"(?i)(api[_-]?key|secret|token)[:=]\\s*\\S+")


def redact(text: str) -> str:
    """Obfuscate emails, URLs, and obvious secrets in ``text``.

    Args:
        text: Input string that may contain sensitive tokens.

    Returns:
        Redacted string with matching patterns replaced by placeholders.
    """
    return SECRET_RE.sub(
        "[REDACTED_SECRET]",
        URL_RE.sub("[REDACTED_URL]", EMAIL_RE.sub("[REDACTED_EMAIL]", text)),
    )
