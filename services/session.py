"""Persist the app's last session so it reopens where the user left off."""
import json
from pathlib import Path

SESSION_PATH = Path.home() / ".config" / "taraweeh-cutter" / "session.json"


def load_session() -> dict:
    """Return the saved session dict, or {} if missing/corrupt."""
    try:
        return json.loads(SESSION_PATH.read_text())
    except (OSError, ValueError):
        return {}


def save_session(data: dict) -> bool:
    try:
        SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
        SESSION_PATH.write_text(json.dumps(data, indent=2))
        return True
    except OSError:
        return False
