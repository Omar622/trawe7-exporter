# Taraweeh Cutter Desktop App

This is a simple, user-friendly desktop app for cutting and exporting Taraweeh prayer recordings. Built with Tkinter, it supports both Arabic and English.


- Import and select audio files (`.mp3`, `.wav`)
- Import multiple audio files at once (select files or a directory)
- Switch between Arabic and English
- Simple, accessible interface for all users

## UI-Only / Not Yet Implemented
- Audio playback and seeking
- Waveform display
- Recommended cut points
- Editing cut start/end times
- Exporting selected files
- Restoring app recommendations

All unimplemented features are present in the UI and will show a "Not implemented yet" message.

## Usage
1. Run the app: `python app.py`
2. Import your audio files: you can select multiple files or an entire directory (all `.mp3` and `.wav` files will be imported)
3. Select files and (when implemented) adjust cut points
4. Export selected files (feature not yet implemented)

## Notes
- **Audio playback, waveform display, cut recommendations, and export features are not yet implemented.** The UI is ready and will show a message for unimplemented features.
- The app is focused on Islamic use (Taraweeh prayer recordings), but can be used for any audio.
- All UI elements are available in both Arabic and English.


## Directory Structure
```
taraweeh_cutter/
├── app.py                # Tkinter desktop app entry point
├── ui/                   # UI classes (Tkinter windows)
├── controller/           # App controller (UI logic)
├── logic/                # Pure logic (testable)
├── services/             # File I/O and OS operations
├── resources/            # Language dictionaries, icons, etc.
├── tests/                # Unit tests for pure logic
├── pyproject.toml        # Dependencies
├── README.md             # This file
├── .gitignore
├── input/                # (Optional) Input files
├── output/               # (Optional) Output files
└── trawe7_exporter/      # (Legacy, can be deleted)
```

## Development
- To implement missing features, connect the UI to the logic in `audio_analyzer.py`, `audio_processor.py`.
- For waveform display and audio playback, consider using libraries like `pydub`, `pygame`, or `sounddevice`.

---
**This app is a work in progress.**
