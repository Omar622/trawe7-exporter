"""Interactive waveform: peaks, editable segment bands, and a playhead.

Draws the wave for the visible viewport only (so zoom stays cheap on long files),
supports edge-drag resize, right-click split/remove/create, and zoom."""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Tuple

AMPLITUDE = 0.72          # <1 flattens the wave so it reads calmer
BASE_PPS = 4              # pixels per second at zoom 1.0
ZOOM_MIN, ZOOM_MAX = 1.0, 40.0
MAX_CONTENT = 600_000     # cap canvas content width
GRAB_PX = 6               # edge grab tolerance
MIN_SEG = 0.15            # min segment while dragging (seconds)
MERGE_EPS = 0.05          # edges this close read as "touching"


class WaveformView(tk.Frame):
    def __init__(self, master, palette: dict,
                 on_seek: Optional[Callable[[float], None]] = None,
                 on_edit: Optional[Callable[[int, float, float], None]] = None,
                 on_split: Optional[Callable[[int, float], None]] = None,
                 on_remove: Optional[Callable[[int], None]] = None,
                 on_create: Optional[Callable[[float], None]] = None):
        super().__init__(master)
        self._palette = palette
        self._on_seek, self._on_edit = on_seek, on_edit
        self._on_split, self._on_remove, self._on_create = on_split, on_remove, on_create
        self._peaks: List[float] = []
        self._duration = 0.0
        self._cuts: List[Dict] = []          # {"id","start","end"}
        self._playhead = 0.0
        self._playhead_id: Optional[int] = None
        self._resize_job: Optional[str] = None
        self._wave_job: Optional[str] = None
        self._cw = 0
        self._zoom = 1.0
        self._drag: Optional[Tuple[int, str]] = None
        self._merge_hint: Optional[int] = None
        self._labels = {"split": "Split here", "remove": "Remove", "create": "Create segment here"}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, height=180, highlightthickness=0, bg=palette["wave_bg"])
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.hbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.hbar.grid_remove()
        self.canvas.configure(xscrollcommand=self._on_xscroll)

        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_hover)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Shift-MouseWheel>", lambda e: self.canvas.xview_scroll(-1 if e.delta > 0 else 1, "units"))
        self.canvas.bind("<Shift-Button-4>", lambda e: self.canvas.xview_scroll(-3, "units"))
        self.canvas.bind("<Shift-Button-5>", lambda e: self.canvas.xview_scroll(3, "units"))
        self.canvas.bind("<Control-MouseWheel>", lambda e: self.zoom_by(1.2 if e.delta > 0 else 1 / 1.2, e.x))
        self.canvas.bind("<Control-Button-4>", lambda e: self.zoom_by(1.2, e.x))
        self.canvas.bind("<Control-Button-5>", lambda e: self.zoom_by(1 / 1.2, e.x))

    # --- public API ---
    def set_peaks(self, peaks: List[float], duration: float) -> None:
        self._peaks = peaks or []
        self._duration = max(0.0, duration)
        self._zoom = 1.0
        self.canvas.xview_moveto(0)
        self._redraw()

    def set_cuts(self, cuts: List[Tuple[int, float, float]]) -> None:
        self._cuts = [{"id": i, "start": s, "end": e} for (i, s, e) in cuts]
        self._draw_cuts()

    def set_labels(self, split: str, remove: str, create: str) -> None:
        self._labels = {"split": split, "remove": remove, "create": create}

    def set_playhead(self, seconds: float) -> None:
        self._playhead = max(0.0, seconds)
        self._draw_playhead()
        self._follow_playhead()

    def set_palette(self, palette: dict) -> None:
        self._palette = palette
        self.canvas.configure(bg=palette["wave_bg"])
        self._redraw()

    def clear(self) -> None:
        self._peaks, self._cuts = [], []
        self._duration, self._playhead, self._zoom = 0.0, 0.0, 1.0
        self._redraw()

    def zoom_by(self, mult: float, center_x: Optional[int] = None) -> None:
        new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, self._zoom * mult))
        if abs(new_zoom - self._zoom) < 1e-6 or self._duration <= 0:
            return
        view_w, _ = self._view_size()
        cx = center_x if center_x is not None else view_w / 2
        t_center = self._x_to_time(self.canvas.canvasx(cx))
        self._zoom = new_zoom
        self._redraw()
        self.canvas.xview_moveto(max(0.0, (self._time_to_x(t_center) - cx) / self._cw))

    # --- geometry ---
    def _view_size(self) -> Tuple[int, int]:
        return self.canvas.winfo_width(), self.canvas.winfo_height()

    def _content_width(self, view_w: int) -> int:
        if self._duration <= 0:
            return max(view_w, 1)
        return max(view_w, min(int(self._duration * BASE_PPS * self._zoom), MAX_CONTENT))

    def _time_to_x(self, t: float) -> float:
        return 0 if self._duration <= 0 else t / self._duration * self._cw

    def _x_to_time(self, x: float) -> float:
        return 0.0 if self._cw <= 0 else max(0.0, min(self._duration, x / self._cw * self._duration))

    # --- hit testing ---
    def _hit_edge(self, cx: float) -> Optional[Tuple[int, str]]:
        for c in self._cuts:
            if abs(cx - self._time_to_x(c["start"])) <= GRAB_PX:
                return c["id"], "start"
            if abs(cx - self._time_to_x(c["end"])) <= GRAB_PX:
                return c["id"], "end"
        return None

    def _hit_segment(self, cx: float) -> Optional[int]:
        for c in self._cuts:
            if self._time_to_x(c["start"]) <= cx <= self._time_to_x(c["end"]):
                return c["id"]
        return None

    def _neighbors(self, cid: int):
        ordered = sorted(self._cuts, key=lambda c: c["start"])
        idx = next((k for k, c in enumerate(ordered) if c["id"] == cid), None)
        if idx is None:
            return None, None, None
        return (ordered[idx],
                ordered[idx - 1] if idx > 0 else None,
                ordered[idx + 1] if idx < len(ordered) - 1 else None)

    # --- mouse ---
    def _on_press(self, event):
        if self._duration <= 0:
            return
        cx = self.canvas.canvasx(event.x)
        edge = self._hit_edge(cx)
        if edge:
            self._drag = edge
        else:
            self._drag = None
            if self._on_seek:
                self._on_seek(self._x_to_time(cx))

    def _on_drag(self, event):
        cx = self.canvas.canvasx(event.x)
        if not self._drag:
            if self._on_seek and self._duration > 0:
                self._on_seek(self._x_to_time(cx))
            return
        cid, side = self._drag
        cut, prev, nxt = self._neighbors(cid)
        if not cut:
            return
        t = self._x_to_time(cx)
        if side == "start":
            lo = prev["end"] if prev else 0.0
            cut["start"] = max(lo, min(t, cut["end"] - MIN_SEG))
            self._merge_hint = prev["id"] if prev and abs(cut["start"] - prev["end"]) <= MERGE_EPS else None
        else:
            hi = nxt["start"] if nxt else self._duration
            cut["end"] = min(hi, max(t, cut["start"] + MIN_SEG))
            self._merge_hint = nxt["id"] if nxt and abs(cut["end"] - nxt["start"]) <= MERGE_EPS else None
        self._draw_cuts()

    def _on_release(self, _event):
        if not self._drag:
            return
        cid, _side = self._drag
        self._drag, self._merge_hint = None, None
        cut = next((c for c in self._cuts if c["id"] == cid), None)
        if cut and self._on_edit:
            self._on_edit(cut["id"], cut["start"], cut["end"])

    def _on_hover(self, event):
        if self._drag or self._duration <= 0:
            return
        over_edge = self._hit_edge(self.canvas.canvasx(event.x)) is not None
        self.canvas.configure(cursor="sb_h_double_arrow" if over_edge else "")

    def _on_right_click(self, event):
        if self._duration <= 0:
            return
        cx = self.canvas.canvasx(event.x)
        t = self._x_to_time(cx)
        seg = self._hit_segment(cx)
        menu = tk.Menu(self, tearoff=0)
        if seg is not None:
            menu.add_command(label=self._labels["split"],
                             command=lambda: self._on_split and self._on_split(seg, t))
            menu.add_command(label=self._labels["remove"],
                             command=lambda: self._on_remove and self._on_remove(seg))
        else:
            menu.add_command(label=self._labels["create"],
                             command=lambda: self._on_create and self._on_create(t))
        menu.tk_popup(event.x_root, event.y_root)

    def _on_xscroll(self, lo, hi):
        self.hbar.set(lo, hi)
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.hbar.grid_remove()
        else:
            self.hbar.grid()
        self._schedule_wave()

    def _on_configure(self, _event):
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(60, self._redraw)

    # --- drawing ---
    def _redraw(self):
        self._resize_job = None
        self.canvas.delete("all")
        self._playhead_id = None
        view_w, height = self._view_size()
        if view_w <= 1 or height <= 1:
            return
        self._cw = self._content_width(view_w)
        self.canvas.configure(scrollregion=(0, 0, self._cw, height))
        mid = height / 2
        self.canvas.create_line(0, mid, self._cw, mid, fill=self._palette["wave_grid"], tags="grid")
        if not self._peaks:
            self.canvas.create_text(view_w / 2, mid, text="—", fill=self._palette["wave_grid"])
        self._draw_cuts()
        self._draw_playhead()
        self._draw_wave_viewport()

    def _schedule_wave(self):
        if self._wave_job:
            self.after_cancel(self._wave_job)
        self._wave_job = self.after(20, self._draw_wave_viewport)

    def _draw_wave_viewport(self):
        self._wave_job = None
        self.canvas.delete("wave")
        view_w, height = self._view_size()
        if view_w <= 1 or height <= 1 or not self._peaks or self._cw <= 0:
            return
        mid = height / 2
        half = (mid - 6) * AMPLITUDE
        n = len(self._peaks)
        color = self._palette["wave"]
        x_lo = max(0, int(self.canvas.canvasx(0)) - 2)
        x_hi = min(self._cw, int(self.canvas.canvasx(view_w)) + 2)
        for x in range(x_lo, x_hi):
            lo = int(x / self._cw * n)
            hi = max(lo + 1, int((x + 1) / self._cw * n))
            peak = max(self._peaks[lo:hi]) if hi > lo else self._peaks[lo]
            self.canvas.create_line(x, mid - peak * half, x, mid + peak * half, fill=color, tags="wave")
        self.canvas.tag_lower("wave")
        self.canvas.tag_lower("grid")

    def _draw_cuts(self):
        self.canvas.delete("cut")
        _, height = self._view_size()
        if height <= 1 or self._duration <= 0:
            return
        base = self._palette["cut"]
        hint = self._palette["accent"]
        for c in self._cuts:
            x0, x1 = self._time_to_x(c["start"]), self._time_to_x(c["end"])
            fill = hint if c["id"] == self._merge_hint else base
            self.canvas.create_rectangle(x0, 0, x1, height, fill=fill, outline="",
                                         stipple="gray25", tags="cut")
            self.canvas.create_line(x0, 1, x1, 1, fill=base, width=2, tags="cut")
            self.canvas.create_line(x0, height - 1, x1, height - 1, fill=base, width=2, tags="cut")
        self.canvas.tag_raise("playhead")

    def _draw_playhead(self):
        _, height = self._view_size()
        if height <= 1 or self._duration <= 0:
            return
        x = self._time_to_x(self._playhead)
        if self._playhead_id is None:
            self._playhead_id = self.canvas.create_line(
                x, 0, x, height, fill=self._palette["playhead"], width=2, tags="playhead")
        else:
            self.canvas.coords(self._playhead_id, x, 0, x, height)
        self.canvas.tag_raise("playhead")

    def _follow_playhead(self):
        view_w, _ = self._view_size()
        if self._cw <= view_w:
            return
        x = self._time_to_x(self._playhead)
        left, right = self.canvas.canvasx(0), self.canvas.canvasx(view_w)
        if x < left or x > right:
            self.canvas.xview_moveto(max(0.0, (x - view_w / 2) / self._cw))
