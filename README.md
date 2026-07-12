# Taraweeh Cutter

A bilingual (Arabic/English) desktop app for splitting long Taraweeh prayer
recordings into per-segment audio files and exporting them. Built with Tkinter +
[ttkbootstrap](https://ttkbootstrap.readthedocs.io/), with a light/dark theme
toggle and a real ffmpeg-backed audio pipeline.

## Features
- Import audio files or a whole folder (`.mp3`, `.wav`, `.m4a`) with per-file selection.
- **Waveform view** with a playhead and manual begin/end cut markers.
- **Auto-detect** cut points from silences (ffmpeg `silencedetect`) and filter by length.
- Review cuts in a table (auto + manual), then **export** each cut to its own file.
- Optional **playback** (play/pause/seek) when `pygame` is installed.
- Light ⇄ dark theme toggle and English ⇄ Arabic language toggle.

## Requirements
- Python ≥ 3.10.
- **ffmpeg** (with `ffprobe`) on your `PATH` — required for waveform, silence
  detection and export. Without it the app still runs, shows a banner and disables
  those features. Install with `sudo apt install ffmpeg` (Debian/Ubuntu) or
  `brew install ffmpeg` (macOS).
- `pygame` is optional (playback only); everything else works without it.

## Usage
```bash
uv sync                     # install dependencies
uv run python app.py        # launch the app
```
Import recordings → select a file to see its waveform → **Analyze** to auto-detect
cuts (or place manual begin/end markers) → **Export Selected**.

### Best font rendering (recommended)
The uv-managed interpreter bundles a Tk without Xft, so text is not antialiased and
Arabic falls back to core X fonts. For crisp DejaVu/Noto fonts, run against a system
Python whose Tk has Xft:
```bash
sudo apt install -y python3-tk                       # Xft-enabled Tk
uv venv .venv-system --python /usr/bin/python3        # venv on the system interpreter
uv pip install --python .venv-system/bin/python \
    ttkbootstrap Pillow ffmpeg-python arabic-reshaper python-bidi pygame
.venv-system/bin/python app.py
```
The UI auto-selects the best available font family, so no code changes are needed.
Note: Tk has no Arabic shaping engine, so the app pre-shapes Arabic with
`arabic-reshaper` + `python-bidi` regardless of interpreter.

## Architecture
```
app.py            Entry point: detect capabilities, build window, wire controller
ui/               View only — dashboard, waveform canvas, icons, styles
controller/       Orchestration: UI events → services + logic → view updates
logic/            Pure, side-effect-free, unit-tested (segments, cut ranges, flags)
services/         All ffmpeg / audio / OS I/O; runs off the Tk thread via a worker
resources/        Language dictionaries and bundled icons
tests/            Unit tests (logic always; ffmpeg test skips when absent)
scripts/          gen_icons.py — regenerates the placeholder icon PNGs
```
`logic/` never imports ffmpeg; services feed it plain numbers so it stays testable.

## Development
```bash
uv run python -m pytest -q          # run the test suite
uv run python scripts/gen_icons.py  # regenerate icons
```

## Notes
- Focused on Taraweeh recordings but works for any audio.
- `pygame` has no `.m4a` playback and approximate seek on compressed audio; analysis
  and export are unaffected.
