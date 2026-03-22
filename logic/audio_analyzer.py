# Pure logic for audio analysis (no I/O, no UI)
def get_speech_segments(silence_periods, total_duration):
    # Example pure function
    segments = []
    prev_end = 0
    for start, end in silence_periods:
        if prev_end < start:
            segments.append((prev_end, start))
        prev_end = end
    if prev_end < total_duration:
        segments.append((prev_end, total_duration))
    return segments

# ...other pure logic functions...
