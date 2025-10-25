import numpy as np
import pytest

import Agility


class FakeQueue:
    def __init__(self):
        self.items = []

    def put(self, value):
        self.items.append(value)


@pytest.fixture(autouse=True)
def disable_sleep(monkeypatch):
    monkeypatch.setattr(Agility.time, "sleep", lambda *args, **kwargs: None)
    yield


def test_make_decision_updates_map_when_no_clicks(monkeypatch):
    templates = {"Map1.png": np.zeros((2, 2), dtype=np.uint8)}
    queue = FakeQueue()

    def fake_find(template_name, template, grayscale, screenshot):
        if template_name == "Map1.png":
            return "Minimap state recognized: Map1.png", (5, 5)
        return None, None

    monkeypatch.setattr(Agility, "find_template", fake_find)

    recognized, current_map, clicks = Agility.make_decision(
        templates,
        np.zeros((5, 5), dtype=np.uint8),
        np.zeros((5, 5), dtype=np.uint8),
        queue,
        current_map=None,
        clicks_to_spend=0,
        sleep_func=lambda *_: None,
    )

    assert recognized is True
    assert current_map == "Map1.png"
    assert clicks == 1
    assert queue.items == []


def test_make_decision_clickpoint_consumes_click(monkeypatch):
    templates = {"Clk1.png": np.zeros((2, 2), dtype=np.uint8)}
    queue = FakeQueue()

    def fake_find(template_name, template, grayscale, screenshot):
        if template_name.startswith("Clk"):
            return "Click point recognized", (10, 10)
        return None, None

    monkeypatch.setattr(Agility, "find_template", fake_find)

    recognized, current_map, clicks = Agility.make_decision(
        templates,
        np.zeros((5, 5), dtype=np.uint8),
        np.zeros((5, 5), dtype=np.uint8),
        queue,
        current_map="Map1.png",
        clicks_to_spend=1,
        sleep_func=lambda *_: None,
    )

    assert recognized is True
    assert current_map == "Map1.png"
    assert clicks == 0
    assert queue.items == [(10, 10)]


def test_make_decision_mark_of_grace_adds_click(monkeypatch):
    templates = {"Mog1.png": np.zeros((2, 2), dtype=np.uint8)}
    queue = FakeQueue()

    def fake_find(template_name, template, grayscale, screenshot):
        if template_name.startswith("Mog"):
            return "Mark of grace recognized", (7, 7)
        return None, None

    monkeypatch.setattr(Agility, "find_template", fake_find)

    recorded_sleep = []

    def fake_sleep(duration):
        recorded_sleep.append(duration)

    recognized, current_map, clicks = Agility.make_decision(
        templates,
        np.zeros((5, 5), dtype=np.uint8),
        np.zeros((5, 5), dtype=np.uint8),
        queue,
        current_map="Map1.png",
        clicks_to_spend=1,
        sleep_func=fake_sleep,
    )

    assert recognized is True
    assert clicks == 2  # existing click + bonus click
    assert queue.items == [(7, 7)]
    assert recorded_sleep == [2]


class DummyWindow:
    def __init__(self):
        self.width = 200
        self.height = 200
        self.left = 0
        self.top = 0
        self.isMinimized = False
        self._hWnd = 1234
        self.resize_calls = []
        self.move_calls = []
        self.activated = False

    def resizeTo(self, width, height):
        self.resize_calls.append((width, height))
        self.width = width
        self.height = height

    def moveTo(self, x, y):
        self.move_calls.append((x, y))
        self.left = x
        self.top = y

    def activate(self):
        self.activated = True


class DummyProcess:
    def __init__(self, *_, **__):
        self.started = False
        self.terminated = False

    def start(self):
        self.started = True

    def terminate(self):
        self.terminated = True


class DummyQueue:
    def __init__(self, *_, **__):
        self.items = []

    def put(self, item):
        self.items.append(item)


class FakeScreenshot:
    def __init__(self):
        self._data = np.zeros((10, 10, 3), dtype=np.uint8)

    def __array__(self, dtype=None):
        return self._data.astype(dtype) if dtype else self._data


def test_main_resizes_window_with_mocked_handle(monkeypatch):
    dummy_window = DummyWindow()

    monkeypatch.setattr(Agility.gw, "getWindowsWithTitle", lambda title: [dummy_window])
    monkeypatch.setattr(Agility.pyautogui, "size", lambda: (800, 600))
    monkeypatch.setattr(Agility.pyautogui, "screenshot", lambda **_: FakeScreenshot())
    monkeypatch.setattr(Agility.pyautogui, "moveTo", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agility.pyautogui, "click", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agility.win32api, "SendMessage", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agility.cv2, "namedWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agility.cv2, "resizeWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agility.cv2, "moveWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agility.cv2, "imshow", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agility.cv2, "waitKey", lambda *args, **kwargs: ord('q'))
    monkeypatch.setattr(Agility.cv2, "destroyAllWindows", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agility.cv2, "cvtColor", lambda *args, **kwargs: np.zeros((10, 10), dtype=np.uint8))
    monkeypatch.setattr(Agility, "make_decision", lambda *args, **kwargs: (False, None, 0))
    monkeypatch.setattr(Agility.mp, "Process", lambda *args, **kwargs: DummyProcess())
    monkeypatch.setattr(Agility.mp, "Queue", lambda *args, **kwargs: DummyQueue())
    monkeypatch.setattr(Agility.time, "sleep", lambda *args, **kwargs: None)

    Agility.main()

    assert dummy_window.resize_calls[0] == (400, 300)
    assert dummy_window.move_calls[0] == (0, 0)
    assert dummy_window.activated is True
