import pytest
from logic.audio_processor import generate_cut_ranges

def test_generate_cut_ranges_basic():
    segments = [(0, 5), (5, 20), (20, 35)]
    result = generate_cut_ranges(segments, min_length=10)
    assert result == [(5, 20), (20, 35)]

def test_generate_cut_ranges_all_short():
    segments = [(0, 2), (2, 4)]
    result = generate_cut_ranges(segments, min_length=5)
    assert result == []
