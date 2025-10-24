"""Utilities for loading minimap templates and constructing waypoint data."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

import cv2
import numpy as np


@dataclass
class MinimapTemplate:
    """Represents a minimap template image used for route building."""

    name: str
    path: Path
    image: np.ndarray


class MinimapTemplateReader:
    """Loads minimap templates from disk for navigation routines."""

    def __init__(self, template_directory: Path | str, image_prefix: str = "Map") -> None:
        self.template_directory = Path(template_directory)
        self.image_prefix = image_prefix

    def available_templates(self) -> List[MinimapTemplate]:
        """Return a list of minimap templates sorted by inferred waypoint order."""
        templates: List[MinimapTemplate] = []
        for path in sorted(self._iter_template_paths(), key=self._sort_key):
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None:
                continue
            templates.append(MinimapTemplate(name=path.stem, path=path, image=image))
        return templates

    def _iter_template_paths(self) -> Iterator[Path]:
        if not self.template_directory.exists():
            return iter(())
        for path in self.template_directory.iterdir():
            if not path.is_file():
                continue
            if not path.stem.startswith(self.image_prefix):
                continue
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
                continue
            yield path

    @staticmethod
    def _sort_key(path: Path) -> tuple[int, str]:
        digits = ''.join(ch for ch in path.stem if ch.isdigit())
        return (int(digits) if digits else 0, path.stem)


@dataclass
class RouteWaypoint:
    """Simple data container describing a navigation waypoint."""

    order: int
    template: MinimapTemplate
    description: Optional[str] = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "order": self.order,
            "template_name": self.template.name,
            "template_path": str(self.template.path),
            "description": self.description,
        }


class RouteBuilder:
    """Builds waypoint sequences from minimap templates."""

    def __init__(self, reader: MinimapTemplateReader) -> None:
        self.reader = reader

    def build_route(self, description: Optional[str] = None) -> List[RouteWaypoint]:
        waypoints: List[RouteWaypoint] = []
        for index, template in enumerate(self.reader.available_templates(), start=1):
            waypoint_description = description if description else f"Waypoint {index}"
            waypoints.append(RouteWaypoint(order=index, template=template, description=waypoint_description))
        return waypoints

    def build_custom_route(self, template_names: Iterable[str], description: Optional[str] = None) -> List[RouteWaypoint]:
        template_map = {template.name: template for template in self.reader.available_templates()}
        waypoints: List[RouteWaypoint] = []
        for index, name in enumerate(template_names, start=1):
            template = template_map.get(name)
            if template is None:
                continue
            waypoint_description = description if description else f"Waypoint {index}"
            waypoints.append(RouteWaypoint(order=index, template=template, description=waypoint_description))
        return waypoints
