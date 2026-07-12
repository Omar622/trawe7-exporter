"""Light/dark palettes for canvas colors.

ttkbootstrap owns widget theming (via bootstyle); this only supplies the colors
ttk does not manage (the waveform Canvas). Treeview sizing lives in the window
so it survives theme switches.
"""
THEMES = {"light": "flatly", "dark": "darkly"}

PALETTES = {
    "light": {
        "wave_bg": "#eef1f6", "wave_grid": "#c3cad9", "wave": "#2c7a7b",
        "playhead": "#dc2626", "accent": "#0e7490", "ok": "#16a34a",
        "cut": "#f59e0b",
    },
    "dark": {
        "wave_bg": "#20232a", "wave_grid": "#3a3f4b", "wave": "#4fd1c5",
        "playhead": "#f87171", "accent": "#38bdf8", "ok": "#22c55e",
        "cut": "#fbbf24",
    },
}


def theme_name(mode: str) -> str:
    return THEMES.get(mode, "flatly")


def palette_for(mode: str) -> dict:
    return PALETTES.get(mode, PALETTES["light"])


def apply_custom_styles(root, mode: str = "light") -> dict:
    """Return the active palette (canvas colors ttk doesn't manage)."""
    return palette_for(mode)
