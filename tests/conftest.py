import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:  # pragma: no cover - prefer real numpy when available
    import numpy  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for test environment
    numpy = types.ModuleType("numpy")

    class _FakeArray(list):
        @property
        def shape(self):
            def _shape(data):
                if isinstance(data, list) and data:
                    inner = _shape(data[0])
                    return (len(data),) + inner
                if isinstance(data, list):
                    return (0,)
                return ()

            return _shape(self)

        def __array__(self, dtype=None):
            return self

    def _build_array(shape, fill=0):
        if not shape:
            return fill
        size = shape[0]
        rest = shape[1:]
        return _FakeArray([_build_array(rest, fill) for _ in range(size)])

    def array(data, dtype=None):  # noqa: D401 - mimic numpy signature
        if isinstance(data, _FakeArray):
            return data
        if isinstance(data, list):
            fake = _FakeArray(data)
        else:
            fake = _FakeArray([data])
        return fake

    def zeros(shape, dtype=None):
        return _build_array(shape, 0)

    def where(condition):
        return (_FakeArray([]), _FakeArray([]))

    numpy.array = array
    numpy.zeros = zeros
    numpy.where = where
    numpy.uint8 = int

    sys.modules["numpy"] = numpy


def _ensure_module(name, attributes):
    module = types.ModuleType(name)
    for attr, value in attributes.items():
        setattr(module, attr, value)
    sys.modules[name] = module
    return module


if "cv2" not in sys.modules:  # pragma: no cover - provide lightweight stub
    def _match_template(*args, **kwargs):
        return numpy.zeros((0, 0))

    _ensure_module(
        "cv2",
        {
            "TM_CCOEFF_NORMED": 0,
            "WINDOW_AUTOSIZE": 1,
            "WINDOW_NORMAL": 0,
            "matchTemplate": _match_template,
            "imread": lambda *args, **kwargs: numpy.zeros((1, 1)),
            "rectangle": lambda *args, **kwargs: None,
            "cvtColor": lambda image, code: image,
            "namedWindow": lambda *args, **kwargs: None,
            "resizeWindow": lambda *args, **kwargs: None,
            "moveWindow": lambda *args, **kwargs: None,
            "imshow": lambda *args, **kwargs: None,
            "waitKey": lambda *args, **kwargs: ord('q'),
            "destroyAllWindows": lambda *args, **kwargs: None,
        },
    )

if "pyautogui" not in sys.modules:  # pragma: no cover - provide minimal API
    class _FakeScreenshot:
        def __array__(self, dtype=None):
            return numpy.zeros((1, 1, 3))

    _ensure_module(
        "pyautogui",
        {
            "size": lambda: (800, 600),
            "screenshot": lambda **kwargs: _FakeScreenshot(),
            "moveTo": lambda *args, **kwargs: None,
            "click": lambda *args, **kwargs: None,
            "write": lambda *args, **kwargs: None,
            "press": lambda *args, **kwargs: None,
        },
    )

if "pygetwindow" not in sys.modules:  # pragma: no cover - provide minimal API
    _ensure_module("pygetwindow", {"getWindowsWithTitle": lambda title: []})

if "win32api" not in sys.modules:  # pragma: no cover
    _ensure_module("win32api", {"SendMessage": lambda *args, **kwargs: None})

if "win32con" not in sys.modules:  # pragma: no cover
    _ensure_module("win32con", {"WM_SYSCOMMAND": 0, "SC_RESTORE": 0})
