# Windows Keylogger

Simple keylogger that records keystrokes and saves them to a `.txt` file when you stop it.

## Visibility

Use the `--mode` argument to choose visibility:

- **`visible`** (default) – Console window stays open while logging. Good for testing.
- **`invisible`** – Runs without opening a window. Still appears in Task Manager.

Both modes save keystrokes to a timestamped `.txt` file in the current directory (or `--output-dir`) when you stop the program (Ctrl+C or close the console).

## Installation

Install once from the **project root** (parent of `windows`):

```powershell
cd "d:\Projects\keylogger software"
pip install -r requirements.txt
```

Or only for keylogger: `pip install pynput`

## Run

From the **project root**:

```powershell
# Visible (console window) – press Ctrl+C to stop and save
python keylogger.py
python keylogger.py --mode visible

# Invisible (no window)
python keylogger.py --mode invisible
```

You can also run from the `windows` folder: `python keylogger.py` (it will use the root keylogger).

Log file name format: `DD-MM-YYYY|HH:MM.txt` (e.g. `17-02-2025|14-30.txt`).

## Optional: output directory

```powershell
python keylogger.py --output-dir C:\Logs
```

---

Please note: for educational purposes only. Use only on systems you are authorized to monitor.
