import os
import tkinter as tk
from tkinter import Button, Label, ttk, messagebox
from dotenv import load_dotenv
import psutil
import threading
import time

from automation_controller import AutomationController, TaskStatus
from login_launcher import LoginLaunchError, LoginLauncher

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

    def launch(self):
        os.startfile(self.runelite_path)

    def login(self):
        account_key = self._resolve_account_key(self.active_username)
        if not account_key:
            messagebox.showerror("Login", "Unable to locate the selected account in configuration.")
            return

        try:
            self.login_launcher.launch(account_key)
        except LoginLaunchError as exc:
            messagebox.showerror("Login", str(exc))
            return

        self.status_var.set("Status: Login automation running…")
        self._poll_login_process()

    def logout(self):
        print("Logout button was clicked!")
        self.controller.stop_all()
        self.status_var.set("Status: Logged out")

    def agility(self):
        self._start_task('Agility')

    def fletching(self):
        self._start_task('Fletching')

    def mining(self):
        self._start_task('Mining')

    def lumbridge(self):
        self._start_task('Lumbridge')

    def varrock(self):
        self._start_task('Varrock')

    def ge(self):
        self._start_task('GE')

    def cancel_task(self):
        if self.active_task_name:
            self.controller.stop_task(self.active_task_name)

    def _start_task(self, task_name):
        if self.active_task_name and self.controller.is_running(self.active_task_name):
            if self.active_task_name == task_name:
                messagebox.showinfo("Task Running", f"{task_name} is already running.")
                return
            messagebox.showwarning(
                "Task Running",
                "Another task is currently in progress. Please cancel it before starting a new one.",
            )
            return

        try:
            self.controller.start_task(task_name, user=self.active_username, callback=self._handle_task_status)
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Automation", str(exc))
            return

        self.active_task_name = task_name
        self.active_task_category = None
        self.status_var.set(f"Status: {task_name} started")
        self.cancel_button.config(state=tk.NORMAL)

    def _handle_task_status(self, status: TaskStatus):
        def update_ui():
            if status.category == 'skill':
                self.activity_var.set(f"Activity: {status.name}")
            elif status.category == 'location':
                self.location_var.set(f"Location: {status.name}")
            else:
                self.activity_var.set(f"Activity: {status.name}")

            if status.state == 'running':
                self.active_task_category = status.category
                progress = int(status.progress * 100) if status.progress is not None else None
                if progress is not None:
                    self.status_var.set(f"Status: {status.message} ({progress}%)")
                else:
                    self.status_var.set(f"Status: {status.message}")
            elif status.state == 'completed':
                self.status_var.set(f"Status: {status.message}")
                self.cancel_button.config(state=tk.DISABLED)
                self.active_task_name = None
                self.active_task_category = None
            elif status.state == 'cancelled':
                self.status_var.set("Status: Task cancelled")
                self.cancel_button.config(state=tk.DISABLED)
                self.active_task_name = None
                self.active_task_category = None
            elif status.state == 'error':
                message = status.message
                if status.error:
                    message = f"{message}: {status.error}"
                self.status_var.set(f"Status: {message}")
                messagebox.showerror("Automation", message)
                self.cancel_button.config(state=tk.DISABLED)
                self.active_task_name = None
                self.active_task_category = None

        self.master.after(0, update_ui)

    def _poll_login_process(self):
        process = self.login_launcher.process
        if not process:
            return

        return_code = self.login_launcher.poll()
        if return_code is None:
            self.master.after(1000, self._poll_login_process)
            return

        stderr_output = self.login_launcher.consume_stderr().strip()
        if return_code == 0:
            self.status_var.set("Status: Login complete")
            messagebox.showinfo("Login", "Login automation finished successfully.")
        else:
            message = f"Login automation exited with code {return_code}"
            if stderr_output:
                message += f"\n\n{stderr_output}"
            self.status_var.set("Status: Login failed")
            messagebox.showerror("Login", message)

        self.login_launcher.terminate()

    def _resolve_account_key(self, username):
        if username in self.accounts:
            return username
        for key, details in self.accounts.items():
            if details.get('username') == username:
                return key
        return None

    def _register_default_tasks(self):
        def build_task(description, *, steps=10, delay=0.5):
            def task(stop_event, update, user):
                for step in range(steps):
                    if stop_event.is_set():
                        return
                    prefix = description
                    if user:
                        prefix = f"{description} for {user}"
                    update(f"{prefix} ({step + 1}/{steps})", (step + 1) / steps)
                    time.sleep(delay)
            return task

        skill_tasks = {
            'Agility': 'Executing agility routine',
            'Fletching': 'Training fletching',
            'Mining': 'Mining resources',
        }
        for name, description in skill_tasks.items():
            self.controller.register_task(name, build_task(description, steps=12, delay=0.6), category='skill')

        location_tasks = {
            'Lumbridge': 'Navigating to Lumbridge',
            'Varrock': 'Travelling to Varrock',
            'GE': 'Heading to the Grand Exchange',
        }
        for name, description in location_tasks.items():
            self.controller.register_task(name, build_task(description, steps=6, delay=0.8), category='location')

    def on_close(self):
        self.controller.stop_all()
        self.login_launcher.terminate()
        self.master.destroy()

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
window = MainWindow(root, accounts, active_user, usernames)
root.mainloop()
