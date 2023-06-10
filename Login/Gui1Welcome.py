import tkinter as tk
import os

# Define a function to close the current window and open Gui2AccountSelection.py
def link_start_action():
    window.destroy()
    os.system("python Gui2AccountSelection.py")

# Define a function for the initial screen
def show_initial_screen():
    # Create the welcome label
    welcome_label = tk.Label(window, text="Welcome to RuneLab")
    welcome_label.pack(pady=20)

    # Create the Link Start button
    link_start_button = tk.Button(window, text="Link Start", command=link_start_action)
    link_start_button.pack(pady=10)

# Create the main window
window = tk.Tk()

# Set the title of the window
window.title("RuneLab")

# Set the size of the window
window.geometry("300x200")

# Set the GUI to be on top by default
window.attributes('-topmost', True)

# Show the initial screen
show_initial_screen()

# Start the main event loop
window.mainloop()
