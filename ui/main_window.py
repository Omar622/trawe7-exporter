"""Main dashboard window. Pure view: emits events to the controller, exposes
setters/getters for the controller to drive. Holds no domain logic."""
import os
import tkinter as tk
import tkinter.font as tkfont

import ttkbootstrap as tb

try:
    from ttkbootstrap.widgets.tooltip import ToolTip
except ImportError:
    from ttkbootstrap.tooltip import ToolTip

from resources.lang import LANG
from ui.icons import IconLoader
from ui.rtl import shape, shape_wrapped
from ui.styles import apply_custom_styles, theme_name
from ui.waveform_view import WaveformView

ICON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "resources", "icons"))
CHECK_ON, CHECK_OFF = "☑", "☐"
# Best-to-worst UI font. With an Xft Tk this picks crisp DejaVu/Noto; on a core-X
# Tk it falls back to the smooth Type1 "nimbus sans l" (never the bitmap Helvetica).
FONT_PREFS = ("DejaVu Sans", "Noto Sans", "Liberation Sans", "Nimbus Sans", "nimbus sans l")


def _fmt_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class TaraweehCutterApp(tb.Window):
    def __init__(self):
        self.theme_mode = "light"
        super().__init__(themename=theme_name(self.theme_mode))
        self.lang = "en"
        self.controller = None
        self.caps = None

        self.palette = apply_custom_styles(self, self.theme_mode)
        self._title_family = self._configure_fonts()
        self._style_treeview()
        self.icons = IconLoader(ICON_DIR, self.theme_mode)

        self.files = {}            # iid -> {"path", "checked"}
        self.cuts = []             # list of {"start","end","source","export"}
        self._i18n = []            # list of callables that re-apply translated text
        self._icon_buttons = []    # (button, icon_name) for theme re-skinning
        self._duration = 0.0
        self._syncing = False
        self._play_icon = "play"

        self.title(self._t("app_title"))
        self.geometry("1180x740")
        self.minsize(940, 620)
        self._build()

    def _configure_fonts(self):
        """Point the UI at the best available family and return it for the title.
        Only applies a family Tk actually has, so it never falls back to bitmaps."""
        available = {f.lower(): f for f in tkfont.families()}
        family = next((available[p.lower()] for p in FONT_PREFS
                       if p.lower() in available), None)
        if family:
            for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont"):
                try:
                    tkfont.nametofont(name).configure(family=family)
                except tk.TclError:
                    pass
            return family
        return tkfont.nametofont("TkDefaultFont").actual("family")

    def _style_treeview(self):
        # Larger row font makes the ☑/☐ cells (and text) bigger and easier to hit.
        self.style.configure("Treeview", font=(self._title_family, 13), rowheight=34)
        self.style.configure("Treeview.Heading", font=(self._title_family, 11, "bold"))

    # --- i18n helpers ---
    def _t(self, key, **kw):
        text = LANG[self.lang].get(key, key)
        if kw:
            text = text.format(**kw)
        return shape(text)

    def _t_raw(self, key):
        return LANG[self.lang].get(key, key)

    def _tip(self, key):
        # pre-wrapped + per-line shaped, so multi-line Arabic keeps its line order
        return shape_wrapped(LANG[self.lang].get(key, key))

    def _reg(self, fn):
        fn()
        self._i18n.append(fn)

    def _dispatch(self, method, *args):
        if self.controller is not None:
            getattr(self.controller, method)(*args)

    # --- button factory ---
    def _button(self, parent, icon, key=None, command=None, bootstyle="secondary-outline"):
        img = self.icons.get(icon)
        if img is not None:
            compound = "left" if key else "image"
            text = self._t(key) if key else ""
        else:
            compound = "none"
            text = self._t(key) if key else self.icons.glyph(icon)
        btn = tb.Button(parent, text=text, image=img, compound=compound,
                        bootstyle=bootstyle, command=command)
        btn.image = img
        if icon != self._play_icon or key is not None:
            self._icon_buttons.append((btn, icon))
        if key:
            self._reg(lambda b=btn, k=key: b.configure(text=self._t(k)))
        return btn

    # --- build ---
    def _build(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1, uniform="body")
        self.grid_columnconfigure(1, weight=2, uniform="body")
        self.grid_columnconfigure(2, weight=1, uniform="body")

        self._build_header()
        self._build_banner()
        self._build_files_pane()
        self._build_center_pane()
        self._build_cuts_pane()
        self._build_advanced()
        self._build_footer()
        self.bind("<space>", self._on_space)

    def _on_space(self, _event):
        w = self.focus_get()
        cls = w.winfo_class() if w else ""
        if cls in ("TEntry", "Entry", "TSpinbox", "Spinbox", "TButton", "TCheckbutton"):
            return
        self._dispatch("on_play_pause")
        return "break"

    def _build_header(self):
        header = tb.Frame(self, padding=(16, 12, 16, 6))
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = tb.Label(header, font=(self._title_family, 20, "bold"), bootstyle="primary")
        title.grid(row=0, column=0, sticky="w")
        self._reg(lambda: title.configure(text=self._t("app_title")))
        self._reg(lambda: self.title(self._t_raw("app_title")))

        self._button(header, "theme", command=lambda: self._dispatch("on_theme_toggle")
                     ).grid(row=0, column=1, padx=4)
        # ASCII AR/EN label — avoids raw (unshaped) Arabic on a Latin-context button.
        lang_btn = self._button(header, "language",
                                command=lambda: self._dispatch("on_language_toggle"))
        lang_btn.grid(row=0, column=2, padx=4)
        self._reg(lambda: lang_btn.configure(
            text="AR" if self.lang == "en" else "EN", compound="left"))

    def _build_banner(self):
        self.banner = tb.Label(self, bootstyle="inverse-warning", anchor="center",
                               padding=6, wraplength=1100)
        self.banner.grid(row=1, column=0, columnspan=3, sticky="ew", padx=16, pady=(0, 6))
        self.banner.grid_remove()

    def _build_files_pane(self):
        pane = tb.Labelframe(self, padding=10)
        pane.grid(row=2, column=0, sticky="nsew", padx=(16, 6), pady=6)
        pane.grid_rowconfigure(1, weight=1)
        pane.grid_columnconfigure(0, weight=1)
        self._reg(lambda: pane.configure(text=self._t("files")))

        bar = tb.Frame(pane)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self._button(bar, "import_file", key="import_files",
                     command=lambda: self._dispatch("on_import_files"),
                     bootstyle="primary").pack(side="left")
        self._button(bar, "import_folder", key="import_folder",
                     command=lambda: self._dispatch("on_import_folder"),
                     bootstyle="primary-outline").pack(side="left", padx=6)

        self.select_all_var = tk.BooleanVar(value=False)
        sa = tb.Checkbutton(bar, variable=self.select_all_var, bootstyle="round-toggle",
                            command=self._on_select_all)
        sa.pack(side="right")
        self._reg(lambda: sa.configure(text=self._t("select_all")))

        cols = ("check", "name", "status", "path")
        self.files_tree = tb.Treeview(pane, columns=cols, show="headings",
                                      bootstyle="primary", selectmode="browse")
        self.files_tree.heading("check", text=CHECK_OFF, anchor="center")
        self.files_tree.column("check", width=42, stretch=False, anchor="center")
        self.files_tree.column("name", width=240, stretch=True)
        self.files_tree.column("status", width=90, stretch=False, anchor="center")
        self.files_tree.column("path", width=0, minwidth=0, stretch=False)
        self._reg(lambda: self.files_tree.heading("name", text=self._t("filename_col")))
        self._reg(lambda: self.files_tree.heading("status", text=self._t("status_col")))
        self.files_tree.grid(row=1, column=0, sticky="nsew")

        vsb = tb.Scrollbar(pane, orient="vertical", command=self.files_tree.yview,
                           bootstyle="round")
        self.files_tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")

        self.files_tree.bind("<Button-1>", self._on_file_check)
        self.files_tree.bind("<<TreeviewSelect>>", lambda _e: self._dispatch("on_select_file"))

    def _build_center_pane(self):
        pane = tb.Frame(self, padding=(6, 6))
        pane.grid(row=2, column=1, sticky="nsew", pady=6)
        pane.grid_rowconfigure(0, weight=1)
        pane.grid_columnconfigure(0, weight=1)

        self.waveform = WaveformView(
            pane, self.palette,
            on_seek=lambda t: self._dispatch("on_seek", t),
            on_edit=lambda i, s, e: self._dispatch("on_segment_edit", i, s, e),
            on_split=lambda i, t: self._dispatch("on_segment_split", i, t),
            on_remove=lambda i: self._dispatch("on_segment_remove", i),
            on_create=lambda t: self._dispatch("on_segment_create", t))
        self.waveform.grid(row=0, column=0, sticky="nsew")
        self._reg(lambda: self.waveform.set_labels(
            self._t("split_here"), self._t("remove_segment"), self._t("create_segment")))

        transport = tb.Frame(pane)
        transport.grid(row=1, column=0, sticky="ew", pady=8)
        transport.grid_columnconfigure(3, weight=1)

        prev_btn = tb.Button(transport, text="⇤", width=3, bootstyle="secondary-outline",
                             command=lambda: self._dispatch("on_prev_silence"))
        prev_btn.grid(row=0, column=0)
        self.play_btn = self._button(transport, "play",
                                     command=lambda: self._dispatch("on_play_pause"),
                                     bootstyle="success")
        self.play_btn.grid(row=0, column=1, padx=4)
        next_btn = tb.Button(transport, text="⇥", width=3, bootstyle="secondary-outline",
                             command=lambda: self._dispatch("on_next_silence"))
        next_btn.grid(row=0, column=2)
        for btn, key in ((prev_btn, "prev_silence"), (next_btn, "next_silence")):
            tip = ToolTip(btn, text=self._t(key), bootstyle="secondary-inverse")
            self._reg(lambda t=tip, k=key: setattr(t, "text", self._t(k)))

        self.seek_var = tk.DoubleVar(value=0)
        self.seek = tb.Scale(transport, from_=0, to=1000, variable=self.seek_var,
                             command=self._on_seek_slider, bootstyle="success")
        self.seek.grid(row=0, column=3, sticky="ew", padx=10)
        self.time_label = tb.Label(transport, text="00:00 / 00:00")
        self.time_label.grid(row=0, column=4)
        self.skip_var = tk.BooleanVar(value=False)
        skip_chk = tb.Checkbutton(transport, variable=self.skip_var, bootstyle="round-toggle")
        skip_chk.grid(row=0, column=5, padx=(12, 0))
        self._reg(lambda: skip_chk.configure(text=self._t("skip_silence")))
        tb.Button(transport, text="−", width=2, bootstyle="secondary-outline",
                  command=lambda: self.waveform.zoom_by(1 / 1.5)).grid(row=0, column=6, padx=(12, 0))
        tb.Button(transport, text="+", width=2, bootstyle="secondary-outline",
                  command=lambda: self.waveform.zoom_by(1.5)).grid(row=0, column=7, padx=(4, 0))

    def _build_cuts_pane(self):
        pane = tb.Labelframe(self, padding=10)
        pane.grid(row=2, column=2, sticky="nsew", padx=(6, 16), pady=6)
        pane.grid_rowconfigure(1, weight=1)
        pane.grid_columnconfigure(0, weight=1)
        self._reg(lambda: pane.configure(text=self._t("cuts")))

        bar = tb.Frame(pane)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.analyze_btn = tb.Button(bar, bootstyle="info",
                                     command=lambda: self._dispatch("on_analyze"))
        self._reg(lambda: self.analyze_btn.configure(text=self._t("analyze")))
        self.analyze_btn.pack(side="left")
        self._button(bar, "restore", key="restore_recommended",
                     command=lambda: self._dispatch("on_restore_recommended")).pack(side="left", padx=6)
        self._button(bar, "remove_cut", key="remove_cut",
                     command=lambda: self._dispatch("on_remove_cut"),
                     bootstyle="danger-outline").pack(side="right")

        cols = ("export", "idx", "start", "end", "source")
        self.cuts_tree = tb.Treeview(pane, columns=cols, show="headings",
                                     bootstyle="info", selectmode="browse")
        self.cuts_tree.heading("export", text=CHECK_OFF, anchor="center")
        self.cuts_tree.heading("idx", text="#", anchor="center")
        self.cuts_tree.column("export", width=42, stretch=False, anchor="center")
        self.cuts_tree.column("idx", width=34, stretch=False, anchor="center")
        self.cuts_tree.column("start", width=70, stretch=True, anchor="center")
        self.cuts_tree.column("end", width=70, stretch=True, anchor="center")
        self.cuts_tree.column("source", width=64, stretch=False, anchor="center")
        self._reg(lambda: self.cuts_tree.heading("start", text=self._t("start")))
        self._reg(lambda: self.cuts_tree.heading("end", text=self._t("end")))
        self._reg(lambda: self.cuts_tree.heading("source", text=self._t("source")))
        self.cuts_tree.grid(row=1, column=0, sticky="nsew")
        vsb = tb.Scrollbar(pane, orient="vertical", command=self.cuts_tree.yview,
                           bootstyle="round")
        self.cuts_tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")
        self.cuts_tree.bind("<Button-1>", self._on_cut_check)

    def _build_advanced(self):
        wrap = tb.Frame(self, padding=(16, 0))
        wrap.grid(row=3, column=0, columnspan=3, sticky="ew")
        wrap.grid_columnconfigure(0, weight=1)

        self._adv_open = False
        self.adv_toggle = tb.Button(wrap, bootstyle="link", command=self._toggle_advanced)
        self.adv_toggle.grid(row=0, column=0, sticky="w")
        self._reg(lambda: self.adv_toggle.configure(
            text=f"{'▾' if self._adv_open else '▸'}  {self._t('advanced')}"))

        self.adv_body = tb.Labelframe(wrap, padding=10)
        self.adv_body.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.adv_body.grid_remove()
        self._reg(lambda: self.adv_body.configure(text=self._t("advanced")))

        self.adv_vars = {"silence_threshold": tk.StringVar(),
                         "min_silence": tk.StringVar(),
                         "min_segment": tk.StringVar()}
        rows = [("silence_threshold", "silence_threshold", "dB", "tip_silence_threshold"),
                ("min_silence", "min_silence", "s", "tip_min_silence"),
                ("min_segment", "min_segment_length", "s", "tip_min_segment_length")]
        for i, (var, key, unit, tipkey) in enumerate(rows):
            lbl = tb.Label(self.adv_body, width=22, anchor="w")
            lbl.grid(row=i, column=0, sticky="w", pady=3)
            self._reg(lambda l=lbl, k=key: l.configure(text=self._t(k)))
            tb.Entry(self.adv_body, textvariable=self.adv_vars[var], width=10).grid(
                row=i, column=1, sticky="w")
            tb.Label(self.adv_body, text=unit, bootstyle="secondary").grid(
                row=i, column=2, sticky="w", padx=(6, 0))
            info = tb.Label(self.adv_body, text="ⓘ", bootstyle="info", cursor="question_arrow")
            info.grid(row=i, column=3, sticky="w", padx=(8, 0))
            tip = ToolTip(info, text=self._tip(tipkey), bootstyle="secondary-inverse", wraplength=1000)
            self._reg(lambda t=tip, k=tipkey: setattr(t, "text", self._tip(k)))
        save_btn = self._button(self.adv_body, "export", key="save",
                                command=lambda: self._dispatch("on_save_settings"),
                                bootstyle="primary")
        save_btn.configure(image="", compound="none")   # text-only Save
        save_btn.grid(row=len(rows), column=0, columnspan=3, sticky="w", pady=(8, 0))

    def _toggle_advanced(self):
        self._adv_open = not self._adv_open
        arrow = "▾" if self._adv_open else "▸"
        self.adv_toggle.configure(text=f"{arrow}  {self._t('advanced')}")
        if self._adv_open:
            self.adv_body.grid()
        else:
            self.adv_body.grid_remove()

    def set_advanced_values(self, silence_threshold, min_silence, min_segment):
        self.adv_vars["silence_threshold"].set(f"{silence_threshold:g}")
        self.adv_vars["min_silence"].set(f"{min_silence:g}")
        self.adv_vars["min_segment"].set(f"{min_segment:g}")

    def get_advanced_values(self):
        return {k: v.get().strip() for k, v in self.adv_vars.items()}

    def _build_footer(self):
        footer = tb.Frame(self, padding=(16, 6, 16, 12))
        footer.grid(row=4, column=0, columnspan=3, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        self.status_label = tb.Label(footer, bootstyle="secondary")
        self.status_label.grid(row=0, column=0, sticky="w")
        self._reg(lambda: self.status_label.configure(text=self._t("ready")))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = tb.Progressbar(footer, maximum=100, variable=self.progress_var,
                                       bootstyle="success")
        self.progress.grid(row=0, column=1, sticky="ew", padx=16)
        self.progress.grid_remove()

        self.export_btn = self._button(footer, "export", key="export_selected",
                                       command=lambda: self._dispatch("on_export_selected"),
                                       bootstyle="success")
        self.export_btn.grid(row=0, column=2, sticky="e")

    # --- files interactions ---
    def _on_file_check(self, event):
        if self.files_tree.identify_region(event.x, event.y) != "cell":
            return
        if self.files_tree.identify_column(event.x) != "#1":
            return
        row = self.files_tree.identify_row(event.y)
        info = self.files.get(row)
        if not info:
            return
        info["checked"] = not info["checked"]
        self.files_tree.set(row, "check", CHECK_ON if info["checked"] else CHECK_OFF)
        self._sync_select_all()

    def _on_select_all(self):
        value = self.select_all_var.get()
        for iid, info in self.files.items():
            info["checked"] = value
            self.files_tree.set(iid, "check", CHECK_ON if value else CHECK_OFF)

    def _sync_select_all(self):
        all_on = bool(self.files) and all(i["checked"] for i in self.files.values())
        self.select_all_var.set(all_on)

    # --- cuts interactions ---
    def _on_cut_check(self, event):
        if self.cuts_tree.identify_region(event.x, event.y) != "cell":
            return
        if self.cuts_tree.identify_column(event.x) != "#1":
            return
        row = self.cuts_tree.identify_row(event.y)
        if not row:
            return
        index = self.cuts_tree.index(row)
        cut = self.cuts[index]
        cut["export"] = not cut["export"]
        self.cuts_tree.set(row, "export", CHECK_ON if cut["export"] else CHECK_OFF)
        self._sync_wave_cuts()

    # --- transport ---
    def _on_seek_slider(self, value):
        if self._syncing or self._duration <= 0:
            return
        self._dispatch("on_seek", float(value) / 1000.0 * self._duration)

    # --- theme / language (invoked by controller) ---
    def apply_theme(self, mode: str):
        self.theme_mode = mode
        self.style.theme_use(theme_name(mode))
        self.palette = apply_custom_styles(self, mode)
        self._style_treeview()
        self.icons = IconLoader(ICON_DIR, mode)
        for btn, name in self._icon_buttons:
            img = self.icons.get(name)
            btn.configure(image=img)
            btn.image = img
        self.set_play_state(self._play_icon == "pause")
        self.waveform.set_palette(self.palette)

    def apply_language(self, lang: str):
        self.lang = lang
        for fn in self._i18n:
            fn()
        if self.caps is not None:
            self.set_capabilities(self.caps)

    # --- controller-facing API ---
    def set_capabilities(self, caps):
        self.caps = caps
        messages = []
        if not caps.ffmpeg:
            messages.append(LANG[self.lang]["ffmpeg_missing"])
        if not caps.playback:
            messages.append(LANG[self.lang]["no_audio_backend"])
        if messages:
            self.banner.configure(text=shape_wrapped("   •   ".join(messages), width=120))
            self.banner.grid()
        else:
            self.banner.grid_remove()
        ff_state = "normal" if caps.ffmpeg else "disabled"
        self.analyze_btn.configure(state=ff_state)
        self.export_btn.configure(state=ff_state)
        self.play_btn.configure(state="normal" if caps.playback else "disabled")

    def update_files_list(self, files):
        self.files_tree.delete(*self.files_tree.get_children())
        self.files.clear()
        for i, path in enumerate(files):
            iid = f"f{i}"
            self.files_tree.insert("", "end", iid=iid,
                                   values=(CHECK_ON, shape(os.path.basename(path)), "—", path))
            self.files[iid] = {"path": path, "checked": True}
        self._sync_select_all()

    def get_checked_files(self):
        return [i["path"] for i in self.files.values() if i["checked"]]

    def get_current_file(self):
        sel = self.files_tree.selection()
        if sel and sel[0] in self.files:
            return self.files[sel[0]]["path"]
        return None

    def select_file_by_path(self, path):
        for iid, info in self.files.items():
            if info["path"] == path:
                self.files_tree.selection_set(iid)   # fires <<TreeviewSelect>>
                self.files_tree.see(iid)
                return

    def set_file_status(self, path, status):
        for iid, info in self.files.items():
            if info["path"] == path:
                self.files_tree.set(iid, "status", status)
                return

    def set_status(self, message):
        self.status_label.configure(text=shape(message))

    def set_progress(self, fraction):
        if fraction is None:
            self.progress.grid_remove()
        else:
            self.progress.grid()
            self.progress_var.set(max(0.0, min(1.0, fraction)) * 100)

    def set_waveform(self, peaks, duration):
        self._duration = max(0.0, duration)
        self.waveform.set_peaks(peaks, duration)
        self.time_label.configure(text=f"00:00 / {_fmt_time(duration)}")

    def set_playhead(self, seconds):
        self.waveform.set_playhead(seconds)
        if self._duration > 0:
            self._syncing = True
            self.seek_var.set(seconds / self._duration * 1000.0)
            self._syncing = False
        self.time_label.configure(text=f"{_fmt_time(seconds)} / {_fmt_time(self._duration)}")

    def set_play_state(self, playing):
        self._play_icon = "pause" if playing else "play"
        img = self.icons.get(self._play_icon)
        if img is not None:
            self.play_btn.configure(image=img, compound="image", text="")
        else:
            self.play_btn.configure(image="", compound="none",
                                    text=self.icons.glyph(self._play_icon))
        self.play_btn.image = img

    def render_cuts(self, cuts):
        self.cuts = cuts
        self.cuts_tree.delete(*self.cuts_tree.get_children())
        for i, cut in enumerate(cuts, start=1):
            mark = CHECK_ON if cut.get("export", True) else CHECK_OFF
            self.cuts_tree.insert("", "end",
                                  values=(mark, i, _fmt_time(cut["start"]),
                                          _fmt_time(cut["end"]), self._t(cut["source"])))
        self._sync_wave_cuts()

    def _sync_wave_cuts(self):
        self.waveform.set_cuts([(c["id"], c["start"], c["end"]) for c in self.cuts
                                if c.get("export", True)])

    def confirm_merge(self):
        from tkinter import messagebox
        return messagebox.askyesno(self._t("merge_title"), self._t("merge_prompt"))

    def is_skip_enabled(self):
        return self.skip_var.get()

    def get_export_cuts(self):
        return [c for c in self.cuts if c.get("export", True)]

    def get_selected_cut_index(self):
        sel = self.cuts_tree.selection()
        return self.cuts_tree.index(sel[0]) if sel else None


if __name__ == "__main__":
    TaraweehCutterApp().mainloop()
