"""Waveform peak extraction via a low-samplerate ffmpeg decode (no numpy)."""
import array
import sys
from typing import List

import ffmpeg

from services.ffmpeg_service import FfmpegNotAvailable, ffmpeg_available


def decode_peaks(path: str, buckets: int = 4000, sr: int = 8000) -> List[float]:
    """Decode to downsampled mono PCM and reduce to `buckets` peaks in [0, 1],
    normalized to the loudest peak so the waveform fills the view height."""
    if not ffmpeg_available():
        raise FfmpegNotAvailable("ffmpeg is required to decode a waveform")
    raw, _ = (
        ffmpeg.input(path)
        .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=sr)
        .run(capture_stdout=True, capture_stderr=True)
    )
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder == "big":
        samples.byteswap()
    if not samples:
        return []

    total = len(samples)
    buckets = max(1, min(buckets, total))
    step = total / buckets
    peaks: List[float] = []
    for i in range(buckets):
        lo = int(i * step)
        hi = total if i == buckets - 1 else max(lo + 1, int((i + 1) * step))
        window = samples[lo:hi]
        peaks.append(float(max(abs(min(window)), abs(max(window)))))

    loudest = max(peaks)
    if loudest <= 0:
        return [0.0] * buckets
    return [p / loudest for p in peaks]
