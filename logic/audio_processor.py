# Pure logic for audio processing (no I/O, no UI)
def generate_cut_ranges(segments, min_length=10):
    # Example pure function
    return [seg for seg in segments if seg[1] - seg[0] >= min_length]

# ...other pure logic functions...
