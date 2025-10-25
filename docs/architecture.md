# Architecture Overview

## High-level system
RuneLabs combines a Tkinter GUI (`main.py`) with modular automation services. The GUI bootstraps shared controllers, exposes buttons for navigation helpers, and launches the login automation when requested. Under the hood, the automation modules coordinate window capture, template recognition, and input simulation to interact with RuneLite.

```
Tkinter GUI ─┬─► AutomationController (tasks + shared state)
             ├─► NavigationController ─► Minimap templates (Agility/Canifis/Map*.jpg)
             ├─► QuestOrchestrator ─► AutomationController.plan_route()
             ├─► TemplateInventoryRecognizer ─► perception/templates/*.png
             └─► LoginLauncher ─► Login.py (subprocess)
```

## Core modules
- **`automation/controller.py`** – Provides the unified `AutomationController` that stores shared automation state, runs registered `AutomationTask` instances, and exposes facades for navigation and inventory refresh.【F:automation/controller.py†L26-L130】
- **`navigation/controller.py`** – Wraps the minimap reader to build waypoint sequences from template assets and caches route plans for quick reuse.【F:navigation/controller.py†L10-L49】
- **`navigation/minimap.py`** – Loads template images, sorts them by inferred order, and constructs `RouteWaypoint` objects for downstream navigation routines.【F:navigation/minimap.py†L8-L83】【F:navigation/minimap.py†L87-L139】
- **`perception/inventory.py`** – Implements template-based inventory detection, returning structured `InventoryDetection` records with label, location, and confidence metadata.【F:perception/inventory.py†L10-L96】
- **`automation/templates.py`** – A lightweight template library for skill automations that matches grayscale screenshots against assets stored under `Agility/` and similar directories.【F:automation/templates.py†L1-L58】
- **`automation/skills/agility.py`** – Defines the agility decision engine, cursor orchestration, and the `AgilitySkill` automation which drives clicks based on template matches.【F:automation/skills/agility.py†L13-L146】
- **`automation/window.py`** – Manages the RuneLite window (activation, resizing) and captures colour/grayscale frames for vision pipelines.【F:automation/window.py†L1-L96】

## Data flow
1. **Window preparation:** `WindowCaptureService` ensures the RuneLite window is visible, resized, and optionally previews frames via OpenCV.【F:automation/window.py†L28-L96】
2. **Image acquisition:** Captured frames feed into either the agility decision engine (`automation/skills/agility.py`) or into the inventory recognizer (`perception/inventory.py`).
3. **Template matching:** Each module searches for domain-specific templates (minimap, marks of grace, login screens, inventory items) loaded from the repository.
4. **Decision logic:** Outcomes update shared automation state (`AutomationState`) or queue cursor actions executed by `HumanLikeCursor` workers.【F:automation/controller.py†L32-L37】【F:automation/skills/agility.py†L52-L136】
5. **User feedback:** The Tkinter GUI updates labels and status fields, while structured logging records events through `automation/logging_config.py` and module-level loggers.【F:main.py†L12-L143】【F:automation/logging_config.py†L1-L22】

## Template asset organisation
- **Minimap templates:** Stored under `Agility/Canifis/Map*.jpg|png`. `NavigationController` expects files prefixed with `Map` followed by ordering digits; this order controls waypoint sequencing.【F:navigation/minimap.py†L42-L77】
- **Agility course templates:** Located in `Agility/Canifis/` with prefixes `Clk`, `Clm`, `Cl`, and `Mog`. The agility engine filters by these prefixes to decide the next action.【F:automation/skills/agility.py†L62-L109】
- **Inventory templates:** Place item icons in `perception/templates/`. Filenames become detection labels unless remapped when instantiating `TemplateInventoryRecognizer`.【F:perception/inventory.py†L24-L55】
- **Login templates:** `Login/` contains screen states such as `1 Welcome.png`, `LoginField.png`, etc., used by `Login.py` to automate the credential flow.【F:Login.py†L62-L125】

## Automation orchestration
The GUI wires together several orchestrators:
- `QuestOrchestrator` generates navigation-focused `QuestTask` pipelines and executes them through the shared `AutomationController` to populate route state.【F:automation/quest.py†L28-L69】【F:main.py†L20-L115】
- `LoginLauncher` spawns the standalone login automation in a subprocess and streams stderr for diagnostics.【F:login_launcher.py†L15-L104】
- `automation_controller.py` (root) remains available for asynchronous task execution with progress callbacks when building more advanced workflows.【F:automation_controller.py†L1-L123】

Together these components allow you to extend RuneLabs with additional automation tasks while keeping window capture, template management, and logging consistent.
