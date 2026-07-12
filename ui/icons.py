"""Loads bundled PNG icons as Tk images, with a unicode-glyph fallback."""
import os
from typing import Dict, Optional, Tuple

try:
    from PIL import Image, ImageTk
    _PIL = True
except ImportError:
    _PIL = False

# Fallback glyphs when a PNG or Pillow is unavailable.
GLYPHS = {
    "import_file": "📄", "import_folder": "📁", "play": "▶", "pause": "⏸",
    "set_begin": "⟤", "set_end": "⟥", "add_cut": "＋", "remove_cut": "🗑",
    "restore": "↺", "export": "⬇", "theme": "◐", "language": "🌐",
}


class IconLoader:
    """Caches PhotoImage refs (Tk garbage-collects images without a live reference)."""

    def __init__(self, base_dir: str, mode: str = "light"):
        self.base_dir = base_dir
        self.mode = mode
        self._cache: Dict[Tuple[str, int, int], object] = {}

    def get(self, name: str, size: Tuple[int, int] = (18, 18)):
        if not _PIL:
            return None
        key = (name, size[0], size[1])
        if key in self._cache:
            return self._cache[key]
        path = os.path.join(self.base_dir, self.mode, f"{name}.png")
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        except Exception:
            return None
        self._cache[key] = photo
        return photo

    def glyph(self, name: str) -> str:
        return GLYPHS.get(name, "")
