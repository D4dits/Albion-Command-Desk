from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


GAME_ROOT_ENV = "ALBION_DPS_GAME_ROOT"
PROMPT_DISABLE_ENV = "ALBION_DPS_DISABLE_GAME_ROOT_PROMPT"
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
DEFAULT_GAME_ROOT_FILE = DATA_DIR / "game_root.txt"
DEFAULT_INDEXED_PATHS = (
    DATA_DIR / "indexedItems.json",
    DATA_DIR / "indexed_items.json",
    Path("data/indexedItems.json"),
    Path("data/indexed_items.json"),
    Path("indexedItems.json"),
)
DEFAULT_ITEMS_PATHS = (
    DATA_DIR / "items.json",
    Path("data/items.json"),
    Path("items.json"),
)
DEFAULT_MAP_INDEX_PATHS = (
    DATA_DIR / "map_index.json",
    Path("data/map_index.json"),
    Path("map_index.json"),
)
MIN_EXTRACTOR_DOTNET_SDK_MAJOR = 8


class _NullLogger:
    def warning(self, *_args, **_kwargs) -> None:
        return

    def info(self, *_args, **_kwargs) -> None:
        return

    def error(self, *_args, **_kwargs) -> None:
        return

    def exception(self, *_args, **_kwargs) -> None:
        return


def ensure_game_databases(*, logger, interactive: bool = True) -> bool:
    has_items = _has_indexed_items()
    has_catalog = _has_items_catalog()
    has_maps = _has_map_index()
    game_root = _resolve_game_root(logger)
    if has_items and has_catalog and has_maps:
        if game_root is None or not _databases_stale(game_root):
            return True
        logger.info("Local game databases are older than Albion game data; rebuilding.")
        return _run_extractor(game_root, logger=logger)

    if not interactive:
        if game_root is not None and not os.environ.get(PROMPT_DISABLE_ENV):
            return _run_extractor(game_root, logger=logger)
        return False
    if os.environ.get(PROMPT_DISABLE_ENV):
        return False

    if game_root is None:
        game_root = _prompt_game_root(logger)
        if game_root is None:
            return False
        _persist_game_root(game_root, logger)

    if not _is_valid_game_root(game_root):
        logger.warning("Selected game root is invalid: %s", game_root)
        return False

    return _run_extractor(game_root, logger=logger)


def ensure_item_databases(*, logger, interactive: bool = True) -> bool:
    return ensure_game_databases(logger=logger, interactive=interactive)


def get_game_database_health(*, logger=None) -> dict[str, str | bool]:
    has_items = _has_indexed_items()
    has_catalog = _has_items_catalog()
    has_maps = _has_map_index()

    missing: list[str] = []
    if not has_items:
        missing.append("indexedItems.json")
    if not has_catalog:
        missing.append("items.json")
    if not has_maps:
        missing.append("map_index.json")

    logger_obj = logger or _NullLogger()
    resolved_root = _resolve_game_root(logger_obj)
    root_text = str(resolved_root) if resolved_root is not None else ""
    stale = bool(resolved_root is not None and has_items and has_catalog and has_maps and _databases_stale(resolved_root))
    ready = has_items and has_catalog and has_maps and not stale

    if ready:
        detail = "All local game databases are present."
        hint = "No action required."
        action_label = "Rebuild data"
    elif stale:
        detail = "Local game databases are older than the Albion game files."
        hint = "Rebuild data to refresh item, enchantment, and map indexes."
        action_label = "Rebuild data"
    else:
        detail = "Missing local game databases: " + ", ".join(missing)
        if resolved_root is None:
            hint = "Select Albion Online folder to extract missing databases."
        else:
            hint = (
                "Detected game folder: "
                + root_text
                + ". Re-run extractor if files are stale or incomplete."
            )
        action_label = "Select game folder"

    return {
        "ready": ready,
        "detail": detail,
        "hint": hint,
        "action_label": action_label,
        "game_root": root_text,
    }


