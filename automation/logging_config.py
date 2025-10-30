"""Utilities for configuring structured logging across automation modules."""

from __future__ import annotations

import logging
from typing import Optional

from utils.log_sanitizer import SensitiveDataFilter

STRUCTURED_LOG_FORMAT = (
    "timestamp=%(asctime)s level=%(levelname)s logger=%(name)s message=\"%(message)s\""
)


def _ensure_sanitizer(root_logger: logging.Logger) -> None:
    """Attach the sensitive data filter once to the root logger."""

    if not any(isinstance(f, SensitiveDataFilter) for f in root_logger.filters):
        root_logger.addFilter(SensitiveDataFilter())


def configure_logging(level: int = logging.INFO, handler: Optional[logging.Handler] = None) -> None:
    """Configure structured logging for the application.

    The configuration is idempotent: if logging has already been configured, the
    root logger level is updated while preserving existing handlers.
    """

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=level, format=STRUCTURED_LOG_FORMAT)
    else:
        root_logger.setLevel(level)

    _ensure_sanitizer(root_logger)

    if handler and handler not in root_logger.handlers:
        root_logger.addHandler(handler)

    logging.captureWarnings(True)


__all__ = ["configure_logging", "STRUCTURED_LOG_FORMAT"]
