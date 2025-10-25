"""Utilities for loading user profiles and masking sensitive values."""
from __future__ import annotations

import getpass
import logging
import os
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Sequence

import keyring
from dotenv import dotenv_values, find_dotenv, load_dotenv
from keyring.errors import KeyringError

DEFAULT_KEYRING_SERVICE = "Osros"


@dataclass
class UserProfile:
    """Profile metadata required for an automation login."""

    identifier: str
    username: str
    login: str
    service_name: str

    def resolve_password(self) -> str:
        """Retrieve or securely prompt for the password associated with this login."""

        try:
            password = keyring.get_password(self.service_name, self.login)
        except KeyringError as exc:  # pragma: no cover - depends on host OS
            raise RuntimeError(
                f"Unable to access credential store '{self.service_name}': {exc}"
            ) from exc

        if password is None:
            prompt = (
                "No password stored for "
                f"{self.identifier} ({_mask_value(self.login)}). "
                "Enter it now to save it securely: "
            )
            password = getpass.getpass(prompt)
            if not password:
                raise RuntimeError(
                    "A password is required to continue. Rerun the automation "
                    "after providing credentials."
                )
            keyring.set_password(self.service_name, self.login, password)
        return password


def _mask_value(value: str) -> str:
    if not value:
        return value
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"


def _load_env_values() -> Dict[str, str]:
    env_path = os.getenv("OSROS_ENV_FILE") or find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)
        return dotenv_values(env_path)
    load_dotenv()
    values: Dict[str, str] = {}
    for key, value in os.environ.items():
        if key.startswith("USER") and key[len("USER"):].isdigit():
            values[key] = value
        elif key.startswith("LOGIN") and key[len("LOGIN"):].isdigit():
            values[key] = value
    return values


def _scrub_message(message: str, tokens: Iterable[str]) -> str:
    scrubbed = message
    for token in tokens:
        if token:
            scrubbed = scrubbed.replace(token, _mask_value(token))
    return scrubbed


class CredentialManager:
    """Coordinate loading user profiles and logging without leaking secrets."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or self._build_default_logger()
        self._users: Dict[str, UserProfile] = {}

    @staticmethod
    def _build_default_logger() -> logging.Logger:
        logger = logging.getLogger("osros.credentials")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def read_users(self) -> Dict[str, UserProfile]:
        env_values = _load_env_values()
        service_name = os.getenv("OSROS_KEYRING_SERVICE", DEFAULT_KEYRING_SERVICE)

        users: Dict[str, UserProfile] = {}
        for key, value in env_values.items():
            if not key.startswith("USER") or not value:
                continue

            suffix = key[len("USER"):]
            if suffix and not suffix.isdigit():
                continue
            login_key = f"LOGIN{suffix}"
            login_value = env_values.get(login_key) or os.getenv(login_key) or value
            identifier = f"User{suffix or '1'}"
            profile = UserProfile(
                identifier=identifier,
                username=value,
                login=login_value,
                service_name=service_name,
            )
            users[identifier] = profile

        if not users:
            raise RuntimeError(
                "No user profiles found. Ensure your .env file defines entries like "
                "USER1=YourDisplayName and LOGIN1=your@email.com."
            )

        self._users = users
        return users

    def select_active_user(
        self, users: Dict[str, UserProfile], candidate: Optional[str] = None
    ) -> str:
        if not users:
            raise RuntimeError("At least one user profile must be configured.")

        if candidate:
            if candidate not in users:
                raise RuntimeError(
                    f"Active user '{candidate}' is not defined in the configuration."
                )
            return candidate

        env_user = os.getenv("ACTIVE_USER")
        if env_user:
            if env_user not in users:
                raise RuntimeError(
                    f"Active user '{env_user}' is not defined in the configuration."
                )
            return env_user

        return next(iter(users))

    def log_info(self, message: str, extra_sensitive: Optional[Iterable[str]] = None) -> None:
        tokens = []
        for profile in self._users.values():
            tokens.append(profile.username)
            tokens.append(profile.login)
        if extra_sensitive:
            tokens.extend(extra_sensitive)
        self.logger.info(_scrub_message(message, tokens))

    @staticmethod
    def candidate_from_argv(argv: Sequence[str]) -> Optional[str]:
        return argv[1] if len(argv) > 1 else None


__all__ = ["CredentialManager", "UserProfile"]
