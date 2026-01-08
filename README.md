# Don’t Touch the Spikes Online

Multiplayer (2–4 players) online version of **Don’t Touch the Spikes**, written in Python.  
Players compete in a free-for-all arena, trying to survive while avoiding spikes.

---

## Features

- TCP socket-based online multiplayer
- Free-for-all gameplay (2–4 players)
- Authoritative server handles collisions and game state
- Minimalistic graphics for fast gameplay
- Cross-platform (Python 3)

---

HOW TO RUN "DON'T TOUCH THE SPIKES ONLINE"

1. Install Python 3.8 or higher
   Make sure Python is added to your system PATH.

2. Install required packages
   Open terminal / PowerShell in the project root folder and run:

       pip install -r requirements.txt

   If pip is not recognized, run:

       python -m pip install -r requirements.txt

3. Start the server
   run:
       python serverLogic.py
   The server will start and listen for incoming client connections.

4. Start the client
    run:
       python clientLogic.py
    remember to enter the server IP address and port number.
    and to run the client at least 2 computers.
5. Play the game
   - Players move automatically; tap to flap
   - Avoid spikes; touching one means death
   - Last player alive wins
   - Works for 2–4 players in free-for-all mode

6. Notes
   - The server is authoritative: all collisions and scoring are handled on the server.
   - Works best over LAN or public server (port forwarding may be required for online play).
   - __pycache__ and temporary files are ignored by .gitignore.


## Requirements

- Python 3.7+  
- Recommended libraries (install via pip):

```bash
pip install -r requirements.txt