def _has_indexed_items() -> bool:
    for path in DEFAULT_INDEXED_PATHS:
        if path.exists():
            return True
    env_val = os.environ.get("ALBION_DPS_INDEXED_ITEMS")
    if env_val and Path(env_val).exists():
        return True
    return False


def _has_map_index() -> bool:
    for path in DEFAULT_MAP_INDEX_PATHS:
        if path.exists():
            return True
    env_val = os.environ.get("ALBION_DPS_MAP_INDEX")
    if env_val and Path(env_val).exists():
        return True
    return False


def _has_items_catalog() -> bool:
    for path in DEFAULT_ITEMS_PATHS:
        if path.exists():
            return True
    env_val = os.environ.get("ALBION_DPS_ITEMS_JSON")
    if env_val and Path(env_val).exists():
        return True
    return False


def _databases_stale(game_root: Path) -> bool:
    game_folder = _resolve_game_folder(game_root)
    if game_folder is None:
        return False
    source_files = [
        game_folder / "Albion-Online_Data" / "StreamingAssets" / "GameData" / "items.bin",
        game_folder / "Albion-Online_Data" / "StreamingAssets" / "GameData" / "localization.bin",
    ]
    source_mtime = max((path.stat().st_mtime for path in source_files if path.exists()), default=0.0)
    if source_mtime <= 0:
        return False
    for path in (DATA_DIR / "indexedItems.json", DATA_DIR / "items.json", DATA_DIR / "map_index.json"):
        if not path.exists() or path.stat().st_mtime < source_mtime:
            return True
    return False


def _resolve_game_root(logger) -> Path | None:
    env_val = os.environ.get(GAME_ROOT_ENV)
    if env_val:
        path = Path(env_val)
        if _is_valid_game_root(path):
            return path
        logger.warning("ALBION_DPS_GAME_ROOT is invalid: %s", path)
    if DEFAULT_GAME_ROOT_FILE.exists():
        stored = DEFAULT_GAME_ROOT_FILE.read_text(encoding="utf-8").strip()
        if stored:
            path = Path(stored)
            if _is_valid_game_root(path):
                return path
            logger.warning("Stored game root is invalid: %s", path)
    auto_path = _auto_detect_game_root()
    if auto_path is not None:
        logger.info("Auto-detected game root: %s", auto_path)
        return auto_path
    return None


def _prompt_game_root(logger) -> Path | None:
    if not sys.stdin.isatty():
        return None
    if sys.platform != "win32":
        try:
            print("Enter Albion Online install folder path (empty to cancel): ", end="", flush=True)
            folder = input().strip()
        except EOFError:
            return None
        if not folder:
            return None
        return Path(folder)

    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        logger.exception("Failed to load tkinter for folder picker.")
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title="Select Albion Online folder")
    root.destroy()
    if not folder:
        return None
    return Path(folder)


def _persist_game_root(path: Path, logger) -> None:
    try:
        DEFAULT_GAME_ROOT_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_GAME_ROOT_FILE.write_text(str(path), encoding="utf-8")
    except Exception:
        logger.exception("Failed to persist game root: %s", path)


def _is_valid_game_root(path: Path) -> bool:
    return _resolve_game_folder(path) is not None


def _resolve_game_folder(path: Path) -> Path | None:
    if _is_valid_game_folder(path):
        return path
    for candidate in _candidate_game_folders(path):
        if _is_valid_game_folder(candidate):
            return candidate
    return None


def _candidate_game_folders(base: Path) -> list[Path]:
    candidates: list[Path] = []
    if sys.platform == "win32":
        candidates.append(base / "game")
    elif sys.platform == "darwin":
        candidates.extend(
            [
                base / "game",
                base / "game_x64",
                base / "game-x64",
            ]
        )
    else:
        candidates.extend(
            [
                base / "game_x64",
                base / "game-x64",
                base / "game",
            ]
        )
    return candidates


def _is_valid_game_folder(path: Path) -> bool:
    items_bin = path / "Albion-Online_Data" / "StreamingAssets" / "GameData" / "items.bin"
    localization_bin = (
        path / "Albion-Online_Data" / "StreamingAssets" / "GameData" / "localization.bin"
    )
    return items_bin.exists() and localization_bin.exists()


