import os
from typing import List

# Supported audio file extensions (lowercase, with dot)
SUPPORTED_AUDIO_EXTENSIONS = ('.mp3', '.wav')

def is_audio_file(filename: str) -> bool:
    """Return True if the file is a supported audio file."""
    return filename.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS)

def list_audio_files_in_dir(directory: str) -> List[str]:
    """Recursively list all supported audio files in a directory."""
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if is_audio_file(file):
                audio_files.append(os.path.join(root, file))
    return audio_files

def filter_audio_files(filepaths: List[str]) -> List[str]:
    """Filter a list of file paths to only supported audio files."""
    return [f for f in filepaths if is_audio_file(f)]
