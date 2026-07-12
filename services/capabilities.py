"""Runtime capability detection, computed once."""
import shutil
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class AppCapabilities:
    ffmpeg: bool      # ffmpeg + ffprobe on PATH
    playback: bool    # pygame importable
    pillow: bool      # Pillow importable


@lru_cache(maxsize=1)
def detect_capabilities() -> AppCapabilities:
    return AppCapabilities(
        ffmpeg=bool(shutil.which("ffmpeg") and shutil.which("ffprobe")),
        playback=_importable("pygame"),
        pillow=_importable("PIL"),
    )


def _importable(module: str) -> bool:
    try:
        __import__(module)
    except ImportError:
        return False
    return True
