import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Sequence

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import win32api
import win32con

from secure_credentials import CredentialManager

DEFAULT_TEMPLATE_DIR = Path("Login")


def _prepare_templates(
    template_dir: Path, credential_manager: CredentialManager
) -> Dict[str, np.ndarray]:
    if not template_dir.exists():
        raise FileNotFoundError(
            f"Template directory '{template_dir}' was not found."
        )

    templates: Dict[str, np.ndarray] = {}
    for path in sorted(template_dir.iterdir()):
        if not path.is_file():
            continue
        image = cv2.imread(str(path), 0)
        if image is None:
            credential_manager.log_info(
                f"Skipping unreadable template '{path.name}'."
            )
            continue
        templates[path.name] = image

    if not templates:
        raise RuntimeError(
            f"No templates could be loaded from '{template_dir}'. Ensure the directory contains image files."
        )
    credential_manager.log_info(
        f"Loaded {len(templates)} template(s) from '{template_dir}'."
    )
    return templates


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RuneLite automation login assistance."
    )
    parser.add_argument(
        "user",
        nargs="?",
        help="Profile identifier to use (for example User1, User2, etc.)",
    )
    parser.add_argument(
        "--templates",
        type=Path,
        help=(
            "Path to the directory of login state templates. "
            "Defaults to the project Login/ folder."
        ),
    )
    return parser.parse_args(argv[1:])


def main(argv: Optional[Sequence[str]] = None) -> None:
    argv = list(argv) if argv is not None else sys.argv
    args = _parse_args(argv)
    credential_manager = CredentialManager()
    users = credential_manager.read_users()
    active_user = credential_manager.select_active_user(users, args.user)
    active_profile = credential_manager.get_user(active_user)

    credential_manager.log_info(f"Automation running for {active_profile.identifier}.")

    title = "RuneLite"
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        raise RuntimeError(
            "RuneLite window not found. Ensure the client is running before starting the automation."
        )
    window = windows[0]

    # Prepare templates
    template_dir = args.templates or DEFAULT_TEMPLATE_DIR
    templates = _prepare_templates(template_dir, credential_manager)

    # Create a window for displaying the image
    cv2.namedWindow("Window", cv2.WINDOW_NORMAL)

    while True:
        # Check if the window is minimized and restore it if necessary
        if window.isMinimized:
            win32api.SendMessage(
                window._hWnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0
            )

        # Get the screen width and height
        screen_width, screen_height = pyautogui.size()

        # Resize the window if necessary
        new_width = screen_width // 2  # Quarter width
        new_height = screen_height // 2  # Quarter height
        if window.width != new_width or window.height != new_height:
            window.resizeTo(new_width, new_height)

        # Move the window to the top left corner
        window.moveTo(0, 0)

        # Activate the RuneLite window
        window.activate()

        # Resize the OpenCV window
        cv2.resizeWindow("Window", new_width, new_height)
        cv2.moveWindow("Window", new_width, 0)

        # Take a screenshot of the area defined by the window
        screenshot = pyautogui.screenshot(
            region=(window.left, window.top, window.width, window.height)
        )

        # Convert the screenshot to a numpy array and then to grayscale for processing
        screenshot_np = np.array(screenshot)
        grayscale = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

        state_recognized = False

        # Loop over all templates
        for template_name, template in templates.items():
            w, h = template.shape[::-1]

            # Apply template matching
            res = cv2.matchTemplate(grayscale, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.8
            loc = np.where(res >= threshold)

            # If a match is found, draw a rectangle and break the loop as we've identified the state
            for pt in zip(*loc[::-1]):
                cv2.rectangle(
                    screenshot_np, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2
                )
                credential_manager.log_info(f"State recognized: {template_name}")
                state_recognized = True

                # New code: act depending on the detected state
                if template_name == "1 Welcome.png":
                    # Click the recognized welcome screen area
                    pyautogui.click(
                        window.left + pt[0] + w // 2, window.top + pt[1] + h // 2
                    )
                    time.sleep(1)
                elif template_name == "LoginField.png":
                    # Click the detected login field and type username
                    pyautogui.click(
                        window.left + pt[0] + w // 2, window.top + pt[1] + h // 2
                    )
                    pyautogui.write(active_profile.login)
                    time.sleep(1)
                elif template_name == "PassField.png":
                    # Click the detected password field and type password
                    pyautogui.click(
                        window.left + pt[0] + w // 2, window.top + pt[1] + h // 2
                    )
                    password = active_profile.resolve_password()
                    pyautogui.write(password)
                    del password
                    time.sleep(1)
                    pyautogui.press("enter")  # Press Enter to submit
                    time.sleep(1)
                elif template_name == "3 ClickToPlay.jpg":
                    # Click the detected ClickToPlay area
                    pyautogui.click(
                        window.left + pt[0] + w // 2, window.top + pt[1] + h // 2
                    )
                elif template_name == "4 InGame.jpg":
                    # Detected in-game state, print it for now, add desired functionality here
                    credential_manager.log_info("In-game state detected")

                break  # Break out of the loop once a match is found and handled

        if not state_recognized:
            credential_manager.log_info("No state recognized: Waiting")

        cv2.imshow("Window", screenshot_np)
        if cv2.waitKey(1) & 0xFF == ord("q"):  # Quit if 'q' is pressed
            break
        time.sleep(1)  # Pause for a second

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
