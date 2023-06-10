import tkinter as tk
import os
from dotenv import load_dotenv

def load_accounts():
    load_dotenv()
    accounts = {
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
    return accounts

def get_usernames(accounts):
    return [account_info['username'] for account_info in accounts.values()]

def on_username_click(username):
    root.destroy()
    os.system(f"python GUI.py {username}")

def on_add_remove_click():
    root.destroy()
    os.system("python Gui3AccountEdits.py")

accounts = load_accounts()
usernames = get_usernames(accounts)

root = tk.Tk()
root.title("RuneLabs")
# Set the size of the window
root.geometry("300x200")
# Set the GUI to be on top by default
root.attributes('-topmost', True)

label = tk.Label(root, text="Please Select or Add an Account")
label.pack(pady=10)

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

for idx, username in enumerate(usernames[:3]):
    button = tk.Button(button_frame, text=username, command=lambda u=username: on_username_click(u))
    button.grid(row=0, column=idx, padx=5)

add_remove_button = tk.Button(root, text="Add/Remove", command=on_add_remove_click)
add_remove_button.pack(pady=10)

root.mainloop()
