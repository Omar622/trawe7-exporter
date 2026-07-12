"""Generate placeholder PNG icons (light + dark) into resources/icons/.

Run: uv run python scripts/gen_icons.py
Swap the output for hand-drawn assets later without touching app code.
"""
import os

from PIL import Image, ImageDraw

SIZE = 128
M = 26  # margin
OUT = os.path.join(os.path.dirname(__file__), "..", "resources", "icons")

GREEN, RED, ACCENT = "#16a34a", "#dc2626", "#0ea5a4"
STROKE = {"light": "#22314f", "dark": "#e9eef7"}


def _w() -> int:
    return max(7, SIZE // 13)


def _canvas():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def play(d, c):
    d.polygon([(M + 6, M), (M + 6, SIZE - M), (SIZE - M, SIZE // 2)], fill=c)


def pause(d, c):
    bw = SIZE // 6
    d.rounded_rectangle([M + 6, M, M + 6 + bw, SIZE - M], radius=6, fill=c)
    d.rounded_rectangle([SIZE - M - bw, M, SIZE - M, SIZE - M], radius=6, fill=c)


def import_file(d, c):
    d.rounded_rectangle([M + 8, M - 4, SIZE - M - 8, SIZE - M + 4], radius=10, outline=c, width=_w())
    cx = SIZE // 2
    d.line([cx, SIZE // 2 - 12, cx, SIZE - M - 10], fill=c, width=_w())
    d.line([cx - 14, SIZE - M - 24, cx, SIZE - M - 10], fill=c, width=_w())
    d.line([cx + 14, SIZE - M - 24, cx, SIZE - M - 10], fill=c, width=_w())


def import_folder(d, c):
    w = _w()
    d.line([M, M + 16, M + 26, M + 16], fill=c, width=w)
    d.line([M + 26, M + 16, M + 34, M + 26], fill=c, width=w)
    d.rounded_rectangle([M, M + 22, SIZE - M, SIZE - M], radius=10, outline=c, width=w)


def set_begin(d, _c):
    w = _w()
    x = M + 10
    d.line([x, M, x, SIZE - M], fill=GREEN, width=w)
    d.line([x, M, x + 22, M], fill=GREEN, width=w)
    d.line([x, SIZE - M, x + 22, SIZE - M], fill=GREEN, width=w)


def set_end(d, _c):
    w = _w()
    x = SIZE - M - 10
    d.line([x, M, x, SIZE - M], fill=RED, width=w)
    d.line([x, M, x - 22, M], fill=RED, width=w)
    d.line([x, SIZE - M, x - 22, SIZE - M], fill=RED, width=w)


def add_cut(d, _c):
    w = _w()
    cx = cy = SIZE // 2
    d.line([cx, M, cx, SIZE - M], fill=GREEN, width=w)
    d.line([M, cy, SIZE - M, cy], fill=GREEN, width=w)


def remove_cut(d, _c):
    w = max(6, _w() - 2)
    d.line([M + 6, M + 14, SIZE - M - 6, M + 14], fill=RED, width=w)   # lid
    d.line([SIZE // 2 - 12, M + 4, SIZE // 2 + 12, M + 4], fill=RED, width=w)  # handle
    d.rounded_rectangle([M + 14, M + 20, SIZE - M - 14, SIZE - M], radius=8, outline=RED, width=w)


def restore(d, c):
    w = _w()
    d.arc([M, M, SIZE - M, SIZE - M], start=40, end=320, fill=c, width=w)
    ax, ay = SIZE - M - 8, M + 20
    d.line([ax, ay, ax + 4, ay - 20], fill=c, width=w)
    d.line([ax, ay, ax + 22, ay - 4], fill=c, width=w)


def export(d, c):
    w = _w()
    cx = SIZE // 2
    d.line([cx, M, cx, SIZE // 2 + 10], fill=ACCENT, width=w)
    d.line([cx - 16, SIZE // 2 - 6, cx, SIZE // 2 + 10], fill=ACCENT, width=w)
    d.line([cx + 16, SIZE // 2 - 6, cx, SIZE // 2 + 10], fill=ACCENT, width=w)
    d.line([M, SIZE // 2 + 4, M, SIZE - M], fill=c, width=w)
    d.line([SIZE - M, SIZE // 2 + 4, SIZE - M, SIZE - M], fill=c, width=w)
    d.line([M, SIZE - M, SIZE - M, SIZE - M], fill=c, width=w)


def theme(d, c):
    d.ellipse([M, M, SIZE - M, SIZE - M], outline=c, width=_w())
    d.pieslice([M, M, SIZE - M, SIZE - M], start=90, end=270, fill=c)


def language(d, c):
    w = max(5, _w() - 2)
    box = [M, M, SIZE - M, SIZE - M]
    d.ellipse(box, outline=c, width=w)
    cx = SIZE // 2
    d.ellipse([cx - 16, M, cx + 16, SIZE - M], outline=c, width=w)
    d.line([M, SIZE // 2, SIZE - M, SIZE // 2], fill=c, width=w)


ICONS = {
    "import_file": import_file, "import_folder": import_folder,
    "play": play, "pause": pause, "set_begin": set_begin, "set_end": set_end,
    "add_cut": add_cut, "remove_cut": remove_cut, "restore": restore,
    "export": export, "theme": theme, "language": language,
}


def main():
    for mode, stroke in STROKE.items():
        target = os.path.join(OUT, mode)
        os.makedirs(target, exist_ok=True)
        for name, draw in ICONS.items():
            img, d = _canvas()
            draw(d, stroke)
            img.save(os.path.join(target, f"{name}.png"))
    print(f"Wrote {len(ICONS) * 2} icons under {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
