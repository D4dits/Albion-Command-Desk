from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    update_auto_check: bool = True


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
        )
    except Exception:
        return AppSettings()


def save_app_settings(settings: AppSettings) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "update_auto_check": bool(settings.update_auto_check),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def sys_platform() -> str:
    return os.environ.get("ALBION_COMMAND_DESK_PLATFORM", os.sys.platform).lower()
