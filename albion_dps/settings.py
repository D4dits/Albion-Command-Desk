from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    update_auto_check: bool = True
    market_selected_preset: str = ""
    market_export_dir: str = ""
    scanner_repo_dir: str = ""
    scanner_repo_url: str = ""
    log_level: str = "INFO"


def settings_dir() -> Path:
    override = os.environ.get("ALBION_COMMAND_DESK_CONFIG_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    home = Path.home()
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        return base / "AlbionCommandDesk"
    if sys_platform() == "darwin":
        return home / "Library" / "Application Support" / "AlbionCommandDesk"
    return home / ".config" / "albion-command-desk"


def settings_path() -> Path:
    return settings_dir() / "settings.json"


def load_app_settings() -> AppSettings:
    path = settings_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return AppSettings()
        return AppSettings(
            update_auto_check=bool(raw.get("update_auto_check", True)),
            market_selected_preset=str(raw.get("market_selected_preset", "") or ""),
            market_export_dir=str(raw.get("market_export_dir", "") or ""),
            scanner_repo_dir=str(raw.get("scanner_repo_dir", "") or ""),
            scanner_repo_url=str(raw.get("scanner_repo_url", "") or ""),
            log_level=_normalize_log_level(raw.get("log_level", "INFO")),
        )
    except Exception:
        return AppSettings()


def save_app_settings(settings: AppSettings) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "update_auto_check": bool(settings.update_auto_check),
        "market_selected_preset": str(settings.market_selected_preset or ""),
        "market_export_dir": str(settings.market_export_dir or ""),
        "scanner_repo_dir": str(settings.scanner_repo_dir or ""),
        "scanner_repo_url": str(settings.scanner_repo_url or ""),
        "log_level": _normalize_log_level(settings.log_level),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def update_app_settings(**changes) -> AppSettings:
    current = load_app_settings()
    if "log_level" in changes:
        changes["log_level"] = _normalize_log_level(changes["log_level"])
    updated = replace(current, **changes)
    save_app_settings(updated)
    return updated


def sys_platform() -> str:
    return os.environ.get("ALBION_COMMAND_DESK_PLATFORM", os.sys.platform).lower()


def _normalize_log_level(value) -> str:
    candidate = str(value or "INFO").strip().upper()
    if candidate not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
        return "INFO"
    return candidate
