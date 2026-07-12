"""ffmpeg-backed probing, silence detection, and segment export."""
import re
import shutil
import threading
import time
from typing import List, Optional, Tuple

import ffmpeg

_SILENCE_START_RE = re.compile(r"silence_start:\s*(-?[0-9.]+)")
_SILENCE_END_RE = re.compile(r"silence_end:\s*(-?[0-9.]+)")


class FfmpegNotAvailable(RuntimeError):
    """ffmpeg/ffprobe binaries are not installed or not on PATH."""


class ExportError(RuntimeError):
    """ffmpeg exited non-zero while exporting a segment."""


class ExportCancelled(RuntimeError):
    """Export was cancelled before completion."""


def ffmpeg_available() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def _require_ffmpeg() -> None:
    if not ffmpeg_available():
        raise FfmpegNotAvailable("ffmpeg and ffprobe must be installed and on PATH")


def probe_duration(path: str) -> float:
    _require_ffmpeg()
    info = ffmpeg.probe(path)
    try:
        return float(info["format"]["duration"])
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"could not read duration from {path}") from exc


def detect_silences(path: str, noise: str = "-30dB",
                    min_silence: float = 0.5) -> List[Tuple[float, float]]:
    """Return silent intervals as (start, end) seconds via the silencedetect filter."""
    _require_ffmpeg()
    _, err = (
        ffmpeg.input(path)
        .filter("silencedetect", n=noise, d=min_silence)
        .output("-", format="null")
        .run(capture_stdout=True, capture_stderr=True)
    )
    log = err.decode("utf-8", errors="ignore")
    starts = [float(v) for v in _SILENCE_START_RE.findall(log)]
    ends = [float(v) for v in _SILENCE_END_RE.findall(log)]

    duration = None
    periods: List[Tuple[float, float]] = []
    for i, start in enumerate(starts):
        if i < len(ends):
            end = ends[i]
        else:
            duration = duration if duration is not None else probe_duration(path)
            end = duration
        periods.append((max(0.0, start), end))
    return periods


def transcode_audio(src: str, dst: str, ac: Optional[int] = None,
                    ar: Optional[int] = None) -> str:
    """Transcode src to dst (format from dst extension). Used to make formats
    pygame can't decode (e.g. .m4a) playable; ac/ar downmix for a fast preview."""
    _require_ffmpeg()
    out_kwargs = {}
    if ac:
        out_kwargs["ac"] = ac
    if ar:
        out_kwargs["ar"] = ar
    ffmpeg.input(src).output(dst, **out_kwargs).overwrite_output().run(
        capture_stdout=True, capture_stderr=True)
    return dst


def export_segment(src: str, dst: str, start: float, end: float,
                   reencode: bool = False,
                   cancel: Optional[threading.Event] = None) -> str:
    """Cut [start, end) from src into dst. Stream-copies unless reencode is set."""
    _require_ffmpeg()
    duration = max(0.0, end - start)
    out_kwargs = {"t": duration} if duration > 0 else {}
    if not reencode:
        out_kwargs["c"] = "copy"

    process = (
        ffmpeg.input(src, ss=start)
        .output(dst, **out_kwargs)
        .overwrite_output()
        .run_async(pipe_stdout=True, pipe_stderr=True)
    )
    # Drain stderr concurrently so a full pipe buffer can't deadlock long encodes.
    stderr: List[bytes] = []
    drain = threading.Thread(target=lambda: stderr.append(process.stderr.read()), daemon=True)
    drain.start()

    while process.poll() is None:
        if cancel is not None and cancel.is_set():
            process.terminate()
            drain.join(timeout=1.0)
            raise ExportCancelled(dst)
        time.sleep(0.05)
    drain.join(timeout=1.0)

    if process.returncode != 0:
        message = b"".join(chunk for chunk in stderr if chunk).decode(errors="ignore")
        raise ExportError(f"ffmpeg failed for {dst}: {message[-400:]}")
    return dst
