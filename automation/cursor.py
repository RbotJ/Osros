"""Human-like cursor movement utilities."""

from __future__ import annotations

import multiprocessing as mp
import random
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import pyautogui


@dataclass
class CursorAction:
    """Represents a cursor action to be executed by the worker."""

    position: Tuple[int, int]
    move_offset: int = 4
    move_delay_range: Tuple[float, float] = (0.1, 0.2)
    click_delay_range: Tuple[float, float] = (0.1, 0.6)
    post_click_delay: float = 4.0
    clicks: int = 1


class HumanLikeCursor:
    """Queue based helper that executes cursor actions in a background process."""

    def __init__(self) -> None:
        self._queue: "mp.Queue[Optional[CursorAction]]" = mp.Queue()
        self._process: Optional[mp.Process] = None

    def start(self) -> None:
        if self._process is None or not self._process.is_alive():
            self._process = mp.Process(target=_cursor_worker, args=(self._queue,))
            self._process.start()

    def stop(self) -> None:
        if self._process is not None:
            self._queue.put(None)
            self._process.join(timeout=1)
            if self._process.is_alive():
                self._process.terminate()
            self._process = None

    def queue_click(self, action: CursorAction) -> None:
        """Queue a click action to be executed by the worker."""

        self._queue.put(action)


def _cursor_worker(queue: "mp.Queue[Optional[CursorAction]]") -> None:
    while True:
        action = queue.get()
        if action is None:
            break
        x_offset = random.randint(-action.move_offset, action.move_offset)
        y_offset = random.randint(-action.move_offset, action.move_offset)
        move_delay = random.uniform(*action.move_delay_range)
        click_delay = random.uniform(*action.click_delay_range)

        time.sleep(move_delay)
        pyautogui.moveTo(action.position[0] + x_offset, action.position[1] + y_offset)

        time.sleep(click_delay)
        for _ in range(action.clicks):
            pyautogui.click()
        time.sleep(action.post_click_delay)


__all__ = ["CursorAction", "HumanLikeCursor"]
