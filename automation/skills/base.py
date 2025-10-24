"""Base abstractions for RuneLabs skill automation."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SkillTask(ABC):
    """Common interface for automatable skill tasks."""

    @abstractmethod
    def start(self) -> None:
        """Initialise resources required for the skill."""

    @abstractmethod
    def stop(self) -> None:
        """Release resources and stop any background workers."""

    @abstractmethod
    def update(self) -> None:
        """Execute a single iteration of the skill routine."""
