import pytest

from automation.controller import AutomationController, AutomationTask


class StubWindowAPI:
    def __init__(self):
        self.focus_calls = []

    def focus(self, title):
        self.focus_calls.append(title)


class StubInputAPI:
    def __init__(self):
        self.clicks = []

    def move_and_click(self, position):
        self.clicks.append(position)


class LifecycleTask(AutomationTask):
    def __init__(self, steps):
        super().__init__("lifecycle")
        self.steps_remaining = steps
        self.events = []

    def on_start(self, context):
        self.events.append("start")
        context["window_api"].focus("RuneLite")

    def perform_step(self, context):
        self.events.append("step")
        context["input_api"].move_and_click((100, 200))
        self.steps_remaining -= 1
        return self.steps_remaining > 0

    def on_stop(self, context):
        self.events.append("stop")


def test_controller_runs_task_lifecycle():
    window_api = StubWindowAPI()
    input_api = StubInputAPI()
    task = LifecycleTask(steps=2)
    controller = AutomationController(window_api, input_api)
    controller.register_task(task)

    context = controller.run_task(task.name)

    assert context["window_api"] is window_api
    assert context["input_api"] is input_api
    assert task.events == ["start", "step", "step", "stop"]
    assert window_api.focus_calls == ["RuneLite"]
    assert input_api.clicks == [(100, 200), (100, 200)]


class FailingTask(AutomationTask):
    def __init__(self):
        super().__init__("failing")
        self.cleaned_up = False

    def on_start(self, context):
        pass

    def perform_step(self, context):
        raise RuntimeError("boom")

    def on_stop(self, context):
        self.cleaned_up = True


def test_controller_cleans_up_on_exception():
    window_api = StubWindowAPI()
    input_api = StubInputAPI()
    task = FailingTask()
    controller = AutomationController(window_api, input_api)
    controller.register_task(task)

    with pytest.raises(RuntimeError):
        controller.run_task(task.name)

    assert task.cleaned_up is True
