"""Centralised helpers for masking sensitive values in logs."""

from __future__ import annotations

import logging
import re
from typing import Iterable, MutableMapping

_MASK = "[REDACTED]"
_SENSITIVE_VALUES: set[str] = set()
_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def register_sensitive_values(values: Iterable[str]) -> None:
    """Register additional strings that should be masked in logs."""

    for value in values:
        if value:
            _SENSITIVE_VALUES.add(value)


def _mask_value(value: str) -> str:
    masked = value
    for secret in _SENSITIVE_VALUES:
        if secret:
            masked = masked.replace(secret, _MASK)
    masked = _EMAIL_PATTERN.sub(_MASK, masked)
    return masked


def sanitize(obj: object) -> object:
    """Sanitize values for log emission."""

    if isinstance(obj, str):
        return _mask_value(obj)
    if isinstance(obj, MutableMapping):
        return {key: sanitize(val) for key, val in obj.items()}
    if isinstance(obj, (tuple, list)):
        factory = list if isinstance(obj, list) else tuple
        return factory(sanitize(val) for val in obj)
    return obj


class SensitiveDataFilter(logging.Filter):
    """Logging filter that masks registered sensitive values."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - logging
        if isinstance(record.msg, str):
            record.msg = _mask_value(record.msg)
        if record.args:
            record.args = sanitize(record.args)

        for attr in ("username", "password", "login", "email"):
            if hasattr(record, attr):
                setattr(record, attr, _MASK)
        return True


__all__ = ["SensitiveDataFilter", "register_sensitive_values", "sanitize"]
