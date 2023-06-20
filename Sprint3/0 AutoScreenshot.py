# Take a screenshot every 2 seconds
import cv2
import numpy as np
import pygetwindow as gw
import pyautogui
import time
import win32api
import win32con

title = "RuneLite"
window = gw.getWindowsWithTitle(title)[0]  # get the first window with this title

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

# Delay before taking the initial screenshot
time.sleep(2)

# Define the time interval in seconds
interval = 2

# Define the output folder
output_folder = "templates/"

# Create the output folder if it doesn't exist
#os.makedirs(output_folder, exist_ok=True)

# Start a loop to capture and save templates
counter = 1
while True:
    # Take a screenshot of the area defined by the window
    screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))

    # Convert the screenshot to a numpy array and then to grayscale for processing
    screenshot_np = np.array(screenshot)
    grayscale = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

    # Get the current timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Define the output filename
    output_filename = f"{output_folder}screenshot_{timestamp}.png"

    # Save the screenshot as a timestamped .png file
    cv2.imwrite(output_filename, grayscale)

    print(f"Saved screenshot {counter}: {output_filename}")

    # Increment the counter
    counter += 1

    # Delay for the specified interval
    time.sleep(interval)
