Project Title: Game Assistance Overlay
====================================

Overview
--------

This project aims to develop a Python script that can analyze an application window (in this case, a game), understand the state of the game, and suggest where a user should move their mouse and click by providing an overlay. This should be helpful to players in determining where to move their characters in a visually complex game.

Components
----------

- Game State Recognition - Using computer vision (OpenCV, possibly machine learning libraries like TensorFlow or PyTorch) to recognize the current state of the game based on the visuals presented in the game window.
- Path Planning - Determine where the user should click next. This could involve hard-coded paths or dynamically computed paths using algorithms like A* or Dijkstra's algorithm.
- Overlay Generation - A GUI (using PyQt or Tkinter) that generates an overlay showing where the user should click next.
- Real-time Interaction - The system needs to operate in real-time, continuously monitoring, understanding, planning, and updating.
- User Control - A control system for the user to turn the system on/off and adjust settings.

Credential Management
---------------------

Sensitive information such as account usernames and passwords must never be committed to source control. Create a personal `.env` file (ignored by Git) alongside `Login.py` with the users you want the automation to know about:

```
# .env (do not commit)
USER1=DisplayName
LOGIN1=login@example.com
USER2=AltAccount
LOGIN2=alt@example.com

# Optional – select which profile to use
ACTIVE_USER=User1

# Optional – override the keyring service name (default is "Osros")
# OSROS_KEYRING_SERVICE=Osros
```

Passwords are stored securely in the operating system keychain via the [`keyring`](https://pypi.org/project/keyring/) library. Configure each login once (repeat for every `LOGINx` value) using:

```
python -m keyring set Osros login@example.com
```

On Windows this command writes to the Windows Credential Manager; on macOS it stores the secret in the Keychain; on Linux it integrates with SecretService/KWallet when available. Credentials are only decrypted in memory at the moment the automation types them into the client.

Development Approach
--------------------

We follow an Agile development approach, with the work divided into sprints. Each sprint has a specific set of tasks, and the goal is to have a working (though not necessarily complete) system at the end of each sprint.

Sprint Plan
-----------

1. Research and learn about the necessary libraries (OpenCV, PyQt/Tkinter, etc.).
2. Set up a basic system that can capture and display the game window.
3. Implement basic state recognition for a subset of the game states.
4. Expand the state recognition to include all states.
5. Implement basic path planning for a subset of the game states.
6. Expand the path planning to include all states.
7. Implement the overlay system.
8. Implement user controls.
9. Testing and bug fixing.
