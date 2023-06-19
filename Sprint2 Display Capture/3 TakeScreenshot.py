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

# Delay before taking the screenshot
#time.sleep(2)

# Take a screenshot of the area defined by the window
screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))

# Convert the screenshot to a numpy array and then to grayscale for processing
screenshot_np = np.array(screenshot)
grayscale = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

# Create a window for displaying the image
cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Window", new_width, new_height)
cv2.moveWindow("Window", new_width, 0)
cv2.imshow("Window", grayscale)
cv2.waitKey(0)
cv2.destroyAllWindows()