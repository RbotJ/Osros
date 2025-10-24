"""High level navigation controller integrating minimap templates with routes."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .minimap import MinimapTemplateReader, RouteBuilder, RouteWaypoint


class NavigationController:
    """Generates waypoint sequences for high level navigation requests."""

    def __init__(
        self,
        template_directory: Path | str,
        route_overrides: Optional[Dict[str, Iterable[str]]] = None,
    ) -> None:
        self.template_directory = Path(template_directory)
        self.reader = MinimapTemplateReader(self.template_directory)
        self.builder = RouteBuilder(self.reader)
        self._route_cache: Dict[str, List[RouteWaypoint]] = {}
        self._route_overrides = {
            key.lower(): tuple(templates)
            for key, templates in (route_overrides or {}).items()
        }

    def list_templates(self) -> List[str]:
        return [template.name for template in self.reader.available_templates()]

    def plan_route(self, destination: str) -> List[RouteWaypoint]:
        """Return waypoint information for the requested destination."""
        route_key = destination.lower()
        if route_key in self._route_cache:
            return list(self._route_cache[route_key])

        override = self._route_overrides.get(route_key)
        if override:
            waypoints = self.builder.build_custom_route(override, description=f"Route to {destination.title()}")
        else:
            waypoints = self.builder.build_route(description=f"Route to {destination.title()}")
        self._route_cache[route_key] = waypoints
        return list(waypoints)

    def describe_route(self, destination: str) -> str:
        waypoints = self.plan_route(destination)
        if not waypoints:
            return f"No waypoint data available for {destination}."
        waypoint_descriptions = ", ".join(f"{wp.order}:{wp.template.name}" for wp in waypoints)
        return f"Route {destination.title()} -> {waypoint_descriptions}"
