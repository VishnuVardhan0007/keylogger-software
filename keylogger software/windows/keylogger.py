"""Run the keylogger from project root. Install deps from root: pip install -r requirements.txt"""
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
os.chdir(_root)

from keylogger import main

if __name__ == "__main__":
    main()
