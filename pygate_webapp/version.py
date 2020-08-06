import os

this_dir = os.path.abspath(os.path.dirname(__file__))

try:
    with open(os.path.join(this_dir, "VERSION")) as f:
        version = f.read().strip()
except Exception:
    version = "0.0.1"

__version__ = version