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
    meter_export_dir: str = ""
    meter_top_n: int = 20
    meter_history_limit: int = 20
    loot_log_keep_files: int = 5
    loot_buffer_seconds: int = 120
    loot_price_region: str = "europe"
    loot_price_city: str = "Bridgewatch"
    loot_self_guild: str = ""
    loot_self_alliance: str = ""
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
            meter_export_dir=str(raw.get("meter_export_dir", "") or ""),
            meter_top_n=_normalize_meter_top_n(raw.get("meter_top_n", 20)),
            meter_history_limit=_normalize_meter_history_limit(raw.get("meter_history_limit", 20)),
            loot_log_keep_files=_normalize_keep_files(raw.get("loot_log_keep_files", 5)),
            loot_buffer_seconds=_normalize_loot_buffer_seconds(
                raw.get("loot_buffer_seconds", 120)
            ),
            loot_price_region=_normalize_loot_region(raw.get("loot_price_region", "europe")),
            loot_price_city=str(raw.get("loot_price_city", "Bridgewatch") or "Bridgewatch"),
            loot_self_guild=str(raw.get("loot_self_guild", "") or ""),
            loot_self_alliance=str(raw.get("loot_self_alliance", "") or ""),
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
        "meter_export_dir": str(settings.meter_export_dir or ""),
        "meter_top_n": _normalize_meter_top_n(settings.meter_top_n),
        "meter_history_limit": _normalize_meter_history_limit(settings.meter_history_limit),
        "loot_log_keep_files": _normalize_keep_files(settings.loot_log_keep_files),
        "loot_buffer_seconds": _normalize_loot_buffer_seconds(settings.loot_buffer_seconds),
        "loot_price_region": _normalize_loot_region(settings.loot_price_region),
        "loot_price_city": str(settings.loot_price_city or "Bridgewatch"),
        "loot_self_guild": str(settings.loot_self_guild or ""),
        "loot_self_alliance": str(settings.loot_self_alliance or ""),
        "scanner_repo_dir": str(settings.scanner_repo_dir or ""),
        "scanner_repo_url": str(settings.scanner_repo_url or ""),
        "log_level": _normalize_log_level(settings.log_level),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def update_app_settings(**changes) -> AppSettings:
    current = load_app_settings()
    if "log_level" in changes:
        changes["log_level"] = _normalize_log_level(changes["log_level"])
    if "loot_log_keep_files" in changes:
        changes["loot_log_keep_files"] = _normalize_keep_files(changes["loot_log_keep_files"])
    if "loot_buffer_seconds" in changes:
        changes["loot_buffer_seconds"] = _normalize_loot_buffer_seconds(
            changes["loot_buffer_seconds"]
        )
    if "loot_price_region" in changes:
        changes["loot_price_region"] = _normalize_loot_region(changes["loot_price_region"])
    if "meter_top_n" in changes:
        changes["meter_top_n"] = _normalize_meter_top_n(changes["meter_top_n"])
    if "meter_history_limit" in changes:
        changes["meter_history_limit"] = _normalize_meter_history_limit(
            changes["meter_history_limit"]
        )
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


def _normalize_keep_files(value) -> int:
    try:
        keep = int(value)
    except (TypeError, ValueError):
        return 5
    return min(50, max(1, keep))


def _normalize_meter_top_n(value) -> int:
    try:
        top_n = int(value)
    except (TypeError, ValueError):
        return 20
    return min(40, max(1, top_n))


def _normalize_loot_buffer_seconds(value) -> int:
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return 120
    return min(600, max(0, seconds))


def _normalize_loot_region(value) -> str:
    candidate = str(value or "europe").strip().lower()
    return candidate if candidate in {"europe", "west", "east"} else "europe"


def _normalize_meter_history_limit(value) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return 20
    return min(200, max(1, limit))
