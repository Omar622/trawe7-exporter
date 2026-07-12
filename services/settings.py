"""Persist cut-detection settings to a per-user JSON file."""
import json
from pathlib import Path

DEFAULTS = {
    "silence_threshold": -30,   # dB (formatted to "-30dB" at the ffmpeg call site)
    "min_silence": 0.5,         # seconds
    "min_segment": 10.0,        # seconds
}

SETTINGS_PATH = Path.home() / ".config" / "taraweeh-cutter" / "settings.json"


def load_settings() -> dict:
    """Return DEFAULTS overlaid with any saved values; defaults on missing/corrupt file."""
    settings = dict(DEFAULTS)
    try:
        stored = json.loads(SETTINGS_PATH.read_text())
        for key in DEFAULTS:
            if key in stored:
                settings[key] = stored[key]
    except (OSError, ValueError):
        pass
    return settings


def save_settings(values: dict) -> bool:
    """Write the known keys of `values` to SETTINGS_PATH. Returns True on success."""
    data = {key: values[key] for key in DEFAULTS if key in values}
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(data, indent=2))
        return True
    except OSError:
        return False
