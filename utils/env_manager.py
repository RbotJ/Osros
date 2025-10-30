"""Secure helpers for managing encrypted environment variables."""

from __future__ import annotations

import argparse
import base64
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Iterable
import uuid

logger = logging.getLogger(__name__)


class SecureEnvManager:
    """Manage plaintext and encrypted environment variable files.

    The manager keeps a plaintext ``.env`` for local editing while
    synchronising an encrypted ``.env.enc`` that is bound to the current
    machine via its MAC address. The encrypted file is used when loading
    credentials to avoid leaving secrets in process memory longer than
    necessary.
    """

    def __init__(
        self,
        plain_path: Path | str = Path(".env"),
        encrypted_path: Path | str = Path(".env.enc"),
    ) -> None:
        self.plain_path = Path(plain_path)
        self.encrypted_path = Path(encrypted_path)

    # ------------------------------------------------------------------
    # Encryption helpers
    # ------------------------------------------------------------------
    def _hardware_signature(self) -> str:
        """Return a stable signature for the current machine."""

        mac_int = uuid.getnode()
        return f"{mac_int:012x}"

    def _derive_key(self) -> bytes:
        signature = self._hardware_signature().encode("utf-8")
        return hashlib.sha256(signature).digest()

    @staticmethod
    def _xor_bytes(data: bytes, key: bytes) -> bytes:
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    def encrypt_text(self, plaintext: str) -> str:
        """Encrypt text using the derived hardware key."""

        key = self._derive_key()
        encrypted = self._xor_bytes(plaintext.encode("utf-8"), key)
        return base64.urlsafe_b64encode(encrypted).decode("utf-8")

    def decrypt_text(self, token: str) -> str:
        key = self._derive_key()
        encrypted = base64.urlsafe_b64decode(token.encode("utf-8"))
        decrypted = self._xor_bytes(encrypted, key)
        return decrypted.decode("utf-8")

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------
    def ensure_encrypted_copy(self) -> bool:
        """Create or refresh the encrypted copy of the plaintext file."""

        if not self.plain_path.exists():
            logger.debug("Plain .env file not found; skipping encryption step.")
            return False

        plaintext = self.plain_path.read_text(encoding="utf-8")
        token = self.encrypt_text(plaintext)
        self.encrypted_path.write_text(token, encoding="utf-8")
        logger.debug(
            "Encrypted credentials saved", extra={"path": str(self.encrypted_path)}
        )
        return True

    def load(self) -> Dict[str, str]:
        """Load environment values from the encrypted store.

        If the encrypted file is missing but a plaintext ``.env`` exists, it
        is encrypted automatically to keep local tooling convenient.
        """

        if self.encrypted_path.exists():
            logger.debug("Loading credentials from encrypted store.")
            encrypted = self.encrypted_path.read_text(encoding="utf-8")
            plaintext = self.decrypt_text(encrypted)
        elif self.plain_path.exists():
            logger.debug("Encrypted store missing; creating from plaintext .env.")
            self.ensure_encrypted_copy()
            plaintext = self.plain_path.read_text(encoding="utf-8")
        else:
            logger.warning("No credentials file found. Proceeding with empty env.")
            return {}

        return self._parse_env(plaintext)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_env(plaintext: str) -> Dict[str, str]:
        values: Dict[str, str] = {}
        for raw_line in plaintext.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        return values

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def export_environment(self, values: Dict[str, str]) -> None:
        """Set values in ``os.environ`` without overwriting existing keys."""

        for key, value in values.items():
            if key not in os.environ:
                os.environ[key] = value

    def get_user_credentials(self) -> Dict[str, Dict[str, str]]:
        """Return a mapping of user identifiers to their credentials."""

        values = self.load()
        self.export_environment(values)

        users: Dict[str, Dict[str, str]] = {}
        index = 1
        while True:
            prefix = f"USER{index}"
            username = values.get(f"{prefix}_USERNAME")
            password = values.get(f"{prefix}_PASSWORD")
            login = values.get(f"{prefix}_LOGIN")

            if not any((username, password, login)):
                break

            users[f"User{index}"] = {
                "username": username or "",
                "password": password or "",
                "login": login or "",
            }
            index += 1

        return users

    def iter_sensitive_values(self) -> Iterable[str]:
        """Yield sensitive values suitable for log masking."""

        values = self.load()
        index = 1
        while True:
            prefix = f"USER{index}"
            username = values.get(f"{prefix}_USERNAME")
            password = values.get(f"{prefix}_PASSWORD")
            login = values.get(f"{prefix}_LOGIN")

            if not any((username, password, login)):
                break

            yield from filter(None, (username, password, login))
            index += 1


def _run_cli(action: str) -> None:
    manager = SecureEnvManager()

    if action == "encrypt":
        if manager.ensure_encrypted_copy():
            print("Encrypted .env -> .env.enc")
        else:
            print("No .env file found; nothing encrypted.")
    elif action == "decrypt":
        if not manager.encrypted_path.exists():
            raise SystemExit("No encrypted file to decrypt.")
        plaintext = manager.decrypt_text(
            manager.encrypted_path.read_text(encoding="utf-8")
        )
        manager.plain_path.write_text(plaintext, encoding="utf-8")
        print("Decrypted .env.enc -> .env")
    else:
        raise SystemExit(f"Unsupported action: {action}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Manage encrypted .env files")
    parser.add_argument(
        "action",
        choices=("encrypt", "decrypt"),
        help="Encrypt the plaintext .env or decrypt the encrypted store",
    )
    args = parser.parse_args(argv)
    _run_cli(args.action)


if __name__ == "__main__":
    main()


__all__ = ["SecureEnvManager", "main"]
