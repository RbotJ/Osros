import pygetwindow as gw

title = "RuneLite"
window = gw.getWindowsWithTitle(title)[0]  # get the first window with this title

print(window.left, window.top, window.width, window.height)
