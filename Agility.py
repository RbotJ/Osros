import logging
import multiprocessing as mp
import os
import random
import time

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import win32api
import win32con

from automation.logging_config import configure_logging


logger = logging.getLogger(__name__)

def find_template(template_name, template, grayscale, screenshot):
    """Find a template in a grayscale image and draw a rectangle in the color screenshot."""
    w, h = template.shape[::-1]
    res = cv2.matchTemplate(grayscale, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.9
    loc = np.where(res >= threshold)

    # If a match is found, draw a rectangle
    for pt in zip(*loc[::-1]):
        cv2.rectangle(screenshot, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
        center_position = (pt[0] + w // 2, pt[1] + h // 2)  # Calculate the center of the rectangle
        if template_name.startswith("Map"):  # Check if it is a minimap template
            logger.info("Minimap state recognized", extra={"template": template_name})
            return f"Minimap state recognized: {template_name}", center_position
        if template_name.startswith("Clk"):  # Check if it is a clickpoint template
            logger.info("Click point recognized", extra={"template": template_name})
            return f"Click point recognized: {template_name}", center_position
        if template_name.startswith("Clm"):  # Check if it is a clickofgrace template
            logger.info("Click of grace recognized", extra={"template": template_name})
            return f"Click of grace recognized: {template_name}", center_position
        if template_name.startswith("Mog"):  # Check if it is a markofgrace template
            logger.info("Mark of grace recognized", extra={"template": template_name})
            return f"Mark of grace recognized: {template_name}", center_position
    return None, None

def click_on_position(queue):
    """Click on a given position."""
    while True:
        if not queue.empty():
            position = queue.get()
            x_offset = random.randint(-4, 4)  # randomize x position
            y_offset = random.randint(-4, 4)  # randomize y position
            move_delay = random.uniform(0.1, 0.2)  # randomize delay before moving
            click_delay = random.uniform(0.1, 0.6)  # randomize delay before clicking

            time.sleep(move_delay)
            target = (position[0] + x_offset, position[1] + y_offset)
            logger.debug(
                "Moving to click position",
                extra={"position": target, "move_delay": round(move_delay, 3)},
            )
            pyautogui.moveTo(*target)

            time.sleep(click_delay)
            logger.debug(
                "Clicking position",
                extra={"position": target, "click_delay": round(click_delay, 3)},
            )
            pyautogui.click()
            time.sleep(4)  # Add a 4-second delay after each click


def make_decision(
    templates,
    grayscale,
    screenshot,
    queue,
    current_map,
    clicks_to_spend,
    *,
    sleep_func=time.sleep,
):
    """Make a decision based on the templates found in the grayscale image."""
    # Check for map templates when there are no clicks to spend
    if clicks_to_spend == 0:
        for template_name, template in templates.items():
            if template_name.startswith("Map"):
                message, position = find_template(template_name, template, grayscale, screenshot)
                if message is not None:
                    logger.info(
                        "Map detected",
                        extra={
                            "template": template_name,
                            "clicks_to_spend": clicks_to_spend,
                        },
                    )
                    current_map = template_name  # Update current map
                    clicks_to_spend = 1  # Set clicks to spend to 1
                    return True, current_map, clicks_to_spend

    # Check for Mog, Clm and Clk templates when there are clicks to spend
    if clicks_to_spend > 0:
        for template_name, template in templates.items():
            if template_name.startswith("Mog"):
                # If a Mog is found, click on it.
                message, position = find_template(template_name, template, grayscale, screenshot)
                if message is not None:
                    logger.info("Mark of grace detected", extra={"template": template_name})
                    queue.put(position)
                    sleep_func(2)  # Wait for 3 seconds
                    clicks_to_spend += 1  # Add an extra click to spend
                    return True, current_map, clicks_to_spend

            if template_name.startswith("Cl"):
                # If it is a clickpoint template
                message, position = find_template(template_name, template, grayscale, screenshot)
                if message is not None:
                    logger.info(
                        "Click point detected",
                        extra={
                            "template": template_name,
                            "remaining_clicks": clicks_to_spend - 1,
                        },
                    )
                    queue.put(position)
                    sleep_func(3)  # Wait for 3 seconds
                    # Decrease the number of clicks to spend only if a clickpoint is found
                    clicks_to_spend -= 1
                    return True, current_map, clicks_to_spend

    logger.debug(
        "No template matched",
        extra={"current_map": current_map, "clicks_to_spend": clicks_to_spend},
    )
    return False, current_map, clicks_to_spend


def main():
    configure_logging()
    title = "RuneLite"
    window = gw.getWindowsWithTitle(title)[0]  # get the first window with this title

    current_map = None
    clicks_to_spend = 0

    # Prepare templates
    template_dir = 'Agility/Canifis/'
    templates = {
        filename: cv2.imread(template_dir + filename, 0)
        for filename in os.listdir(template_dir)
    }

    # Create a window for displaying the image
    cv2.namedWindow("Window", cv2.WINDOW_AUTOSIZE)
    window_resized = False  # A flag to check whether the window has been resized or not

    queue = mp.Queue()
    p = mp.Process(target=click_on_position, args=(queue,))
    p.start()
    try:
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

            state_recognized, current_map, clicks_to_spend = make_decision(
                templates,
                grayscale,
                screenshot_np,
                queue,
                current_map,
                clicks_to_spend,
            )

            if not state_recognized:
                logger.debug("No state recognized: waiting")

            cv2.imshow("Window", screenshot_np)

            # Resize and move the window after it has been shown
            if not window_resized:
                cv2.resizeWindow("Window", new_width, new_height)
                cv2.moveWindow("Window", new_width, 0)
                window_resized = True

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Quit if 'q' is pressed
                break
            time.sleep(.1)  # Pause for a second
    except Exception as exc:
        logger.exception("An error occurred during agility automation", exc_info=exc)
    finally:
        p.terminate()  # Make sure to terminate the click_on_position process when main process ends.
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
