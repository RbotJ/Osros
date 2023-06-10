import os
from dotenv import load_dotenv
import pyautogui
import time
import pygetwindow as gw
import json

# Load the .env file
load_dotenv()

def read_users():
    def read_users():
        users = {
            'User1': {
                'username': os.getenv('USER1_USERNAME'),
                'password': os.getenv('USER1_PASSWORD'),
                'login': os.getenv('USER1_LOGIN')
            },
            'User2': {
                'username': os.getenv('USER2_USERNAME'),
                'password': os.getenv('USER2_PASSWORD'),
                'login': os.getenv('USER2_LOGIN')
            },
            'User3': {
                'username': os.getenv('USER3_USERNAME'),
                'password': os.getenv('USER3_PASSWORD'),
                'login': os.getenv('USER3_LOGIN')
            }
        }
        return users

def wait_for_login_screen():
    login_screen_image = 'login_screen.png'

    while True:
        login_screen = pyautogui.locateOnScreen(login_screen_image, confidence=0.9)
        if login_screen:
            break
        time.sleep(1)

def set_runelite_active():
    runelite_window = gw.getWindowsWithTitle('RuneLite')[0]
    if runelite_window:
        runelite_window.activate()

def click_existing_user_button():
    button_image = 'existing_user_button.png'
    button_location = pyautogui.locateOnScreen(button_image, confidence=0.9)

    if button_location:
        button_center = pyautogui.center(button_location)
        pyautogui.click(button_center)
    else:
        print("Existing User button not found.")

def click_login_field():
    # Replace 'login_button.png' with the actual image of the "Login" button
    button_image = 'loginField.png'
    button_location = pyautogui.locateOnScreen(button_image, confidence=0.9)

    if button_location:
        button_center = pyautogui.center(button_location)
        pyautogui.click(button_center)
    else:
        print("Login button not found.")

def click_password_field():
    # Replace 'login_button.png' with the actual image of the "Login" button
    button_image = 'PassField.png'
    button_location = pyautogui.locateOnScreen(button_image, confidence=0.9)

    if button_location:
        button_center = pyautogui.center(button_location)
        pyautogui.click(button_center)
    else:
        print("Login button not found.")

def enter_login_details(active_user):
    login = users[active_user]['login']
    pyautogui.write(login)
    pyautogui.press('enter')

def enter_password_details(active_user):
    password = users[active_user]['password']
    pyautogui.write(password)
    pyautogui.press('enter')

# Set RuneLite as the active window
set_runelite_active()

# Read user data from .env
users = read_users()

# Set active_user to the user you want to log in as
active_user = 'User1'  # Replace with the user you want to log in as

# Wait for the login screen to finish loading
wait_for_login_screen()

# Interact with the "Existing User" button by clicking it once
click_existing_user_button()

# Click the "Login" button
click_login_field()

# Enter the login details for the active_user
enter_login_details(active_user)

# Click the "Password" field
click_password_field()

# Enter the password for the active_user
enter_password_details(active_user)