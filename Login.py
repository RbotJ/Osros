import cv2
import logging
import numpy as np
import os
import sys
import time

import pyautogui
import pygetwindow as gw
import win32api
import win32con
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# Your users dictionary function
def read_users():
    users = {}
    index = 1

    while True:
        prefix = f"USER{index}"
        username = os.getenv(f"{prefix}_USERNAME")
        password = os.getenv(f"{prefix}_PASSWORD")
        login = os.getenv(f"{prefix}_LOGIN")

        if not any((username, password, login)):
            # Stop reading once we encounter an entirely empty block of credentials
            break

        users[f"User{index}"] = {
            'username': username,
            'password': password,
            'login': login
        }
        index += 1

    return users


# Read user data from .env
users = read_users()

if not users:
    logging.error("No users were loaded from the environment. Please ensure credentials are configured.")
    sys.exit(1)


def get_active_user(argv, available_users):
    if len(argv) < 2:
        logging.error("No active user specified. Usage: python Login.py <UserX>")
        sys.exit(1)

    requested_user = argv[1].lower()
    for user in available_users:
        if user.lower() == requested_user:
            return user

    logging.error(
        "Active user '%s' was not found. Available users: %s",
        argv[1],
        ", ".join(sorted(available_users))
    )
    sys.exit(1)


active_user = get_active_user(sys.argv, users)
credentials = users[active_user]


def validate_credentials(user_key, creds):
    missing = [field for field, value in creds.items() if not value]
    if missing:
        logging.error(
            "Missing credential fields for %s: %s. Check the environment configuration before retrying.",
            user_key,
            ", ".join(missing)
        )
        return False
    return True


if not validate_credentials(active_user, credentials):
    sys.exit(1)

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
                pyautogui.write(credentials['login'])
                time.sleep(1)
            elif template_name == 'PassField.png':
                # Click the detected password field and type password
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                pyautogui.write(credentials['password'])
                time.sleep(1)
                pyautogui.press('enter')  # Press Enter to submit
                time.sleep(1)
            elif template_name == '3 ClickToPlay.jpg':
                # Click the detected ClickToPlay area
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
            elif template_name == '4 InGame.jpg':
                # Detected in-game state, print it for now, add desired functionality here
                print("In-game state detected")

            break  # Break out of the loop once a match is found and handled

    if not state_recognized:
        logging.info("No state recognized: Waiting")

    cv2.imshow("Window", screenshot_np)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Quit if 'q' is pressed
        break
    time.sleep(1)  # Pause for a second

cv2.destroyAllWindows()
