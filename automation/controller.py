"""Core automation controller that integrates navigation and perception modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from navigation.controller import NavigationController
from navigation.minimap import RouteWaypoint
from perception.inventory import InventoryDetection, TemplateInventoryRecognizer


@dataclass
class AutomationState:
    """Holds shared automation state for downstream systems."""

    destination: Optional[str] = None
    planned_route: List[RouteWaypoint] = field(default_factory=list)
    inventory_detections: List[InventoryDetection] = field(default_factory=list)


class AutomationController:
    """Surface APIs for automation layers to coordinate navigation and perception."""

    def __init__(
        self,
        navigation: NavigationController,
        inventory_recognizer: TemplateInventoryRecognizer,
    ) -> None:
        self.navigation = navigation
        self.inventory_recognizer = inventory_recognizer
        self.state = AutomationState()

    def plan_route(self, destination: str) -> List[RouteWaypoint]:
        route = self.navigation.plan_route(destination)
        self.state.destination = destination
        self.state.planned_route = list(route)
        return list(route)

    def describe_route(self, destination: str) -> str:
        return self.navigation.describe_route(destination)

    def refresh_inventory(self, image) -> List[InventoryDetection]:
        if image is None:
            self.state.inventory_detections = []
            return []
        detections = self.inventory_recognizer.detect_from_image(image)
        self.state.inventory_detections = list(detections)
        return list(detections)

    def last_inventory(self) -> List[InventoryDetection]:
        return list(self.state.inventory_detections)


__all__ = ["AutomationController", "AutomationState"]
