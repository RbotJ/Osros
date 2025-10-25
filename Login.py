import argparse
import cv2
import logging
import numpy as np
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import pyautogui
import pygetwindow as gw
import win32api
import win32con
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


@dataclass
class UserCredentials:
    username: str
    password: str
    login: str

    def missing_fields(self) -> Iterable[str]:
        return [
            field
            for field, value in (
                ("username", self.username),
                ("password", self.password),
                ("login", self.login),
            )
            if not value
        ]


def read_users() -> Dict[str, UserCredentials]:
    users: Dict[str, UserCredentials] = {}
    index = 1

    while True:
        prefix = f"USER{index}"
        username = os.getenv(f"{prefix}_USERNAME")
        password = os.getenv(f"{prefix}_PASSWORD")
        login = os.getenv(f"{prefix}_LOGIN")

        if not any((username, password, login)):
            # Stop reading once we encounter an entirely empty block of credentials
            break

        credentials = UserCredentials(
            username=username or "",
            password=password or "",
            login=login or "",
        )
        users[f"User{index}"] = credentials
        index += 1

    return users


def parse_arguments(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RuneLite login automation")
    parser.add_argument(
        "user",
        nargs="?",
        help="User key (e.g. User1) or username/login email to activate",
    )
    parser.add_argument(
        "--list-users",
        action="store_true",
        help="List available users and exit",
    )
    return parser.parse_args(argv)


def select_active_user(
    requested_user: str, available_users: Dict[str, UserCredentials]
) -> Tuple[str, UserCredentials]:
    normalized = requested_user.lower()
    for key, credentials in available_users.items():
        identifiers = [key, credentials.username, credentials.login]
        if any(identifier and identifier.lower() == normalized for identifier in identifiers):
            return key, credentials

    logging.error(
        "Active user '%s' was not found. Available options: %s",
        requested_user,
        ", ".join(sorted(available_users.keys())),
    )
    raise SystemExit(1)


def validate_credentials(user_key: str, creds: UserCredentials) -> None:
    missing = list(creds.missing_fields())
    if missing:
        logging.error(
            "Missing credential fields for %s: %s. Check the environment configuration before retrying.",
            user_key,
            ", ".join(missing),
        )
        raise SystemExit(1)


def get_runelite_window(title: str = "RuneLite"):
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        logging.error("RuneLite window with title '%s' was not found.", title)
        raise SystemExit(1)
    return windows[0]


def load_templates(template_dir: str) -> Dict[str, np.ndarray]:
    if not os.path.isdir(template_dir):
        logging.error("Template directory '%s' does not exist.", template_dir)
        raise SystemExit(1)

    templates: Dict[str, np.ndarray] = {}
    for filename in os.listdir(template_dir):
        path = os.path.join(template_dir, filename)
        if os.path.isdir(path):
            continue
        template = cv2.imread(path, 0)
        if template is None:
            logging.warning("Failed to load template '%s'.", path)
            continue
        templates[filename] = template

    if not templates:
        logging.error("No templates were loaded from '%s'.", template_dir)
        raise SystemExit(1)

    return templates


def login_loop(window, templates: Dict[str, np.ndarray], credentials: UserCredentials) -> None:
    cv2.namedWindow("Window", cv2.WINDOW_NORMAL)

    while True:
        # Check if the window is minimized and restore it if necessary
        if window.isMinimized:
            win32api.SendMessage(window._hWnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)

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
                cv2.rectangle(screenshot_np, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
                logging.info("State recognized: %s", template_name)
                state_recognized = True

                # New code: act depending on the detected state
                if template_name == '1 Welcome.png':
                    # Click the recognized welcome screen area
                    pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                    time.sleep(1)
                elif template_name == 'LoginField.png':
                    # Click the detected login field and type username
                    pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                    pyautogui.write(credentials.login)
                    time.sleep(1)
                elif template_name == 'PassField.png':
                    # Click the detected password field and type password
                    pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                    pyautogui.write(credentials.password)
                    time.sleep(1)
                    pyautogui.press('enter')  # Press Enter to submit
                    time.sleep(1)
                elif template_name == '3 ClickToPlay.jpg':
                    # Click the detected ClickToPlay area
                    pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                elif template_name == '4 InGame.jpg':
                    # Detected in-game state, log it for now, add desired functionality here
                    logging.info("In-game state detected")

                break  # Break out of the loop once a match is found and handled

        if not state_recognized:
            logging.info("No state recognized: Waiting")

        cv2.imshow("Window", screenshot_np)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Quit if 'q' is pressed
            break
        time.sleep(1)  # Pause for a second

    cv2.destroyAllWindows()


def main(argv: Iterable[str]) -> int:
    users = read_users()
    if not users:
        logging.error("No users were loaded from the environment. Please ensure credentials are configured.")
        return 1

    args = parse_arguments(argv)

    if args.list_users:
        for key, creds in users.items():
            login_display = creds.login or "<missing login>"
            logging.info(
                "%s -> username=%s, login=%s",
                key,
                creds.username or "<missing username>",
                login_display,
            )
        if not args.user:
            return 0

    if not args.user:
        logging.error("No active user specified. Provide a user key or username.")
        return 1

    user_key, credentials = select_active_user(args.user, users)
    validate_credentials(user_key, credentials)

    window = get_runelite_window()
    templates = load_templates('Login/')
    login_loop(window, templates, credentials)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
