import os
import tempfile
from logic.file_utils import is_audio_file, list_audio_files_in_dir, filter_audio_files

def test_is_audio_file():
    assert is_audio_file('test.mp3')
    assert is_audio_file('test.wav')
    assert not is_audio_file('test.txt')
    assert not is_audio_file('test.MP4')

def test_filter_audio_files():
    files = ['a.mp3', 'b.wav', 'c.txt', 'd.mp3']
    assert filter_audio_files(files) == ['a.mp3', 'b.wav', 'd.mp3']

def test_list_audio_files_in_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'sub'))
        files = [
            os.path.join(tmpdir, 'a.mp3'),
            os.path.join(tmpdir, 'b.wav'),
            os.path.join(tmpdir, 'c.txt'),
            os.path.join(tmpdir, 'sub', 'd.mp3'),
        ]
        for f in files:
            with open(f, 'w') as fp:
                fp.write('test')
        found = list_audio_files_in_dir(tmpdir)
        assert set(found) == set([files[0], files[1], files[3]])
