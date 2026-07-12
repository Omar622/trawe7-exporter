"""Round-trips real ffmpeg when the binary is present; skips otherwise."""
import os
import subprocess

import pytest

from services import ffmpeg_service as fs
from services.waveform_service import decode_peaks

HAS_FFMPEG = fs.ffmpeg_available()
requires_ffmpeg = pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg not installed")


def _make_tone(path, seconds):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"sine=frequency=440:duration={seconds}", path],
        check=True, capture_output=True)


@requires_ffmpeg
def test_probe_and_export(tmp_path):
    src = str(tmp_path / "tone.wav")
    _make_tone(src, 3)
    assert abs(fs.probe_duration(src) - 3.0) < 0.5

    dst = str(tmp_path / "cut.wav")
    fs.export_segment(src, dst, 0.5, 1.5, reencode=True)
    assert os.path.exists(dst)
    assert abs(fs.probe_duration(dst) - 1.0) < 0.4


@requires_ffmpeg
def test_decode_peaks(tmp_path):
    src = str(tmp_path / "tone.wav")
    _make_tone(src, 2)
    peaks = decode_peaks(src, buckets=100)
    assert len(peaks) == 100
    assert 0.0 < max(peaks) <= 1.0


def test_probe_raises_without_ffmpeg():
    if HAS_FFMPEG:
        pytest.skip("ffmpeg present")
    with pytest.raises(fs.FfmpegNotAvailable):
        fs.probe_duration("missing.mp3")
