import logging
import os
import time
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import cv2
import keyring
import numpy as np
import pyautogui
import pygetwindow as gw
import win32api
import win32con
from dotenv import dotenv_values, find_dotenv, load_dotenv
from keyring.errors import KeyringError


DEFAULT_KEYRING_SERVICE = "Osros"


def _mask_value(value: str) -> str:
    if not value:
        return value
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"


def _iter_sensitive_tokens() -> Iterable[str]:
    user_profiles = globals().get("users", {})
    if isinstance(user_profiles, dict):
        for profile in user_profiles.values():
            yield profile.username
            yield profile.login


def scrub_message(message: str, extra_tokens: Optional[Iterable[str]] = None) -> str:
    scrubbed = message
    for token in list(_iter_sensitive_tokens()) + list(extra_tokens or []):
        if token:
            scrubbed = scrubbed.replace(token, _mask_value(token))
    return scrubbed


logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def log_info(message: str, extra_sensitive: Optional[Iterable[str]] = None) -> None:
    logger.info(scrub_message(message, extra_sensitive))


@dataclass
class UserProfile:
    identifier: str
    username: str
    login: str
    service_name: str

    def resolve_password(self) -> str:
        try:
            password = keyring.get_password(self.service_name, self.login)
        except KeyringError as exc:  # pragma: no cover - platform specific
            raise RuntimeError(
                f"Unable to access credential store '{self.service_name}': {exc}"
            ) from exc

        if password is None:
            raise RuntimeError(
                "No password found in the credential store for login "
                f"'{self.login}'. Configure it using "
                f"`python -m keyring set {self.service_name} {self.login}`."
            )
        return password


def _load_env_values() -> Dict[str, str]:
    env_path = os.getenv("OSROS_ENV_FILE") or find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)
        return dotenv_values(env_path)
    load_dotenv()
    values: Dict[str, str] = {}
    for key, value in os.environ.items():
        if key.startswith("USER") and key[len("USER"):].isdigit():
            values[key] = value
        elif key.startswith("LOGIN") and key[len("LOGIN"):].isdigit():
            values[key] = value
    return values


def read_users() -> Dict[str, UserProfile]:
    env_values = _load_env_values()
    service_name = os.getenv("OSROS_KEYRING_SERVICE", DEFAULT_KEYRING_SERVICE)

    users: Dict[str, UserProfile] = {}
    for key, value in env_values.items():
        if not key.startswith("USER") or not value:
            continue

        suffix = key[len("USER"):]
        if suffix and not suffix.isdigit():
            continue
        login_key = f"LOGIN{suffix}"
        login_value = env_values.get(login_key) or os.getenv(login_key) or value
        identifier = f"User{suffix or '1'}"
        profile = UserProfile(
            identifier=identifier,
            username=value,
            login=login_value,
            service_name=service_name,
        )
        users[identifier] = profile

    if not users:
        raise RuntimeError(
            "No user profiles found. Ensure your .env file defines entries like "
            "USER1=YourDisplayName and LOGIN1=your@email.com."
        )

    return users


# Read user data from configuration
users = read_users()

# Set active_user to the user you want to log in as
# active_user = sys.argv[1]  # argv[0] is the script name, argv[1] is the first argument
active_user = os.getenv("ACTIVE_USER") or next(iter(users))
if active_user not in users:
    raise RuntimeError(f"Active user '{active_user}' is not defined in the configuration.")

log_info(f"Automation running for {active_user}.")

title = "RuneLite"
window = gw.getWindowsWithTitle(title)[0]  # get the first window with this title

# Prepare templates
template_dir = 'Login/'  # directory with templates
templates = {filename: cv2.imread(template_dir + filename, 0) for filename in os.listdir(template_dir)}

# Create a window for displaying the image
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
    screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))

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
            log_info(f"State recognized: {template_name}")
            state_recognized = True

            # New code: act depending on the detected state
            if template_name == '1 Welcome.png':
                # Click the recognized welcome screen area
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                time.sleep(1)
            elif template_name == 'LoginField.png':
                # Click the detected login field and type username
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                pyautogui.write(users[active_user].login)
                time.sleep(1)
            elif template_name == 'PassField.png':
                # Click the detected password field and type password
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                password = users[active_user].resolve_password()
                pyautogui.write(password)
                del password
                time.sleep(1)
                pyautogui.press('enter')  # Press Enter to submit
                time.sleep(1)
            elif template_name == '3 ClickToPlay.jpg':
                # Click the detected ClickToPlay area
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
            elif template_name == '4 InGame.jpg':
                # Detected in-game state, print it for now, add desired functionality here
                log_info("In-game state detected")

            break  # Break out of the loop once a match is found and handled

    if not state_recognized:
        log_info("No state recognized: Waiting")

    cv2.imshow("Window", screenshot_np)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Quit if 'q' is pressed
        break
    time.sleep(1)  # Pause for a second

cv2.destroyAllWindows()
