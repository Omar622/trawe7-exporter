import pytest
from logic.audio_analyzer import get_speech_segments

def test_get_speech_segments_basic():
    silence_periods = [(2, 4), (6, 8)]
    total_duration = 10
    result = get_speech_segments(silence_periods, total_duration)
    assert result == [(0, 2), (4, 6), (8, 10)]

def test_get_speech_segments_no_silence():
    silence_periods = []
    total_duration = 5
    result = get_speech_segments(silence_periods, total_duration)
    assert result == [(0, 5)]
