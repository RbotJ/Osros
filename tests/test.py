import tkinter as tk
import sys
import os
import psutil
import subprocess
import pyautogui

def is_runelite_running():
    for process in psutil.process_iter(['exe']):
        if process.info['exe'] and 'RuneLite.exe' in process.info['exe']:
            return True
    return False

def update_status():
    if is_runelite_running():
        status_label.config(text="Link Ready")
        open_runelite_button.pack_forget()
        login_button.pack(pady=10)  # Show the Login button
    else:
        status_label.config(text="Not Found")
        open_runelite_button.pack(pady=10)
        login_button.pack_forget()  # Hide the Login button

def open_runelite():
    os.startfile('C:/Users/jarec/AppData/Local/RuneLite/RuneLite.exe')
    root.after(2000, update_status)

def run_login_script():
    subprocess.run(["python", "Login.py"])
    login_status_label.config(text="Login Status: Online")

active_user = sys.argv[1] if len(sys.argv) > 1 else "Unknown User"

root = tk.Tk()
root.title("RuneLabs")
root.geometry("300x200")
root.attributes('-topmost', True)

welcome_label = tk.Label(root, text=f"Welcome {active_user}")
welcome_label.pack(pady=10)

status_label = tk.Label(root, text="")
status_label.pack(pady=10)

open_runelite_button = tk.Button(root, text="Open RuneLite", command=open_runelite)

# Add a Login button
login_button = tk.Button(root, text="Login", command=run_login_script)
login_status_label = tk.Label(root, text="")
login_status_label.pack(pady=10)

update_status()

root.mainloop()
