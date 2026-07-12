"""Optional audio playback. Falls back to a no-op backend when pygame is absent."""
from services.capabilities import detect_capabilities

_PYGAME_FORMATS = (".wav", ".mp3", ".ogg")


class AudioPlayer:
    """Backend-agnostic transport interface."""
    available = False

    def supports(self, path: str) -> bool:
        return False

    def load(self, path: str, duration: float = 0.0) -> None: ...
    def play(self) -> None: ...
    def pause(self) -> None: ...
    def stop(self) -> None: ...
    def seek(self, seconds: float) -> None: ...
    def position(self) -> float: return 0.0
    def duration(self) -> float: return 0.0
    def is_playing(self) -> bool: return False
    def is_loaded(self) -> bool: return False


class NullPlayer(AudioPlayer):
    """Used when no playback backend is available; scrubbing still works in the UI."""


class PygamePlayer(AudioPlayer):
    """pygame.mixer backend. Note: no .m4a support; seek on compressed audio is approximate."""
    available = True

    def __init__(self):
        import pygame
        self._pg = pygame
        pygame.mixer.init()
        self._path = None
        self._duration = 0.0
        self._offset = 0.0     # seek base, since get_pos() is relative to the last play()
        self._playing = False
        self._paused = False

    def supports(self, path: str) -> bool:
        return path.lower().endswith(_PYGAME_FORMATS)

    def load(self, path: str, duration: float = 0.0) -> None:
        self._pg.mixer.music.load(path)
        self._path = path
        self._duration = duration
        self._offset = 0.0
        self._playing = self._paused = False

    def play(self) -> None:
        if not self._path:
            return
        if self._paused:
            self._pg.mixer.music.unpause()
        else:
            self._pg.mixer.music.play(start=self._offset)
        self._playing, self._paused = True, False

    def pause(self) -> None:
        if self._playing and not self._paused:
            self._pg.mixer.music.pause()
            self._playing, self._paused = False, True

    def stop(self) -> None:
        self._pg.mixer.music.stop()
        self._offset = 0.0
        self._playing = self._paused = False

    def seek(self, seconds: float) -> None:
        self._offset = max(0.0, seconds)
        resume = self._playing
        self._pg.mixer.music.play(start=self._offset)
        if resume:
            self._playing, self._paused = True, False
        else:
            self._pg.mixer.music.pause()
            self._playing, self._paused = False, True

    def position(self) -> float:
        pos_ms = self._pg.mixer.music.get_pos()
        return self._offset if pos_ms < 0 else self._offset + pos_ms / 1000.0

    def duration(self) -> float:
        return self._duration

    def is_playing(self) -> bool:
        return self._playing and self._pg.mixer.music.get_busy()

    def is_loaded(self) -> bool:
        return self._path is not None


def make_player() -> AudioPlayer:
    if not detect_capabilities().playback:
        return NullPlayer()
    try:
        return PygamePlayer()
    except Exception:
        return NullPlayer()
