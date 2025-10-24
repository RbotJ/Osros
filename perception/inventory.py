"""Template-based inventory and object recognition pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np


@dataclass
class InventoryDetection:
    """Represents the result of a template match within the inventory region."""

    label: str
    location: Tuple[int, int]
    confidence: float
    template_path: Path

    def as_dict(self) -> Dict[str, object]:
        return {
            "label": self.label,
            "location": self.location,
            "confidence": self.confidence,
            "template_path": str(self.template_path),
        }


class TemplateInventoryRecognizer:
    """Perform template matching against screenshots to locate inventory objects."""

    def __init__(
        self,
        template_directory: Path | str,
        detection_threshold: float = 0.8,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        self.template_directory = Path(template_directory)
        self.detection_threshold = detection_threshold
        self.labels = labels or {}
        self._templates: Dict[str, Tuple[Path, np.ndarray]] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        if not self.template_directory.exists():
            return
        for path in self.template_directory.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
                continue
            image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if image is None:
                continue
            self._templates[path.stem] = (path, image)

    def detect_from_image(self, image: np.ndarray) -> List[InventoryDetection]:
        detections: List[InventoryDetection] = []
        if image is None or not self._templates:
            return detections
        for name, (path, template) in self._templates.items():
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val < self.detection_threshold:
                continue
            label = self.labels.get(name, name)
            detections.append(
                InventoryDetection(
                    label=label,
                    location=max_loc,
                    confidence=float(max_val),
                    template_path=path,
                )
            )
        return detections

    def detect_from_path(self, image_path: Path | str) -> List[InventoryDetection]:
        image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if image is None:
            return []
        return self.detect_from_image(image)

    def template_names(self) -> Sequence[str]:
        return tuple(self._templates.keys())


__all__ = ["InventoryDetection", "TemplateInventoryRecognizer"]
