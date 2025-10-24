"""Agility skill automation routine."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from ..cursor import CursorAction, HumanLikeCursor
from ..templates import TemplateLibrary, TemplateMatch
from ..window import WindowCaptureService
from .base import SkillTask
from . import register_skill


@dataclass
class DecisionOutcome:
    """Represents the result of a decision made by the agility engine."""

    handled: bool
    message: Optional[str] = None
    click_position: Optional[tuple[int, int]] = None
    post_delay: float = 0.0


class AgilityDecisionEngine:
    """Encapsulates the stateful decision logic for agility courses."""

    def __init__(self, template_library: TemplateLibrary) -> None:
        self._templates = template_library
        self.current_map: Optional[str] = None
        self.clicks_to_spend = 0

    def evaluate(self, grayscale: np.ndarray) -> DecisionOutcome:
        if self.clicks_to_spend == 0:
            match = self._templates.match_first(grayscale, prefixes=("Map",))
            if match:
                self.current_map = match.name
                self.clicks_to_spend = 1
                return DecisionOutcome(True, f"Minimap state recognized: {match.name}")

        if self.clicks_to_spend > 0:
            mog_match = self._templates.match_first(grayscale, prefixes=("Mog",))
            if mog_match:
                self.clicks_to_spend += 1
                return DecisionOutcome(
                    True,
                    f"Mark of grace recognized: {mog_match.name}",
                    mog_match.center,
                    post_delay=2.0,
                )

            click_match = self._templates.match_first(grayscale, prefixes=("Clm", "Clk", "Cl"))
            if click_match:
                self.clicks_to_spend = max(0, self.clicks_to_spend - 1)
                message = self._message_for_click(click_match)
                return DecisionOutcome(
                    True,
                    message,
                    click_match.center,
                    post_delay=3.0,
                )

        return DecisionOutcome(False)

    @staticmethod
    def _message_for_click(match: TemplateMatch) -> str:
        if match.name.startswith("Clm"):
            return f"Click of grace recognized: {match.name}"
        if match.name.startswith("Clk"):
            return f"Click point recognized: {match.name}"
        return f"Click recognized: {match.name}"


class AgilitySkill(SkillTask):
    """Implements the agility routine using the shared services."""

    def __init__(self, template_dir: str = "Agility/Canifis/", window_title: str = "RuneLite") -> None:
        self._window_service = WindowCaptureService(window_title)
        self._window_service.configure_preview("RuneLite Capture")
        self._templates = TemplateLibrary(template_dir)
        self._cursor = HumanLikeCursor()
        self._decision_engine = AgilityDecisionEngine(self._templates)
        self._running = False

    def start(self) -> None:
        self._cursor.start()
        self._running = True

    def stop(self) -> None:
        self._running = False
        self._cursor.stop()
        self._window_service.close_preview()
        cv2.destroyAllWindows()

    def update(self) -> None:
        if not self._running:
            return
        try:
            color, grayscale = self._window_service.capture()
        except RuntimeError as exc:
            print(f"Window capture failed: {exc}")
            time.sleep(1)
            return

        outcome = self._decision_engine.evaluate(grayscale)
        if outcome.handled:
            if outcome.message:
                print(outcome.message)
            if outcome.click_position:
                self._cursor.queue_click(CursorAction(position=outcome.click_position))
            if outcome.post_delay:
                time.sleep(outcome.post_delay)
        else:
            print("No state recognized: Waiting")
        time.sleep(0.1)


register_skill("agility", AgilitySkill)


__all__ = ["AgilitySkill", "AgilityDecisionEngine", "DecisionOutcome"]
