"""Window management utilities for RuneLabs automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import win32api
import win32con


@dataclass
class WindowGeometry:
    """Represents the geometry of a desktop window."""

    left: int
    top: int
    width: int
    height: int

    @property
    def region(self) -> Tuple[int, int, int, int]:
        """Return the region tuple compatible with ``pyautogui.screenshot``."""

        return (self.left, self.top, self.width, self.height)


class WindowCaptureService:
    """High level helper around ``pygetwindow`` for RuneLite automation."""

    def __init__(
        self,
        title: str,
        *,
        size_ratio: float = 0.5,
        position: Tuple[int, int] = (0, 0),
        manage_geometry: bool = True,
    ) -> None:
        self._title = title
        self._size_ratio = size_ratio
        self._position = position
        self._manage_geometry = manage_geometry
        self._window = self._get_window()
        self._preview_name: Optional[str] = None

    def _get_window(self):
        windows = gw.getWindowsWithTitle(self._title)
        if not windows:
            raise RuntimeError(f"Window with title '{self._title}' not found")
        return windows[0]

    def configure_preview(self, name: str) -> None:
        """Enable an OpenCV preview window to visualise captures."""

        self._preview_name = name
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)

    def _ensure_window_visible(self) -> None:
        if self._window.isMinimized:
            win32api.SendMessage(
                self._window._hWnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0
            )

    def _desired_geometry(self) -> WindowGeometry:
        screen_width, screen_height = pyautogui.size()
        new_width = int(screen_width * self._size_ratio)
        new_height = int(screen_height * self._size_ratio)
        return WindowGeometry(
            left=self._position[0],
            top=self._position[1],
            width=new_width,
            height=new_height,
        )

    def _current_geometry(self) -> WindowGeometry:
        return WindowGeometry(
            left=self._window.left,
            top=self._window.top,
            width=self._window.width,
            height=self._window.height,
        )

    def prepare_window(self) -> WindowGeometry:
        """Ensure the window is visible and optionally resized and positioned."""

        self._ensure_window_visible()
        if self._manage_geometry:
            geometry = self._desired_geometry()
            if self._window.width != geometry.width or self._window.height != geometry.height:
                self._window.resizeTo(geometry.width, geometry.height)
            self._window.moveTo(geometry.left, geometry.top)
        else:
            geometry = self._current_geometry()
        self._window.activate()
        if self._preview_name:
            cv2.resizeWindow(self._preview_name, geometry.width, geometry.height)
            cv2.moveWindow(self._preview_name, geometry.left, geometry.top)
        return geometry

    def capture(self) -> Tuple[np.ndarray, np.ndarray]:
        """Capture the window as colour and grayscale numpy arrays."""

        geometry = self.prepare_window()
        screenshot = pyautogui.screenshot(region=geometry.region)
        color = np.array(screenshot)
        grayscale = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
        if self._preview_name is not None:
            cv2.imshow(self._preview_name, color)
        return color, grayscale

    def close_preview(self) -> None:
        """Destroy the OpenCV preview window if one was created."""

        if self._preview_name is not None:
            cv2.destroyWindow(self._preview_name)
            self._preview_name = None


__all__ = ["WindowCaptureService", "WindowGeometry"]
