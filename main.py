import logging
import os
import threading
import time
import tkinter as tk
from tkinter import Button, Label, ttk, messagebox
from pathlib import Path

import psutil
from dotenv import load_dotenv

from automation.logging_config import configure_logging
from automation.controller import AutomationController  # merged controller (lifecycle + nav/perception)
from automation.quest import QuestOrchestrator
from navigation.controller import NavigationController
from perception.inventory import TemplateInventoryRecognizer
from login_launcher import LoginLaunchError, LoginLauncher


logger = logging.getLogger(__name__)


class MainWindow:
    def __init__(self, master, accounts, active_username, usernames):
        # Ensure env vars are loaded before reading any
        load_dotenv()

        self.master = master
        self.accounts = accounts
        self.active_username = active_username
        self.usernames = usernames

        # External integrations
        self.login_launcher = LoginLauncher()
        self.runelite_path = os.getenv("RuneLite")

        # Navigation / perception stack
        template_root = Path("Agility/Canifis")
        inventory_template_root = Path("perception/templates")
        self.navigation_controller = NavigationController(
            template_root,
            route_overrides={
                "lumbridge": ["Map1", "Map2", "Map3", "Map4"],
                "varrock": ["Map3", "Map4", "Map5", "Map6"],
                "ge": ["Map5", "Map6", "Map7", "Map8"],
            },
        )
        self.inventory_recognizer = TemplateInventoryRecognizer(inventory_template_root)

        # Unified automation controller (provides task lifecycle + shared state + nav/perception)
        self.automation_controller = AutomationController(
            navigation=self.navigation_controller,
            inventory_recognizer=self.inventory_recognizer,
        )

        # High-level orchestrator that schedules quests / navigation
        self.quest_orchestrator = QuestOrchestrator(self.automation_controller)

        # --- UI wiring ---
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
        self.combo.bind("<<ComboboxSelected>>", self.on_username_select)
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

        # Any default tasks can be registered here if you add implementations
        self._register_default_tasks()

        self.check_runelite()
        threading.Thread(target=self.monitor_runelite, daemon=True).start()

    # ---------- UI callbacks ----------
    def on_username_select(self, event):
        self.active_username = self.combo.get()
        self.active_user = self.combo.get()
        logger.info("Active user changed", extra={"active_user": self.active_user})

    def launch(self):
        logger.info("Launching RuneLite", extra={"path": self.runelite_path})
        if not self.runelite_path:
            messagebox.showerror("RuneLabs", "RuneLite path not set in environment (.env)")
            return
        try:
            os.startfile(self.runelite_path)  # Windows-only
        except Exception as e:
            logger.exception("Failed to start RuneLite")
            messagebox.showerror("RuneLabs", f"Failed to start RuneLite:\n{e}")

    def login(self):
        logger.info("Login button clicked", extra={"active_user": getattr(self, "active_user", None)})
        user = getattr(self, "active_user", None)
        if not user:
            messagebox.showwarning("RuneLabs", "Please select a user first.")
            return
        try:
            self.login_launcher.launch(user)
            self.status_var.set("Status: Logged in")
        except LoginLaunchError as e:
            logger.exception("Login failed")
            messagebox.showerror("RuneLabs", f"Login failed:\n{e}")

    def logout(self):
        logger.info("Logout button clicked")
        # Implement actual logout if your launcher supports it
        self.status_var.set("Status: Logged out")

    def agility(self):
        logger.info("Agility button clicked")

    def fletching(self):
        logger.info("Fletching button clicked")

    def mining(self):
        logger.info("Mining button clicked")

    # ---------- Navigation helpers ----------
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

    # ---------- RuneLite process monitoring ----------
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
        for process in psutil.process_iter(["exe"]):
            if process.info["exe"] and "RuneLite.exe" in process.info["exe"]:
                return True
        return False

    # ---------- Task wiring (stub) ----------
    def _register_default_tasks(self):
        # Example:
        # from my_tasks import SomeTask
        # self.automation_controller.register_task(SomeTask())
        pass

    # ---------- Window lifecycle ----------
    def on_close(self):
        try:
            self.master.destroy()
        except Exception:
            pass


def load_accounts():
    load_dotenv()
    accounts = {
        "User1": {
            "username": os.getenv("USER1"),
            "password": os.getenv("PASS1"),
            "login": os.getenv("USER1_LOGIN"),
        },
        "User2": {
            "username": os.getenv("USER2"),
            "password": os.getenv("PASS2"),
            "login": os.getenv("USER2_LOGIN"),
        },
        "User3": {
            "username": os.getenv("USER3"),
            "password": os.getenv("PASS3"),
            "login": os.getenv("USER3_LOGIN"),
        },
    }
    return accounts


def get_usernames(accounts):
    return [account_info["username"] for account_info in accounts.values() if account_info.get("username")]


# --- Main bootstrap ---
configure_logging()
logger.info("Loading accounts for main window")
accounts = load_accounts()
usernames = get_usernames(accounts)
active_user = usernames[0] if usernames else ""  # default active user if available

root = tk.Tk()
root.geometry("250x200")  # Width x Height
root.attributes("-topmost", True)  # Keep the window on top
window = MainWindow(root, accounts, active_user, usernames)
root.mainloop()
