import pygetwindow as gw

windows = gw.getAllWindows()

for window in windows:
    print(window.title)
