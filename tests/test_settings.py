from __future__ import annotations

from albion_dps.settings import AppSettings, load_app_settings, save_app_settings, settings_path


def test_settings_roundtrip_with_override(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_settings")
    save_app_settings(AppSettings(update_auto_check=False))
    loaded = load_app_settings()
    assert loaded.update_auto_check is False
    assert settings_path().name == "settings.json"


def test_settings_defaults_on_missing_file(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_settings_missing")
    loaded = load_app_settings()
    assert loaded.update_auto_check is True
