# RuneLabs Automation Toolkit

## Overview
RuneLabs provides a collection of GUI tools and automation helpers for interacting with the RuneLite client. The toolkit combines a Tkinter control panel, reusable automation controllers, and computer-vision powered routines for navigation, quest planning, and skill-specific automation.

This document explains how to prepare a Windows workstation, install dependencies, configure environment variables, and launch both the GUI and the headless automation scripts that ship with the repository.

## Windows prerequisites
The automation stack targets Windows because it depends on Win32 APIs for window management and `pywin32` for input simulation. Before installing the project ensure the following are available:

- **Operating system:** Windows 10 or Windows 11 (64-bit).
- **Python:** Python 3.10 or 3.11 from [python.org](https://www.python.org/downloads/windows/). Enable the "Add Python to PATH" option during installation.
- **Microsoft C++ Build Tools:** Required for some native dependencies. Install the [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/), selecting the "Desktop development with C++" workload.
- **RuneLite client:** Installed locally. Note the full path to `RuneLite.exe` for use in your `.env` file.
- **Git:** To clone the repository.

## Dependency installation
1. **Clone the repository**
   ```powershell
   git clone https://github.com/your-org/Osros.git
   cd Osros
   ```

2. **Create and activate a virtual environment** (optional but recommended)
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Python dependencies**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   The `requirements.txt` file includes packages such as OpenCV, NumPy, `pyautogui`, `pywin32`, and `python-dotenv`. If any wheel compilation fails, ensure the Visual C++ build tools are installed.

## Environment configuration
1. **Create your `.env` file**
   ```powershell
   copy Template.env .env
   ```

2. **Populate account credentials**
   - Fill in each block of variables (`USER1_USERNAME`, `USER1_PASSWORD`, `USER1_LOGIN`, etc.).
   - The Tkinter GUI also recognises legacy aliases (`USER1`, `PASS1`, `USER1_LOGIN`, etc.). Duplicate the username and password values into both naming styles to keep the GUI and legacy automation scripts in sync.

3. **Add client paths and options**
   - Set `RuneLite` to the full path of `RuneLite.exe` (for example, `C:\Program Files\RuneLite\RuneLite.exe`).
   - Include any other environment flags your local automations require.

4. **Keep secrets secure**
   - The `.env` file stays untracked by Git. Store it outside of shared drives when possible.

## Launching the GUI control panel
The Tkinter GUI (`main.py`) is the entry-point for monitoring RuneLite, launching login automation, and triggering navigation helpers.

1. Ensure RuneLite is installed and closed. The GUI can launch the client if the `RuneLite` path is configured.
2. Activate your virtual environment if you created one.
3. Run the GUI:
   ```powershell
   python main.py
   ```
4. Select an account from the drop-down list. The list is populated from the `.env` credentials.
5. Use the **Launch** button to start RuneLite, **Login** to trigger the automated login process, and the navigation buttons (Lumbridge, Varrock, GE) to generate waypoint plans. Status labels update based on automation state.
6. Close the window to clean up background monitors.

## Running automation scripts headlessly
Several standalone automation modules are included for specialised tasks. Each module can be executed from the repository root after activating your environment.

| Script | Purpose | How to run |
| ------ | ------- | ---------- |
| `Login.py` | Automates credential entry and login flow inside RuneLite using template matching. | `python Login.py User1` (replace `User1` with a key defined in `.env`). |
| `automation/skills/agility.py` | Provides the `AgilitySkill` automation, which captures the game window, recognises agility course states, and performs human-like clicks. See [docs/usage.md](docs/usage.md#agility-skill-runner) for orchestration examples. | Import into your own runner or extend the GUI. A sample loop is provided in the usage guide. |
| `automation_controller.py` | Runs background automation tasks with progress reporting. Useful when orchestrating multi-step workflows. | Import `AutomationController` in your scripts and register callables; refer to [docs/usage.md](docs/usage.md#automation-controller) for details. |

Most automation flows depend on template assets in the `Agility/` and `Login/` directories. Review the [template capture guide](docs/template_capture.md) before adding or updating images.

## Automation workflow tips
- Verify that RuneLite is set to **fixed window size** and **English locale** so templates align correctly.
- Run scripts in a maximised PowerShell window with Administrator privileges if you encounter permission issues when automating input.
- Use the provided logging utilities (`automation/logging_config.py`) to capture structured logs during long-running automation sessions.

## Further reading
- [Architecture overview](docs/architecture.md)
- [Automation usage cookbook](docs/usage.md)
- [Template capture and maintenance](docs/template_capture.md)