def _auto_detect_game_root() -> Path | None:
    candidates: list[Path] = []
    if sys.platform == "win32":
        candidates.extend(
            [
                Path(r"C:\Program Files\Albion Online"),
                Path(r"C:\Program Files (x86)\Albion Online"),
                Path(r"C:\Program Files\Steam\steamapps\common\Albion Online"),
                Path(r"C:\Program Files (x86)\Steam\steamapps\common\Albion Online"),
            ]
        )
    elif sys.platform == "darwin":
        candidates.extend(
            [
                Path("/Applications/Albion Online.app/Contents/Resources"),
                Path.home()
                / "Library"
                / "Application Support"
                / "Steam"
                / "steamapps"
                / "common"
                / "Albion Online",
            ]
        )
    else:
        candidates.extend(
            [
                Path.home() / ".steam" / "steam" / "steamapps" / "common" / "Albion Online",
                Path.home() / ".local" / "share" / "Steam" / "steamapps" / "common" / "Albion Online",
                Path("/datadisk/Albion Online"),
            ]
        )

    for candidate in candidates:
        if _is_valid_game_root(candidate):
            return candidate
    return None


def _run_extractor(game_root: Path, *, logger) -> bool:
    repo_root = REPO_ROOT
    resolved_root = _resolve_game_folder(game_root)
    if resolved_root is None:
        logger.error("Invalid game root: %s", game_root)
        return False
    dotnet_ok, dotnet_detail = _dotnet_sdk_supported(min_major=MIN_EXTRACTOR_DOTNET_SDK_MAJOR)
    if not dotnet_ok:
        logger.error("Cannot rebuild local game databases: %s", dotnet_detail)
        return False
    env = os.environ.copy()
    env["DOTNET_CLI_HOME"] = str(repo_root / "artifacts" / "dotnet")
    env["DOTNET_CLI_UI_LANGUAGE"] = "en"
    env["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1"
    env["NUGET_PACKAGES"] = str(repo_root / "artifacts" / "nuget")

    if sys.platform == "win32":
        script = repo_root / "tools" / "extract_items" / "run_extract_items.ps1"
        if not script.exists():
            logger.error("Extractor script missing: %s", script)
            return False
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-GameRoot",
            str(resolved_root),
            "-OutputDir",
            str(DATA_DIR),
        ]
    else:
        script = repo_root / "tools" / "extract_items" / "run_extract_items.sh"
        if not script.exists():
            logger.error("Extractor script missing: %s", script)
            return False
        cmd = [
            "bash",
            str(script),
            "--game-root",
            str(resolved_root),
            "--output",
            str(DATA_DIR),
            "--server",
            "live",
        ]

    result = subprocess.run(cmd, env=env, cwd=repo_root)
    if result.returncode != 0:
        logger.error("Extractor failed with code %s", result.returncode)
        return False
    return _has_indexed_items() and _has_items_catalog() and _has_map_index()


def _dotnet_sdk_supported(*, min_major: int) -> tuple[bool, str]:
    dotnet = shutil.which("dotnet")
    if not dotnet:
        return False, f".NET SDK {min_major}.0 or newer is required, but dotnet is not available in PATH."
    try:
        result = subprocess.run(
            [dotnet, "--list-sdks"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return False, f"failed to inspect .NET SDKs: {exc}"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return False, f"failed to inspect .NET SDKs: {detail or 'unknown dotnet error'}"
    majors = _dotnet_sdk_major_versions(result.stdout or "")
    if any(major >= int(min_major) for major in majors):
        return True, ""
    found = ", ".join(str(major) for major in sorted(majors)) or "none"
    return False, f".NET SDK {min_major}.0 or newer is required; installed SDK major versions: {found}."


def _dotnet_sdk_major_versions(output: str) -> set[int]:
    majors: set[int] = set()
    for line in str(output or "").splitlines():
        match = re.match(r"\s*(\d+)\.", line)
        if match is None:
            continue
        try:
            majors.add(int(match.group(1)))
        except ValueError:
            continue
    return majors
