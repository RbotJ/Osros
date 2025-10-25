"""Agility skill automation routine."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

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

    def __init__(
        self,
        template_dir: str = "Agility/Canifis/",
        window_title: str = "RuneLite",
        *,
        window_service: Optional[WindowCaptureService] = None,
        template_library: Optional[TemplateLibrary] = None,
        cursor: Optional[HumanLikeCursor] = None,
        decision_engine: Optional[AgilityDecisionEngine] = None,
        enable_preview: bool = True,
        preview_name: str = "RuneLite Capture",
        manage_window_geometry: bool = True,
    ) -> None:
        self._window_service = window_service or WindowCaptureService(
            window_title, manage_geometry=manage_window_geometry
        )
        self._preview_name = preview_name if enable_preview else None
        self._preview_configured = False

        self._templates = template_library or TemplateLibrary(template_dir)
        self._cursor = cursor or HumanLikeCursor()
        self._own_cursor = cursor is None
        self._cursor_started = False
        self._decision_engine = decision_engine or AgilityDecisionEngine(self._templates)
        self._running = False

    def start(self) -> None:
        if self._preview_name and not self._preview_configured:
            self._window_service.configure_preview(self._preview_name)
            self._preview_configured = True
        if not self._cursor_started:
            self._cursor.start()
            self._cursor_started = True
        self._running = True

    def stop(self) -> None:
        self._running = False
        if self._own_cursor and self._cursor_started:
            self._cursor.stop()
        self._cursor_started = False
        if self._preview_configured and self._preview_name is not None:
            self._window_service.close_preview()
            self._preview_configured = False

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
