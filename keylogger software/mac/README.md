# Mac Keylogger

Simple keylogger that records keystrokes and saves them to a `.txt` file when you stop it.

**Note:** On macOS it does not capture secure input (e.g. password fields). You may need to grant **Accessibility** (and optionally **Input Monitoring**) permissions in System Preferences → Privacy & Security.

## Installation

From project root: `pip install -r requirements.txt`  
Or only for keylogger: `pip install pynput`

## How to run it

Run from the project root.

**Foreground:**

```bash
python3 keylogger.py
```

Press Ctrl+C to stop and save the log.

**Background:**

```bash
nohup python3 keylogger.py --mode invisible &
```

Stop with `fg` then Ctrl+C, or `kill <PID>`.

Log file name format: `DD-MM-YYYY|HH:MM.txt` in the current directory (or use `--output-dir`).

---

Please note: for educational purposes only. Use only on systems you are authorized to monitor.
