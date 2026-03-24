from __future__ import annotations

from albion_dps.settings import (
    AppSettings,
    load_app_settings,
    save_app_settings,
    settings_path,
    update_app_settings,
)


def test_settings_roundtrip_with_override(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_settings")
    save_app_settings(
        AppSettings(
            update_auto_check=False,
            market_selected_preset="martlock_plate",
            market_export_dir="artifacts/tmp/exports",
            meter_export_dir="artifacts/tmp/meter_exports",
            scanner_repo_dir="artifacts/albiondata-client",
            scanner_repo_url="https://example.invalid/repo.git",
            log_level="DEBUG",
        )
    )
    loaded = load_app_settings()
    assert loaded.update_auto_check is False
    assert loaded.market_selected_preset == "martlock_plate"
    assert loaded.market_export_dir == "artifacts/tmp/exports"
    assert loaded.meter_export_dir == "artifacts/tmp/meter_exports"
    assert loaded.scanner_repo_dir == "artifacts/albiondata-client"
    assert loaded.scanner_repo_url == "https://example.invalid/repo.git"
    assert loaded.log_level == "DEBUG"
    assert settings_path().name == "settings.json"


def test_settings_defaults_on_missing_file(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_settings_missing")
    loaded = load_app_settings()
    assert loaded.update_auto_check is True
    assert loaded.meter_export_dir == ""
    assert loaded.scanner_repo_dir == ""
    assert loaded.scanner_repo_url == ""
    assert loaded.log_level == "INFO"


def test_update_app_settings_preserves_existing_fields(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_settings_merge")
    save_app_settings(
        AppSettings(
            update_auto_check=True,
            market_selected_preset="saved_fire",
            market_export_dir="artifacts/tmp/exports",
            meter_export_dir="artifacts/tmp/meter_exports",
            scanner_repo_dir="artifacts/albiondata-client",
            scanner_repo_url="https://example.invalid/repo.git",
            log_level="DEBUG",
        )
    )
    updated = update_app_settings(update_auto_check=False)
    assert updated.update_auto_check is False
    assert updated.market_selected_preset == "saved_fire"
    assert updated.market_export_dir == "artifacts/tmp/exports"
    assert updated.meter_export_dir == "artifacts/tmp/meter_exports"
    assert updated.scanner_repo_dir == "artifacts/albiondata-client"
    assert updated.scanner_repo_url == "https://example.invalid/repo.git"
    assert updated.log_level == "DEBUG"
