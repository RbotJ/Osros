# Automation Usage Guide

This guide summarises how to run or embed each automation module shipped with the repository. All examples assume you have created a `.env` file and installed dependencies as described in the root `README.md`.

## GUI launcher (`main.py`)
The Tkinter GUI is the canonical entry point for day-to-day automation.

1. Activate your Python virtual environment.
2. Ensure `RuneLite` is set in `.env` and at least one set of credentials is populated.
3. Run `python main.py` to launch the control panel.
4. Use the **Launch** button to start RuneLite, **Login** to trigger the login subprocess, and navigation buttons to generate waypoint plans via `QuestOrchestrator` and `AutomationController` integration.【F:main.py†L12-L135】
5. The GUI automatically monitors the RuneLite process and disables the launch button once the client is detected.【F:main.py†L145-L174】

## Login automation (`Login.py`)
`Login.py` is a standalone script that automates the RuneLite login flow.

- Invoke it with an account key (e.g. `python Login.py User1`).
- The script restores and resizes the RuneLite window, captures screenshots, and matches templates (e.g. `LoginField.png`, `PassField.png`).【F:Login.py†L70-L124】
- Credential values come from `.env` variables with the `_USERNAME`, `_PASSWORD`, and `_LOGIN` suffixes.【F:Login.py†L33-L61】
- Press `q` in the OpenCV preview window to stop the automation loop.【F:Login.py†L126-L151】

## Automation controller (`automation_controller.py`)
Use the root-level `AutomationController` class when you need to run long-lived tasks on background threads.

```python
from automation_controller import AutomationController, TaskStatus

controller = AutomationController()

# Register a callable task
@controller.register_task("example", category="demo")
def example_task(stop_event, update, user):
    update("Doing work", 0.5)
    # Check stop_event.is_set() periodically to support cancellation
```

- Start a task with `controller.start_task("example", user="User1", callback=print)` to receive `TaskStatus` updates.【F:automation_controller.py†L27-L117】
- Cancel running tasks via `controller.stop_task("example")` or `controller.stop_all()` when shutting down.【F:automation_controller.py†L119-L140】

## Navigation helpers (`navigation` package)
`NavigationController` translates a directory of minimap templates into route plans.

```python
from navigation.controller import NavigationController

nav = NavigationController("Agility/Canifis")
route = nav.plan_route("Lumbridge")
print([wp.as_dict() for wp in route])
```

- The controller caches routes by destination name and honours custom overrides provided at instantiation time.【F:navigation/controller.py†L10-L49】
- Template ordering follows the filename numbering handled by `MinimapTemplateReader` and `RouteBuilder`.【F:navigation/minimap.py†L26-L101】

## Inventory recognition (`perception/inventory.py`)
The `TemplateInventoryRecognizer` detects items or UI widgets inside captured screenshots.

```python
from perception.inventory import TemplateInventoryRecognizer
import cv2

recognizer = TemplateInventoryRecognizer("perception/templates")
image = cv2.imread("tests/data/inventory.png", cv2.IMREAD_UNCHANGED)
detections = recognizer.detect_from_image(image)
for detection in detections:
    print(detection.as_dict())
```

- Place templates in `perception/templates/` and name them descriptively; the stem becomes the label unless you provide a `labels` mapping.【F:perception/inventory.py†L24-L57】
- Adjust `detection_threshold` when instantiating the recognizer if you need more or fewer matches.【F:perception/inventory.py†L34-L53】

## Agility skill runner (`automation/skills/agility.py`)
The agility module showcases a full automation loop that reads minimap and course templates, makes decisions, and queues cursor actions.

```python
import time
from automation.skills.agility import AgilitySkill

skill = AgilitySkill(enable_preview=False)
skill.start()
try:
    while True:
        skill.update()
        time.sleep(0.05)
except KeyboardInterrupt:
    pass
finally:
    skill.stop()
```

- The `AgilitySkill` wraps a `WindowCaptureService` and `HumanLikeCursor` to automate clicks based on template matches returned by `TemplateLibrary`.【F:automation/skills/agility.py†L82-L140】【F:automation/templates.py†L16-L58】
- Customise thresholds or window management behaviour through constructor arguments (`window_title`, `manage_window_geometry`, `enable_preview`).【F:automation/skills/agility.py†L82-L106】

## Shared utilities
- **Logging:** Call `automation.logging_config.configure_logging()` at startup to enable structured logging across modules.【F:automation/logging_config.py†L6-L22】
- **Window capture:** Reuse `WindowCaptureService` when building new automations that need consistent screenshots and preview handling.【F:automation/window.py†L28-L96】
- **Skill registry:** New skill implementations can call `automation.skills.register_skill("name", SkillClass)` to appear in the shared registry and integrate with orchestrators.【F:automation/skills/__init__.py†L8-L20】
