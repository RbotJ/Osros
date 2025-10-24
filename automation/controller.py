"""Automation controller infrastructure with task lifecycle management."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable

logger = logging.getLogger(__name__)


class AutomationTask:
    """Base task that can be orchestrated by :class:`AutomationController`."""

    def __init__(self, name: str) -> None:
        self.name = name

    def on_start(self, context: Dict[str, Any]) -> None:  # pragma: no cover - default no-op
        """Prepare the task before execution."""

    def perform_step(self, context: Dict[str, Any]) -> bool:  # pragma: no cover - default no-op
        """Perform a unit of work.

        Returns ``True`` if more work remains, ``False`` to end the lifecycle.
        """

        return False

    def on_stop(self, context: Dict[str, Any]) -> None:  # pragma: no cover - default no-op
        """Clean up any resources associated with the task."""


class AutomationController:
    """Coordinates automation tasks while sharing window and input dependencies."""

    def __init__(self, window_api: Any, input_api: Any, *, logger_instance: logging.Logger | None = None) -> None:
        self.window_api = window_api
        self.input_api = input_api
        self._logger = logger_instance or logger
        self._tasks: Dict[str, AutomationTask] = {}

    def register_task(self, task: AutomationTask) -> None:
        if task.name in self._tasks:
            raise ValueError(f"Task '{task.name}' is already registered")

        self._tasks[task.name] = task
        self._logger.debug("Registered task", extra={"task": task.name})

    def registered_tasks(self) -> Iterable[str]:
        return tuple(self._tasks.keys())

    def run_task(self, task_name: str) -> Dict[str, Any]:
        if task_name not in self._tasks:
            raise KeyError(f"Task '{task_name}' is not registered")

        task = self._tasks[task_name]
        context = {"window_api": self.window_api, "input_api": self.input_api}
        self._logger.info("Starting task", extra={"task": task_name})
        task.on_start(context)

        step_index = 0
        try:
            while True:
                self._logger.debug(
                    "Performing task step",
                    extra={"task": task_name, "step": step_index},
                )
                step_index += 1
                should_continue = task.perform_step(context)
                if not should_continue:
                    break
        finally:
            self._logger.info("Stopping task", extra={"task": task_name})
            task.on_stop(context)

        return context


__all__ = ["AutomationController", "AutomationTask"]
