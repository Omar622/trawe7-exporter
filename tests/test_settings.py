"""Settings persistence round-trip and graceful fallback."""
import json

from services import settings as S


def test_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "SETTINGS_PATH", tmp_path / "settings.json")
    assert S.load_settings() == S.DEFAULTS


def test_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "SETTINGS_PATH", tmp_path / "cfg" / "settings.json")
    assert S.save_settings({"silence_threshold": -25, "min_silence": 0.8, "min_segment": 15})
    loaded = S.load_settings()
    assert loaded == {"silence_threshold": -25, "min_silence": 0.8, "min_segment": 15}


def test_corrupt_returns_defaults(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    path.write_text("{ not valid json")
    monkeypatch.setattr(S, "SETTINGS_PATH", path)
    assert S.load_settings() == S.DEFAULTS


def test_partial_file_merges_defaults(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"min_segment": 20}))
    monkeypatch.setattr(S, "SETTINGS_PATH", path)
    loaded = S.load_settings()
    assert loaded["min_segment"] == 20
    assert loaded["silence_threshold"] == S.DEFAULTS["silence_threshold"]
