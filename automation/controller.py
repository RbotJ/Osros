"""Automation controller with task lifecycle + navigation/perception state."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

# Optional deps; keep imports local-friendly for testability
try:
    from navigation.controller import NavigationController
    from navigation.minimap import RouteWaypoint
except Exception:  # pragma: no cover - optional in some runtimes
    NavigationController = Any  # type: ignore[misc,assignment]
    RouteWaypoint = Any  # type: ignore[misc,assignment]

try:
    from perception.inventory import InventoryDetection, TemplateInventoryRecognizer
except Exception:  # pragma: no cover - optional in some runtimes
    InventoryDetection = Any  # type: ignore[misc,assignment]
    TemplateInventoryRecognizer = Any  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


# ---------- Shared automation state (from codex branch) ----------
@dataclass
class AutomationState:
    """Holds shared automation state for downstream systems."""
    destination: Optional[str] = None
    planned_route: List[RouteWaypoint] = field(default_factory=list)
    inventory_detections: List[InventoryDetection] = field(default_factory=list)


# ---------- Task lifecycle (from master) ----------
class AutomationTask:
    """Base task that can be orchestrated by :class:`AutomationController`."""

    def __init__(self, name: str) -> None:
        self.name = name

    def on_start(self, context: Dict[str, Any]) -> None:  # pragma: no cover - default no-op
        """Prepare the task before execution."""

    def perform_step(self, context: Dict[str, Any]) -> bool:  # pragma: no cover - default no-op
        """Perform a unit of work.
        Return True if more work remains; False to end the lifecycle.
        """
        return False

    def on_stop(self, context: Dict[str, Any]) -> None:  # pragma: no cover - default no-op
        """Clean up any resources associated with the task."""


class AutomationController:
    """Coordinates automation tasks and exposes navigation/perception helpers."""

    def __init__(
        self,
        window_api: Any | None = None,
        input_api: Any | None = None,
        *,
        navigation: NavigationController | None = None,
        inventory_recognizer: TemplateInventoryRecognizer | None = None,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        # I/O deps for GUI/automation tasks
        self.window_api = window_api
        self.input_api = input_api

        # Optional higher-level deps
        self.navigation = navigation
        self.inventory_recognizer = inventory_recognizer

        # Shared state
        self.state = AutomationState()

        # Infra
        self._logger = logger_instance or logger
        self._tasks: Dict[str, AutomationTask] = {}

    # ----- Task registry/lifecycle (preserves master behavior) -----
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
        context: Dict[str, Any] = {
            "window_api": self.window_api,
            "input_api": self.input_api,
            "navigation": self.navigation,
            "inventory_recognizer": self.inventory_recognizer,
            "state": self.state,
            "logger": self._logger,
        }

        self._logger.info("Starting task", extra={"task": task_name})
        task.on_start(context)
        step_index = 0
        try:
            while True:
                self._logger.debug(
                    "Performing task step", extra={"task": task_name, "step": step_index}
                )
                step_index += 1
                if not task.perform_step(context):
                    break
        finally:
            self._logger.info("Stopping task", extra={"task": task_name})
            task.on_stop(context)

        return context

    # ----- Navigation/perception facade (from codex branch) -----
    def plan_route(self, destination: str) -> List[RouteWaypoint]:
        nav = self._require_navigation()
        route = nav.plan_route(destination)
        self.state.destination = destination
        self.state.planned_route = list(route)
        return list(route)

    def describe_route(self, destination: str) -> str:
        nav = self._require_navigation()
        return nav.describe_route(destination)

    def refresh_inventory(self, image: Any) -> List[InventoryDetection]:
        if image is None:
            self.state.inventory_detections = []
            return []
        rec = self._require_inventory()
        detections = rec.detect_from_image(image)
        self.state.inventory_detections = list(detections)
        return list(detections)

    def last_inventory(self) -> List[InventoryDetection]:
        return list(self.state.inventory_detections)

    # ----- Dependency guards -----
    def _require_navigation(self) -> NavigationController:
        if self.navigation is None:
            raise RuntimeError("NavigationController not configured on AutomationController")
        return self.navigation

    def _require_inventory(self) -> TemplateInventoryRecognizer:
        if self.inventory_recognizer is None:
            raise RuntimeError("TemplateInventoryRecognizer not configured on AutomationController")
        return self.inventory_recognizer


__all__ = ["AutomationController", "AutomationTask", "AutomationState"]
