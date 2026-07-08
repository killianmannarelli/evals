import sys, os
from pathlib import Path
# make `src` and `checks` importable when running `pytest` from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
