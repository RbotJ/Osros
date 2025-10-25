import logging
import os
import sys
import time

import cv2
import logging
import numpy as np
import pyautogui
import pygetwindow as gw
import win32api
import win32con
from dotenv import load_dotenv

from automation.logging_config import configure_logging


logger = logging.getLogger(__name__)

# Load the .env file
configure_logging()
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


# Read user data from .env
users = read_users()

# Set active_user to the user you want to log in as
active_user = sys.argv[1] if len(sys.argv) > 1 else 'User3'
logger.info("Starting login automation", extra={"active_user": active_user})

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
        logger.debug(
            "Resizing RuneLite window",
            extra={"width": new_width, "height": new_height},
        )
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
            logger.info("State recognized", extra={"template": template_name})
            state_recognized = True

            # New code: act depending on the detected state
            if template_name == '1 Welcome.png':
                # Click the recognized welcome screen area
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                logger.info("Welcome screen clicked", extra={"template": template_name})
                time.sleep(1)
            elif template_name == 'LoginField.png':
                # Click the detected login field and type username
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                pyautogui.write(users[active_user]['login'])
                logger.info("Entered username", extra={"user": active_user})
                time.sleep(1)
            elif template_name == 'PassField.png':
                # Click the detected password field and type password
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                pyautogui.write(users[active_user]['password'])
                time.sleep(1)
                pyautogui.press('enter')  # Press Enter to submit
                logger.info("Password submitted", extra={"user": active_user})
                time.sleep(1)
            elif template_name == '3 ClickToPlay.jpg':
                # Click the detected ClickToPlay area
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                logger.info("Clicked to play", extra={"template": template_name})
            elif template_name == '4 InGame.jpg':
                # Detected in-game state, print it for now, add desired functionality here
                logger.info("In-game state detected")

            break  # Break out of the loop once a match is found and handled

    if not state_recognized:
        logger.debug("No login state recognized: waiting")

    cv2.imshow("Window", screenshot_np)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Quit if 'q' is pressed
        break
    time.sleep(1)  # Pause for a second

cv2.destroyAllWindows()
