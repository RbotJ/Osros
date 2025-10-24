"""Quest task scaffolding built on top of the automation controller."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from .controller import AutomationController


QuestAction = Callable[[AutomationController], None]


@dataclass
class QuestStep:
    """Represents a single step within a quest flow."""

    name: str
    action: QuestAction
    description: Optional[str] = None

    def execute(self, controller: AutomationController) -> None:
        self.action(controller)


@dataclass
class QuestTask:
    """A sequence of quest steps that are run in order."""

    name: str
    steps: List[QuestStep]

    def run(self, controller: AutomationController) -> None:
        for step in self.steps:
            step.execute(controller)


class QuestOrchestrator:
    """Coordinates quest tasks using an automation controller."""

    def __init__(self, controller: AutomationController) -> None:
        self.controller = controller
        self._tasks: List[QuestTask] = []

    def register(self, task: QuestTask) -> None:
        self._tasks.append(task)

    def run_all(self) -> None:
        for task in self._tasks:
            task.run(self.controller)

    def plan_navigation_task(self, destination: str, auto_register: bool = False) -> QuestTask:
        """Convenience helper that creates a navigation oriented quest task."""

        def _navigate(ctrl: AutomationController) -> None:
            ctrl.plan_route(destination)

        step = QuestStep(name=f"Navigate to {destination}", action=_navigate)
        task = QuestTask(name=f"Travel to {destination}", steps=[step])
        if auto_register:
            self.register(task)
        return task


__all__ = ["QuestAction", "QuestStep", "QuestTask", "QuestOrchestrator"]
