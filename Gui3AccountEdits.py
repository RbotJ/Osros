import tkinter as tk
import os
from dotenv import load_dotenv, set_key

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

def save_accounts(accounts):
    for account, data in accounts.items():
        for field, value in data.items():
            set_key('.env', f"{account.upper()}_{field.upper()}", value)

def on_select_account():
    selected_account = account_var.get()
    if selected_account in accounts:
        username_var.set(accounts[selected_account]['username'])
        password_var.set(accounts[selected_account]['password'])
        login_var.set(accounts[selected_account]['login'])

def on_save_account():
    selected_account = account_var.get()
    if selected_account:
        accounts[selected_account] = {
            'username': username_var.get(),
            'password': password_var.get(),
            'login': login_var.get()
        }
        save_accounts(accounts)

def on_back_click():
    root.destroy()
    os.system("python GUI2AccountSelection.py")

accounts = load_accounts()

root = tk.Tk()
root.title("RuneLabs")

# Set the size of the window
root.geometry("300x200")
# Set the GUI to be on top by default
root.attributes('-topmost', True)

account_var = tk.StringVar()
username_var = tk.StringVar()
password_var = tk.StringVar()
login_var = tk.StringVar()

tk.Label(root, text="Select An Account->").grid(row=0, column=0, padx=5, pady=5)
account_optionmenu = tk.OptionMenu(root, account_var, *accounts.keys(), command=lambda _: on_select_account())
account_optionmenu.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Username").grid(row=1, column=0, padx=5, pady=5)
username_entry = tk.Entry(root, textvariable=username_var)
username_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="Password").grid(row=2, column=0, padx=5, pady=5)
password_entry = tk.Entry(root, textvariable=password_var)
password_entry.grid(row=2, column=1, padx=5, pady=5)

tk.Label(root, text="Login").grid(row=3, column=0, padx=5, pady=5)
login_entry = tk.Entry(root, textvariable=login_var)
login_entry.grid(row=3, column=1, padx=5, pady=5)

save_button = tk.Button(root, text="Save", command=on_save_account)
save_button.grid(row=4, column=0, padx=5, pady=10)

back_button = tk.Button(root, text="Back", command=on_back_click)
back_button.grid(row=4, column=1, padx=5, pady=10)

root.mainloop()
