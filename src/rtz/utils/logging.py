"""Structured logging utilities for RedTeamer Zero."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger


def configure_logging(level: str = "INFO", *, json: bool = True) -> None:
    """Configure structlog and stdlib logging handlers.

    Args:
        level: Desired log level name (e.g. ``"INFO"``).
        json: If ``True`` emit JSON records, otherwise pretty console output.
    """
    logging_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=logging_level, format="%(message)s")

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    renderer: structlog.typing.Processor
    if json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.EventRenamer("message"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "rtz") -> BoundLogger:
    """Return a structlog logger bound to ``name``.

    Args:
        name: Logical logger name used when emitting records.

    Returns:
        Configured structlog logger instance.
    """
    return structlog.get_logger(name)
