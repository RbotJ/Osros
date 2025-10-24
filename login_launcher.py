"""Utility helpers for launching the legacy Login automation subprocess."""
from __future__ import annotations

import io
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional


class LoginLaunchError(RuntimeError):
    """Raised when the Login automation process fails to start."""


class LoginLauncher:
    """Launches and monitors the ``Login.py`` automation module."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen[str]] = None
        self._stderr_buffer = io.StringIO()
        self._stderr_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def launch(self, account_key: str) -> subprocess.Popen[str]:
        """Start the Login script for the provided account key."""

        with self._lock:
            if self._process and self._process.poll() is None:
                raise LoginLaunchError("The login automation is already running")

            script_path = Path(__file__).with_name("Login.py")
            if not script_path.exists():
                raise LoginLaunchError(f"Could not locate Login.py at {script_path}")

            command = [sys.executable, str(script_path), account_key]

            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=script_path.parent,
                )
            except OSError as exc:
                raise LoginLaunchError(f"Failed to start login automation: {exc}") from exc

            self._stderr_buffer = io.StringIO()
            if process.stderr is not None:
                self._stderr_thread = threading.Thread(
                    target=self._collect_stderr,
                    args=(process.stderr,),
                    daemon=True,
                )
                self._stderr_thread.start()
            else:
                self._stderr_thread = None

            self._process = process
            return process

    def poll(self) -> Optional[int]:
        process = self._process
        if process is None:
            return None
        return process.poll()

    def terminate(self) -> None:
        with self._lock:
            process = self._process
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            self._process = None

    def consume_stderr(self) -> str:
        with self._lock:
            contents = self._stderr_buffer.getvalue()
            self._stderr_buffer = io.StringIO()
            return contents

    def _collect_stderr(self, stream: io.TextIOBase) -> None:
        try:
            for line in stream:
                with self._lock:
                    self._stderr_buffer.write(line)
        finally:
            stream.close()

    @property
    def process(self) -> Optional[subprocess.Popen[str]]:
        return self._process
