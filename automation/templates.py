"""Template loading and matching helpers for automation routines."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

import cv2
import numpy as np


@dataclass
class TemplateMatch:
    """Result of a template match operation."""

    name: str
    center: Tuple[int, int]
    score: float


class TemplateLibrary:
    """Load and query OpenCV templates from disk."""

    def __init__(self, template_dir: str, threshold: float = 0.9) -> None:
        self.template_dir = template_dir
        self.threshold = threshold
        self.templates: Dict[str, np.ndarray] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        for filename in os.listdir(self.template_dir):
            path = os.path.join(self.template_dir, filename)
            if not os.path.isfile(path):
                continue
            template = cv2.imread(path, 0)
            if template is None:
                continue
            self.templates[filename] = template

    def match_first(
        self,
        grayscale: np.ndarray,
        *,
        prefixes: Iterable[str],
    ) -> Optional[TemplateMatch]:
        """Return the first matching template with the given prefixes."""

        for template_name in sorted(self.templates):
            if not any(template_name.startswith(prefix) for prefix in prefixes):
                continue
            match = self._match_template(template_name, grayscale)
            if match is not None:
                return match
        return None

    def _match_template(
        self, template_name: str, grayscale: np.ndarray
    ) -> Optional[TemplateMatch]:
        template = self.templates[template_name]
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(grayscale, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= self.threshold)
        for pt in zip(*loc[::-1]):
            center = (pt[0] + w // 2, pt[1] + h // 2)
            score = float(res[pt[1], pt[0]])
            return TemplateMatch(name=template_name, center=center, score=score)
        return None


__all__ = ["TemplateLibrary", "TemplateMatch"]
