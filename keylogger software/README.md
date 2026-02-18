# A simple keylogger for Windows, Linux and Mac

A keylogger records your keystrokes and saves them in a log file on your local computer. This project provides simple, bare-bones keyloggers for the major operating systems.

**Check the README in each platform folder for up-to-date install and run instructions.**

## Contents

- [Windows installation guide](windows/README.md)
- [Linux installation guide](linux/README.md)
- [Mac installation guide](mac/README.md)

---

## Windows

Use the `--mode` argument to set visibility:

- **`visible`** (default) – Console window stays open while logging. Good for testing.
- **`invisible`** – Runs without opening a window. Still visible in Task Manager.

Both save keystrokes to a timestamped `.txt` file when you stop the program (Ctrl+C or close the console).

From project root:
```powershell
pip install -r requirements.txt
python keylogger.py
# or: python keylogger.py --mode invisible
```

---

## Linux

From project root: `pip install -r requirements.txt`

### How to run it

Run in the background with `nohup` and `&` so it keeps logging after you close the terminal:

```bash
nohup python3 keylogger.py --mode invisible &
```

You'll see a process ID (PID). The keylogger is now running and will log keystrokes to a `.txt` file.

**Stop it:** `fg` then Ctrl+C, or `kill <PID>` (e.g. `kill 12529`).

See [linux/README.md](linux/README.md) for full details.

---

## Mac

On macOS the Python keylogger may not capture secure input (e.g. password fields). You may need to grant Accessibility (and optionally Input Monitoring) permissions.

From project root: `pip install -r requirements.txt` then `python keylogger.py`

See [mac/README.md](mac/README.md) for details.

---

## In-app only (encrypted) option

An **in-app only** desktop app is in the `app/` folder. It records keystrokes **only inside its own window** (no system-wide capture), stores them encrypted in SQLite, and includes a viewer to decrypt and browse logs. Useful for consent-based use (e.g. typing practice, local audits).

```bash
pip install -r requirements.txt   # from project root (cryptography)
python -m app
```

See the `app/` package and root `requirements.txt` for that setup.

---

## Uses

Some uses of a keylogger are:

- Personal control and file backup: know if someone used your computer while you were away.
- Self-analysis (e.g. typing habits).

---

## License and disclaimer

This repo is for **educational purposes only**. No contributors are responsible for how this program is used. Use only on systems you are authorized to monitor and in accordance with local laws.

Distributed under the MIT license. See [LICENSE.txt](LICENSE.txt) for details.
