import cv2
import numpy as np
import pygetwindow as gw
import pyautogui
import win32api
import win32con
import os
import time
from dotenv import load_dotenv
import sys

# Load the .env file
load_dotenv()


# Your users dictionary function
def read_users():
    users = {
        'User1': {
            'username': os.getenv('USER1'),
            'password': os.getenv('PASS1'),
            'login': os.getenv('LOGIN1')
        },
        'User2': {
            'username': os.getenv('USER2'),
            'password': os.getenv('PASS2'),
            'login': os.getenv('ULOGIN2')
        },
        'User3': {
            'username': os.getenv('USER3'),
            'password': os.getenv('PASS3'),
            'login': os.getenv('LOGIN3')
        }
    }
    return users


# Read user data from .env
users = read_users()

# Set active_user to the user you want to log in as
if len(sys.argv) > 1:
    active_user = sys.argv[1]
else:
    active_user = 'User3'

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
            print(f"State recognized: {template_name}")
            state_recognized = True

            # New code: act depending on the detected state
            if template_name == '1 Welcome.png':
                # Click the recognized welcome screen area
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                time.sleep(1)
            elif template_name == 'LoginField.png':
                # Click the detected login field and type username
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                pyautogui.write(users[active_user]['login'])
                time.sleep(1)
            elif template_name == 'PassField.png':
                # Click the detected password field and type password
                pyautogui.click(window.left + pt[0] + w // 2, window.top + pt[1] + h // 2)
                pyautogui.write(users[active_user]['password'])
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
        print("No state recognized: Waiting")

    cv2.imshow("Window", screenshot_np)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Quit if 'q' is pressed
        break
    time.sleep(1)  # Pause for a second

cv2.destroyAllWindows()
