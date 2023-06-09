import tkinter as tk
import sys
import os
import psutil

def is_runelite_running():
    for process in psutil.process_iter(['exe']):
        if process.info['exe'] and 'RuneLite.exe' in process.info['exe']:
            return True
    return False

def update_status():
    if is_runelite_running():
        status_label.config(text="Link Ready")
        open_runelite_button.pack_forget()
    else:
        status_label.config(text="Not Found")
        open_runelite_button.pack(pady=10)

def open_runelite():
    # Replace 'path/to/RuneLite' with the actual path to the RuneLite executable
    os.startfile('C:/Users/jarec/AppData/Local/RuneLite/RuneLite.exe')
    root.after(2000, update_status)

active_user = sys.argv[1] if len(sys.argv) > 1 else "Unknown User"

root = tk.Tk()
root.title("RuneLabs")
# Set the size of the window
root.geometry("300x200")
# Set the GUI to be on top by default
root.attributes('-topmost', True)

welcome_label = tk.Label(root, text=f"Welcome {active_user}")
welcome_label.pack(pady=10)

status_label = tk.Label(root, text="")
status_label.pack(pady=10)

open_runelite_button = tk.Button(root, text="Open RuneLite", command=open_runelite)

update_status()

root.mainloop()
