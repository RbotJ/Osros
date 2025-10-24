import logging
import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import Button, Label, ttk, messagebox
from dotenv import load_dotenv
import psutil
import threading
import time

from automation_controller import AutomationController, TaskStatus
from login_launcher import LoginLaunchError, LoginLauncher
from tkinter import Button, Label, ttk

import psutil
from dotenv import load_dotenv

from automation.logging_config import configure_logging


logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self, master, accounts, active_username, usernames):
        self.master = master
        self.accounts = accounts
        self.active_username = active_username
        self.usernames = usernames
        self.controller = AutomationController()
        self.login_launcher = LoginLauncher()
        self.active_task_name = None
        self.active_task_category = None
        self.runelite_path = os.getenv('RuneLite')
        master.title("RuneLabs")
        master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.location_var = tk.StringVar(value="Location: Unknown")
        self.activity_var = tk.StringVar(value="Activity: None")
        self.status_var = tk.StringVar(value="Status: Idle")

        self.label = Label(master, text="Welcome to RuneLabs")
        self.label.pack()

        self.combo = ttk.Combobox(master, values=usernames)
        if active_username in usernames:
            self.combo.current(usernames.index(active_username))
        self.combo.bind('<<ComboboxSelected>>', self.on_username_select)
        self.combo.pack()

        self.button_frame = tk.Frame(master)
        self.button_frame.pack()

        self.launch_button = Button(self.button_frame, text="Launch", command=self.launch)
        self.launch_button.pack(side=tk.LEFT)

        self.login_button = Button(self.button_frame, text="Login", command=self.login)
        self.login_button.pack(side=tk.LEFT)

        self.logout_button = Button(self.button_frame, text="Logout", command=self.logout)
        self.logout_button.pack(side=tk.LEFT)

        self.status_frame = tk.Frame(master)
        self.status_frame.pack()

        self.location_status = Label(self.status_frame, textvariable=self.location_var)
        self.location_status.pack(side=tk.LEFT)

        self.activity = Label(self.status_frame, textvariable=self.activity_var)
        self.activity.pack(side=tk.LEFT)

        self.status = Label(self.status_frame, textvariable=self.status_var)
        self.status.pack(side=tk.LEFT)

        self.cancel_button = Button(self.status_frame, text="Cancel Task", command=self.cancel_task, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT)

        self.skill_label = Label(master, text="Skills")
        self.skill_label.pack()

        self.skill_frame = tk.Frame(master)
        self.skill_frame.pack()

        self.agility_button = Button(self.skill_frame, text="Agility", command=self.agility)
        self.agility_button.pack(side=tk.LEFT)

        self.fletching_button = Button(self.skill_frame, text="Fletching", command=self.fletching)
        self.fletching_button.pack(side=tk.LEFT)

        self.mining_button = Button(self.skill_frame, text="Mining", command=self.mining)
        self.mining_button.pack(side=tk.LEFT)

        self.navigation_label = Label(master, text="Navigate")
        self.navigation_label.pack()

        self.navigation_frame = tk.Frame(master)
        self.navigation_frame.pack()

        self.lumbridge_button = Button(self.navigation_frame, text="Lumbridge", command=self.lumbridge)
        self.lumbridge_button.pack(side=tk.LEFT)

        self.varrock_button = Button(self.navigation_frame, text="Varrock", command=self.varrock)
        self.varrock_button.pack(side=tk.LEFT)

        self.ge_button = Button(self.navigation_frame, text="GE", command=self.ge)
        self.ge_button.pack(side=tk.LEFT)

        self._register_default_tasks()

        self.check_runelite()

        threading.Thread(target=self.monitor_runelite, daemon=True).start()

    def on_username_select(self, event):
        self.active_username = self.combo.get()
        print(f"Active User is {self.active_username}")
        self.active_user = self.combo.get()
        logger.info("Active user changed", extra={"active_user": self.active_user})

    def launch(self):
        logger.info("Launching RuneLite", extra={"path": self.runelite_path})
        os.startfile(self.runelite_path)

    def login(self):
        logger.info("Login button clicked", extra={"active_user": self.active_user})
        subprocess.Popen(['python', 'Sprint4/Login.py', self.active_user])

    def logout(self):
        logger.info("Logout button clicked")

    def agility(self):
        logger.info("Agility button clicked")

    def fletching(self):
        logger.info("Fletching button clicked")

    def mining(self):
        logger.info("Mining button clicked")

    def lumbridge(self):
        logger.info("Lumbridge navigation clicked")

    def varrock(self):
        logger.info("Varrock navigation clicked")

    def ge(self):
        logger.info("Grand Exchange navigation clicked")

    def check_runelite(self):
        if self.is_runelite_running():
            self.launch_button.config(text="Linked", state="disabled")
        else:
            self.launch_button.config(text="Launch", state="normal")

    def monitor_runelite(self):
        while True:
            self.check_runelite()
            time.sleep(5)  # check every 5 seconds

    @staticmethod
    def is_runelite_running():
        for process in psutil.process_iter(['exe']):
            if process.info['exe'] and 'RuneLite.exe' in process.info['exe']:
                return True
        return False


def load_accounts():
    load_dotenv()
    accounts = {
        'User1': {
            'username': os.getenv('USER1'),
            'password': os.getenv('PASS1'),
            'login': os.getenv('USER1_LOGIN')
        },
        'User2': {
            'username': os.getenv('USER2'),
            'password': os.getenv('PASS2'),
            'login': os.getenv('USER2_LOGIN')
        },
        'User3': {
            'username': os.getenv('USER3'),
            'password': os.getenv('PASS3'),
            'login': os.getenv('USER3_LOGIN')
        }
    }
    return accounts


def get_usernames(accounts):
    return [account_info['username'] for account_info in accounts.values()]


configure_logging()
logger.info("Loading accounts for main window")
accounts = load_accounts()
usernames = get_usernames(accounts)
active_user = usernames[0]  # Set the first user as the active user

root = tk.Tk()
root.geometry("250x200")  # Width x Height
root.attributes('-topmost', True)  # This will keep the window on top
window = MainWindow(root, accounts, active_user, usernames)
root.mainloop()
