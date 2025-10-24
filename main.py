import os
import tkinter as tk
from tkinter import Button, Label, ttk
from pathlib import Path
import psutil
import threading
import time
import subprocess

from dotenv import load_dotenv

from automation.controller import AutomationController
from automation.quest import QuestOrchestrator
from navigation.controller import NavigationController
from perception.inventory import TemplateInventoryRecognizer


class MainWindow:
    def __init__(self, master, active_user, usernames):
        self.master = master
        self.active_user = active_user
        self.runelite_path = os.getenv('RuneLite')

        template_root = Path('Agility/Canifis')
        inventory_template_root = Path('perception/templates')
        self.navigation_controller = NavigationController(
            template_root,
            route_overrides={
                'lumbridge': ['Map1', 'Map2', 'Map3', 'Map4'],
                'varrock': ['Map3', 'Map4', 'Map5', 'Map6'],
                'ge': ['Map5', 'Map6', 'Map7', 'Map8'],
            },
        )
        self.inventory_recognizer = TemplateInventoryRecognizer(inventory_template_root)
        self.automation_controller = AutomationController(self.navigation_controller, self.inventory_recognizer)
        self.quest_orchestrator = QuestOrchestrator(self.automation_controller)

        master.title("RuneLabs")

        self.label = Label(master, text="Welcome to RuneLabs")
        self.label.pack()

        self.combo = ttk.Combobox(master, values=usernames)
        self.combo.current(usernames.index(active_user))
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

        self.location_status = Label(self.status_frame, text="Location")
        self.location_status.pack(side=tk.LEFT)

        self.activity = Label(self.status_frame, text="Activity")
        self.activity.pack(side=tk.LEFT)

        self.status = Label(self.status_frame, text="Status")
        self.status.pack(side=tk.LEFT)

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

        self.check_runelite()

        threading.Thread(target=self.monitor_runelite, daemon=True).start()

    def on_username_select(self, event):
        self.active_user = self.combo.get()
        print(f"Active User is {self.active_user}")

    def launch(self):
        os.startfile(self.runelite_path)

    def login(self):
        print("Login button was clicked!")
        subprocess.Popen(['python', 'Sprint4/Login.py', self.active_user])

    def logout(self):
        print("Logout button was clicked!")

    def agility(self):
        print("Agility button was clicked!")

    def fletching(self):
        print("Fletching button was clicked!")

    def mining(self):
        print("Mining button was clicked!")

    def _update_navigation_ui(self, destination: str, route_summary: str, waypoint_count: int) -> None:
        self.location_status.config(text=f"Route: {destination}")
        self.status.config(text=f"Waypoints: {waypoint_count}")
        self.activity.config(text="Navigating")
        print(route_summary)

    def navigate_to(self, destination: str) -> None:
        quest = self.quest_orchestrator.plan_navigation_task(destination)
        quest.run(self.automation_controller)
        route = self.automation_controller.state.planned_route
        if not route:
            summary = f"No route data for {destination}"
            self._update_navigation_ui(destination, summary, 0)
            return
        route_summary = ", ".join(f"{wp.order}:{wp.template.name}" for wp in route)
        summary = f"Navigation route for {destination}: {route_summary}"
        self._update_navigation_ui(destination, summary, len(route))

    def lumbridge(self):
        self.navigate_to("Lumbridge")

    def varrock(self):
        self.navigate_to("Varrock")

    def ge(self):
        self.navigate_to("GE")

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


accounts = load_accounts()
usernames = get_usernames(accounts)
active_user = usernames[0]  # Set the first user as the active user

root = tk.Tk()
root.geometry("250x200")  # Width x Height
root.attributes('-topmost', True)  # This will keep the window on top
window = MainWindow(root, active_user, usernames)
root.mainloop()
