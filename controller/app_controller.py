"""Orchestrates UI events, services and pure logic. Owns domain state."""
import dataclasses
import hashlib
import json
import os
import tempfile
from tkinter import filedialog

from logic import file_utils
from logic.audio_analyzer import get_speech_segments
from logic.audio_processor import generate_cut_ranges
from resources.lang import LANG
from services.ffmpeg_service import (ExportCancelled, detect_silences,
                                     export_segment, probe_duration, transcode_audio)
from services.player_service import make_player
from services.session import load_session, save_session
from services.settings import load_settings, save_settings
from services.waveform_service import decode_peaks
from services.worker import TaskRunner

_AUDIO_FILETYPES = [("Audio Files", "*.mp3 *.wav *.m4a"), ("All Files", "*.*")]
MIN_SEGMENT = 0.2       # shortest allowed segment (seconds)
MERGE_EPS = 0.05        # edges within this are "touching" → offer to merge
NEW_SEGMENT = 5.0       # width of a segment created on silence (seconds)


class AppController:
    def __init__(self, window, caps, lang="en"):
        self.window = window
        self.caps = caps
        self.lang = lang
        self.mode = "light"

        s = load_settings()
        self.silence_threshold = s["silence_threshold"]
        self.min_silence = s["min_silence"]
        self.min_length = s["min_segment"]
        self.noise = f"{self.silence_threshold:g}dB"

        self.runner = TaskRunner(window)
        self.player = make_player()

        self.imported = []          # all imported paths
        self.current = None         # focused file path
        self.duration = 0.0
        self.peaks = []
        self.cuts = []              # list of cut dicts for the current file
        self._cut_seq = 0           # stable-id counter for segments
        self.position = 0.0
        self.output_dir = None
        self._poll_job = None
        self._pb_tmpdir = None      # temp dir for transcoded playback files
        self._pb_pending = False    # a playback transcode is in flight
        self._restoring = False     # suppress session save while restoring
        self._restore_cuts = None   # cuts to re-apply once the file loads
        self._last_saved = None     # last-saved session snapshot (dirty check)

        # Reflect the real backend, not just whether pygame imported.
        caps = dataclasses.replace(caps, playback=self.player.available)
        self.caps = caps
        window.set_capabilities(caps)
        window.set_advanced_values(self.silence_threshold, self.min_silence, self.min_length)

    def _t(self, key, **kw):
        text = LANG[self.lang].get(key, key)
        return text.format(**kw) if kw else text

    def _new_cut(self, start, end, source, export=True):
        self._cut_seq += 1
        return {"id": self._cut_seq, "start": start, "end": end,
                "source": source, "export": export}

    def _find_cut(self, cid):
        return next((c for c in self.cuts if c.get("id") == cid), None)

    # --- import ---
    def on_import_files(self):
        paths = filedialog.askopenfilenames(title=self._t("import_files"),
                                            filetypes=_AUDIO_FILETYPES)
        self._import(list(paths))

    def on_import_folder(self):
        directory = filedialog.askdirectory(title=self._t("import_folder"))
        if directory:
            self._import(file_utils.list_audio_files_in_dir(directory))

    def _import(self, paths):
        audio = file_utils.filter_audio_files(paths)
        added = [p for p in audio if p not in self.imported]
        if not added:
            if not self.imported:
                self.window.set_status(self._t("no_audio_found"))
            return
        self.imported.extend(added)
        self.window.update_files_list(self.imported)
        self.window.set_status(self._t("imported_n", n=len(added)))

    # --- file selection / waveform load ---
    def on_select_file(self):
        path = self.window.get_current_file()
        if not path or path == self.current:
            return
        self._stop_playback()
        self.current = path
        self.cuts, self.position = [], 0.0
        self.window.render_cuts([])
        self.window.set_playhead(0.0)
        self._pb_pending = False
        if self.player.available and self.player.supports(path):
            self._safe_load(path)       # native format: ready instantly

        if not self.caps.ffmpeg:
            self.window.set_waveform([], 0.0)
            return
        self.window.set_status(self._t("analyzing", name=os.path.basename(path)))
        self.runner.submit(lambda p, c: (probe_duration(path), decode_peaks(path)),
                           on_done=self._on_loaded, on_error=self._on_error)

    def _pb_temp(self, path):
        if self._pb_tmpdir is None:
            self._pb_tmpdir = tempfile.mkdtemp(prefix="taraweeh-pb-")
        digest = hashlib.md5(path.encode()).hexdigest()[:10]
        return os.path.join(self._pb_tmpdir, f"{digest}.wav")

    def _safe_load(self, play_path, source=None):
        # Ignore a transcode that finished after the user moved to another file.
        if source is not None and source != self.current:
            return
        try:
            self.player.load(play_path, self.duration)
        except Exception:
            pass

    def _on_loaded(self, result):
        self.duration, self.peaks = result
        self.window.set_waveform(self.peaks, self.duration)
        self.window.set_status(self._t("ready"))
        if self._restore_cuts is not None:
            self.cuts = [self._new_cut(c["start"], c["end"], c.get("source", "auto"),
                                       c.get("export", True)) for c in self._restore_cuts]
            self._restore_cuts = None
            self.window.render_cuts(self.cuts)

    # --- auto analysis ---
    def on_analyze(self):
        if not self.caps.ffmpeg or not self.current:
            return
        self.window.set_status(self._t("analyzing", name=os.path.basename(self.current)))
        path = self.current
        self.runner.submit(lambda p, c: self._detect(path),
                           on_done=self._on_analyzed, on_error=self._on_error)

    def _detect(self, path):
        duration = self.duration or probe_duration(path)
        silences = detect_silences(path, noise=self.noise, min_silence=self.min_silence)
        return generate_cut_ranges(get_speech_segments(silences, duration), self.min_length)

    def _on_analyzed(self, ranges):
        auto = [self._new_cut(s, e, "auto") for s, e in ranges]
        manual = [c for c in self.cuts if c["source"] == "manual"]
        self.cuts = sorted(auto + manual, key=lambda c: c["start"])
        self.window.render_cuts(self.cuts)
        self.window.set_status(self._t("analyzed_n", n=len(ranges)))

    def on_restore_recommended(self):
        self.cuts = [c for c in self.cuts if c["source"] == "auto"]
        self.on_analyze()

    def on_remove_cut(self):
        index = self.window.get_selected_cut_index()
        if index is not None:
            del self.cuts[index]
            self.window.render_cuts(self.cuts)

    # --- direct editing from the waveform ---
    def on_segment_edit(self, cid, start, end):
        cut = self._find_cut(cid)
        if not cut:
            return
        cut["start"], cut["end"] = start, end
        cut["source"] = "manual"
        self.cuts.sort(key=lambda c: c["start"])
        self._clamp_to_neighbors(cut)
        self._maybe_merge(cut)
        self.window.render_cuts(self.cuts)

    def _clamp_to_neighbors(self, cut):
        i = self.cuts.index(cut)
        lo = self.cuts[i - 1]["end"] if i > 0 else 0.0
        hi = self.cuts[i + 1]["start"] if i < len(self.cuts) - 1 else self.duration
        cut["start"] = max(lo, min(cut["start"], cut["end"] - MIN_SEGMENT))
        cut["end"] = min(hi, max(cut["end"], cut["start"] + MIN_SEGMENT))

    def _maybe_merge(self, cut):
        i = self.cuts.index(cut)
        prev = self.cuts[i - 1] if i > 0 else None
        nxt = self.cuts[i + 1] if i < len(self.cuts) - 1 else None
        if prev and abs(cut["start"] - prev["end"]) <= MERGE_EPS:
            earlier, later, side = prev, cut, "prev"
        elif nxt and abs(cut["end"] - nxt["start"]) <= MERGE_EPS:
            earlier, later, side = cut, nxt, "next"
        else:
            return
        if self.window.confirm_merge():
            earlier["end"] = later["end"]
            earlier["source"] = "manual"
            self.cuts.remove(later)
        elif side == "prev":                     # keep adjacent but separate
            cut["start"] = min(prev["end"] + 2 * MERGE_EPS, cut["end"] - MIN_SEGMENT)
        else:
            cut["end"] = max(nxt["start"] - 2 * MERGE_EPS, cut["start"] + MIN_SEGMENT)

    def on_segment_split(self, cid, t):
        cut = self._find_cut(cid)
        if not cut or not (cut["start"] + MIN_SEGMENT < t < cut["end"] - MIN_SEGMENT):
            return
        i = self.cuts.index(cut)
        self.cuts[i:i + 1] = [self._new_cut(cut["start"], t, cut["source"], cut["export"]),
                              self._new_cut(t, cut["end"], cut["source"], cut["export"])]
        self.window.render_cuts(self.cuts)

    def on_segment_remove(self, cid):
        cut = self._find_cut(cid)
        if cut:
            self.cuts.remove(cut)
            self.window.render_cuts(self.cuts)

    def on_segment_create(self, t):
        """Create a ~NEW_SEGMENT-wide segment at t, clamped to the silence gap."""
        lo = max((c["end"] for c in self.cuts if c["end"] <= t), default=0.0)
        hi = min((c["start"] for c in self.cuts if c["start"] >= t), default=self.duration)
        if hi - lo < MIN_SEGMENT:
            return
        width = min(NEW_SEGMENT, hi - lo)
        start = max(lo, t - width / 2)
        end = min(hi, start + width)
        start = max(lo, end - width)
        self.cuts.append(self._new_cut(start, end, "manual"))
        self.cuts.sort(key=lambda c: c["start"])
        self.window.render_cuts(self.cuts)

    # --- transport ---
    def on_seek(self, seconds):
        self.position = seconds
        if self.player.available and self.player.is_loaded():
            self.player.seek(seconds)
        self.window.set_playhead(seconds)

    def on_next_silence(self):
        self._seek_silence(forward=True)

    def on_prev_silence(self):
        self._seek_silence(forward=False)

    def _seek_silence(self, forward):
        """Jump the playhead to the start of the next/previous silent gap."""
        points = self._silence_points()
        if forward:
            target = next((p for p in points if p > self.position + 0.05), None)
        else:
            target = next((p for p in reversed(points) if p < self.position - 0.05), None)
        if target is not None:
            self.on_seek(target)

    def _silence_points(self):
        """Sorted start-times of the silent gaps between export segments."""
        cuts = sorted((c for c in self.cuts if c.get("export", True)), key=lambda c: c["start"])
        points, prev_end = [], 0.0
        for c in cuts:
            if c["start"] > prev_end + 0.05:
                points.append(prev_end)
            prev_end = c["end"]
        if self.duration > prev_end + 0.05:
            points.append(prev_end)
        return points

    def on_play_pause(self):
        if not self.player.available:
            return
        if self.player.is_loaded():
            self._toggle_playback()
        elif self.current and self.caps.ffmpeg and not self._pb_pending:
            self._prepare_and_play(self.current)

    def _toggle_playback(self):
        if self.player.is_playing():
            self.player.pause()
            self.window.set_play_state(False)
            self._stop_poll()
        else:
            self.player.play()
            self.window.set_play_state(True)
            self._poll_position()

    def _prepare_and_play(self, path):
        """Transcode a non-native format to a temp WAV, then start playback."""
        temp = self._pb_temp(path)
        if os.path.exists(temp):                 # cached from a previous play
            self._safe_load(temp, source=path)
            if self.player.is_loaded():
                self._toggle_playback()
            return
        self._pb_pending = True
        self.window.set_status(self._t("preparing_playback"))
        self._cleanup_temps(keep=temp)
        self.runner.submit(
            lambda p, c: transcode_audio(path, temp, ac=1, ar=22050),
            on_done=lambda dst: self._on_transcoded(dst, path),
            on_error=self._on_pb_error)

    def _on_transcoded(self, dst, source):
        self._pb_pending = False
        if source != self.current:
            return
        self._safe_load(dst, source=source)
        self.window.set_status(self._t("ready"))
        if self.player.is_loaded():
            self._toggle_playback()               # auto-play now that it's ready

    def _on_pb_error(self, exc):
        self._pb_pending = False
        self.window.set_status(self._t("playback_failed"))

    def _cleanup_temps(self, keep):
        if not self._pb_tmpdir:
            return
        for name in os.listdir(self._pb_tmpdir):
            path = os.path.join(self._pb_tmpdir, name)
            if path != keep:
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _poll_position(self):
        if not self.player.is_playing():
            self.window.set_play_state(False)
            self._poll_job = None
            return
        self.position = self.player.position()
        if self.window.is_skip_enabled() and not self._apply_skip():
            return                        # skip ended playback
        self.window.set_playhead(self.position)
        self._poll_job = self.window.after(50, self._poll_position)

    def _apply_skip(self):
        """Play only the selected cuts: in a gap, jump to the next cut; stop after
        the last one. Returns False if playback was stopped."""
        ranges = sorted((c["start"], c["end"]) for c in self.cuts if c.get("export", True))
        if not ranges:
            return True
        for start, end in ranges:
            if start <= self.position < end:
                return True               # inside a voice cut, keep playing
        for start, end in ranges:
            if start > self.position:
                self.position = start
                self.player.seek(start)   # jump over the silent gap
                return True
        self._stop_playback()             # past the last cut
        self.window.set_playhead(ranges[-1][1])
        return False

    def _stop_poll(self):
        if self._poll_job is not None:
            self.window.after_cancel(self._poll_job)
            self._poll_job = None

    def _stop_playback(self):
        self._stop_poll()
        if self.player.available:
            self.player.stop()
        self.window.set_play_state(False)

    # --- export ---
    def on_export_selected(self):
        if not self.caps.ffmpeg:
            return
        checked = self.window.get_checked_files()
        if not checked:
            self.window.set_status(self._t("no_selection"))
            return
        current_ranges = ([(c["start"], c["end"]) for c in self.window.get_export_cuts()]
                          if self.current in checked else [])
        if self.current in checked and not current_ranges and len(checked) == 1:
            self.window.set_status(self._t("no_cuts"))
            return
        out = filedialog.askdirectory(title=self._t("select_output_dir"))
        if not out:
            return
        self.output_dir = out
        self.window.set_progress(0.0)
        self.runner.submit(self._export_job(checked, self.current, current_ranges, out),
                           on_done=lambda n: self._on_exported(n, out),
                           on_progress=self.window.set_progress,
                           on_error=self._on_error)

    def _export_job(self, checked, current, current_ranges, out):
        def run(progress, cancel):
            plan = []
            for src in checked:
                if src == current and current_ranges:
                    ranges = current_ranges
                else:
                    dur = probe_duration(src)
                    silences = detect_silences(src, noise=self.noise, min_silence=self.min_silence)
                    ranges = generate_cut_ranges(get_speech_segments(silences, dur), self.min_length)
                plan.append((src, ranges))

            total = sum(len(r) for _, r in plan) or 1
            done = 0
            for src, ranges in plan:
                base, ext = os.path.splitext(os.path.basename(src))
                for i, (start, end) in enumerate(ranges, start=1):
                    if cancel.is_set():
                        raise ExportCancelled()
                    export_segment(src, os.path.join(out, f"{base}_part{i:02d}{ext}"),
                                   start, end, cancel=cancel)
                    done += 1
                    progress(done / total)
            return done
        return run

    def _on_exported(self, count, out):
        self.window.set_progress(None)
        self.window.set_status(self._t("export_done", n=count, dir=out))

    def _on_error(self, exc):
        self.window.set_progress(None)
        self.window.set_status(self._t("export_failed", error=str(exc)[:100]))

    # --- theme / language ---
    def on_theme_toggle(self):
        self.mode = "dark" if self.mode == "light" else "light"
        self.window.apply_theme(self.mode)

    def on_language_toggle(self):
        self.lang = "ar" if self.lang == "en" else "en"
        self.window.apply_language(self.lang)

    # --- session (auto-save / restore) ---
    def _snapshot(self):
        return {"theme": self.mode, "lang": self.lang, "imported": self.imported,
                "current": self.current,
                "cuts": [{"start": c["start"], "end": c["end"], "source": c["source"],
                          "export": c.get("export", True)} for c in self.cuts]}

    def _save_session(self):
        if self._restoring:
            return
        snap = json.dumps(self._snapshot(), sort_keys=True)
        if snap != self._last_saved:
            save_session(self._snapshot())
            self._last_saved = snap

    def start_autosave(self):
        self._save_session()
        self.window.after(10000, self.start_autosave)

    def on_close(self):
        self._save_session()
        self.window.destroy()

    def restore_session(self):
        data = load_session()
        if not data:
            return
        self._restoring = True
        try:
            if data.get("theme") in ("light", "dark") and data["theme"] != self.mode:
                self.mode = data["theme"]
                self.window.apply_theme(self.mode)
            if data.get("lang") in ("en", "ar") and data["lang"] != self.lang:
                self.lang = data["lang"]
                self.window.apply_language(self.lang)
            imported = [p for p in data.get("imported", []) if os.path.exists(p)]
            if imported:
                self.imported = imported
                self.window.update_files_list(imported)
            current = data.get("current")
            if current and current in imported:
                self._restore_cuts = data.get("cuts", [])
                self.window.select_file_by_path(current)   # fires on_select_file → async load
        finally:
            self._restoring = False

    # --- advanced settings ---
    def on_save_settings(self):
        values = self.window.get_advanced_values()
        try:
            threshold = float(values["silence_threshold"])
            min_silence = float(values["min_silence"])
            min_segment = float(values["min_segment"])
        except (KeyError, ValueError, TypeError):
            self.window.set_status(self._t("settings_invalid"))
            return
        if min_silence <= 0 or min_segment <= 0:
            self.window.set_status(self._t("settings_invalid"))
            return
        self.silence_threshold, self.min_silence, self.min_length = threshold, min_silence, min_segment
        self.noise = f"{threshold:g}dB"
        save_settings({"silence_threshold": threshold, "min_silence": min_silence,
                       "min_segment": min_segment})
        self.window.set_status(self._t("settings_saved"))
