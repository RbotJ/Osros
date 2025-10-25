"""Automation task controller for orchestrating asynchronous RuneLabs actions."""
from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Callable, Dict, Optional


@dataclass
class TaskStatus:
    """Represents the current state of a managed automation task."""

    name: str
    message: str
    progress: float
    state: str
    category: str
    error: Optional[str] = None


@dataclass
class _TaskDescriptor:
    name: str
    category: str
    func: Callable[[threading.Event, Callable[[str, Optional[float]], None], Optional[str]], None]


@dataclass
class _RunningTask:
    thread: threading.Thread
    stop_event: threading.Event


class AutomationController:
    """Coordinates asynchronous automation tasks and their lifecycle."""

    def __init__(self) -> None:
        self._tasks: Dict[str, _TaskDescriptor] = {}
        self._running: Dict[str, _RunningTask] = {}
        self._lock = threading.Lock()

    def register_task(
        self,
        name: str,
        func: Callable[[threading.Event, Callable[[str, Optional[float]], None], Optional[str]], None],
        *,
        category: str = "general",
    ) -> None:
        """Register a callable task with the controller."""

        with self._lock:
            if name in self._tasks:
                raise ValueError(f"Task '{name}' is already registered")
            self._tasks[name] = _TaskDescriptor(name=name, category=category, func=func)

    def start_task(
        self,
        name: str,
        *,
        user: Optional[str] = None,
        callback: Optional[Callable[[TaskStatus], None]] = None,
    ) -> None:
        """Start the task identified by ``name`` in a background thread."""

        with self._lock:
            descriptor = self._tasks.get(name)
            if descriptor is None:
                raise ValueError(f"Task '{name}' is not registered")

            running = self._running.get(name)
            if running and running.thread.is_alive():
                raise RuntimeError(f"Task '{name}' is already running")

            stop_event = threading.Event()

            def _notify(status: TaskStatus) -> None:
                if callback is not None:
                    callback(status)

            def _run_task() -> None:
                try:
                    _notify(
                        TaskStatus(
                            name=descriptor.name,
                            message="Starting task",
                            progress=0.0,
                            state="running",
                            category=descriptor.category,
                        )
                    )

                    def _update(message: str, progress: Optional[float] = None) -> None:
                        _notify(
                            TaskStatus(
                                name=descriptor.name,
                                message=message,
                                progress=0.0 if progress is None else max(0.0, min(1.0, progress)),
                                state="running",
                                category=descriptor.category,
                            )
                        )

                    descriptor.func(stop_event, _update, user)

                    if stop_event.is_set():
                        _notify(
                            TaskStatus(
                                name=descriptor.name,
                                message="Task cancelled",
                                progress=0.0,
                                state="cancelled",
                                category=descriptor.category,
                            )
                        )
                    else:
                        _notify(
                            TaskStatus(
                                name=descriptor.name,
                                message="Task completed",
                                progress=1.0,
                                state="completed",
                                category=descriptor.category,
                            )
                        )
                except Exception as exc:  # pragma: no cover - defensive safety
                    _notify(
                        TaskStatus(
                            name=descriptor.name,
                            message="Task failed",
                            progress=0.0,
                            state="error",
                            category=descriptor.category,
                            error=str(exc),
                        )
                    )
                finally:
                    with self._lock:
                        self._running.pop(name, None)

            thread = threading.Thread(target=_run_task, name=f"automation-{name}", daemon=True)
            self._running[name] = _RunningTask(thread=thread, stop_event=stop_event)
            thread.start()

    def stop_task(self, name: str) -> bool:
        """Request cancellation of a running task."""

        with self._lock:
            running = self._running.get(name)
            if not running:
                return False
            running.stop_event.set()
            return True

    def stop_all(self) -> None:
        """Cancel all running tasks."""

        with self._lock:
            names = list(self._running.keys())
        for task_name in names:
            self.stop_task(task_name)

    def is_running(self, name: str) -> bool:
        with self._lock:
            running = self._running.get(name)
            return bool(running and running.thread.is_alive())

    def list_running(self) -> Dict[str, str]:
        """Return a mapping of running task names to their categories."""

        with self._lock:
            running: Dict[str, str] = {}
            for name, descriptor in self._tasks.items():
                task = self._running.get(name)
                if task and task.thread.is_alive():
                    running[name] = descriptor.category
            return running
