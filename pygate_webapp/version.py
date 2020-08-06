try:
    with open("VERSION") as f:
        version = f.read().strip()
except Exception:
    version = "0.0.1"

__version__ = version