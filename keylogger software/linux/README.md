# Linux Keylogger

Simple keylogger that records keystrokes and saves them to a `.txt` file when you stop it.

## Installation

From project root: `pip install -r requirements.txt`  
Or only for keylogger: `pip install pynput`

## How to run it

Run from the project root.

**Foreground (visible):**

```bash
python3 keylogger.py
```

Press Ctrl+C to stop and save the log.

**Background (invisible):**

Using `nohup` and `&` runs the keylogger in the background so it keeps logging after you close the terminal:

```bash
nohup python3 keylogger.py --mode invisible &
```

You'll see something like:

```
[1] 12529   # this is the keylogger's PID (process ID)
```

The keylogger is now running and will log keystrokes to a timestamped `.txt` file in the current directory.

**Stop it:**

- Bring to foreground and then Ctrl+C:
  ```bash
  fg
  # then press Ctrl+C
  ```
- Or kill by PID:
  ```bash
  kill 12529
  ```

Log file name format: `DD-MM-YYYY|HH:MM.txt` (e.g. `17-02-2025|14-30.txt`).

---

Please note: for educational purposes only. Use only on systems you are authorized to monitor.
