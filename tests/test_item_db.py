from __future__ import annotations

import os
import xml.etree.ElementTree as ET

from albion_dps.domain import item_db


class _Logger:
    def __init__(self) -> None:
        self.infos: list[str] = []

    def info(self, message, *args) -> None:
        self.infos.append(str(message) % args if args else str(message))

    def warning(self, *_args, **_kwargs) -> None:
        return

    def error(self, *_args, **_kwargs) -> None:
        return

    def exception(self, *_args, **_kwargs) -> None:
        return


def _make_game_root(tmp_path):
    game = tmp_path / "Albion" / "game"
    data = game / "Albion-Online_Data" / "StreamingAssets" / "GameData"
    data.mkdir(parents=True)
    (data / "items.bin").write_bytes(b"items")
    (data / "localization.bin").write_bytes(b"loc")
    return tmp_path / "Albion"


def _make_repo_data(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for name in ("indexedItems.json", "items.json", "map_index.json"):
        (data_dir / name).write_text("[]", encoding="utf-8")
    return data_dir


def test_ensure_game_databases_rebuilds_stale_local_data(monkeypatch, tmp_path) -> None:
    game_root = _make_game_root(tmp_path)
    data_dir = _make_repo_data(tmp_path)
    old_time = 1000
    new_time = 2000
    for path in data_dir.iterdir():
        os.utime(path, (old_time, old_time))
    game_data = game_root / "game" / "Albion-Online_Data" / "StreamingAssets" / "GameData"
    os.utime(game_data / "items.bin", (new_time, new_time))
    os.utime(game_data / "localization.bin", (new_time, new_time))
    calls: list[str] = []

    monkeypatch.setattr(item_db, "DATA_DIR", data_dir)
    monkeypatch.setattr(item_db, "DEFAULT_INDEXED_PATHS", (data_dir / "indexedItems.json",))
    monkeypatch.setattr(item_db, "DEFAULT_ITEMS_PATHS", (data_dir / "items.json",))
    monkeypatch.setattr(item_db, "DEFAULT_MAP_INDEX_PATHS", (data_dir / "map_index.json",))
    monkeypatch.setattr(item_db, "_resolve_game_root", lambda _logger: game_root)
    monkeypatch.setattr(item_db, "_run_extractor", lambda root, *, logger: calls.append(str(root)) or True)

    assert item_db.ensure_game_databases(logger=_Logger(), interactive=False)
    assert calls == [str(game_root)]


def test_game_database_health_reports_stale_local_data(monkeypatch, tmp_path) -> None:
    game_root = _make_game_root(tmp_path)
    data_dir = _make_repo_data(tmp_path)
    old_time = 1000
    new_time = 2000
    for path in data_dir.iterdir():
        os.utime(path, (old_time, old_time))
    game_data = game_root / "game" / "Albion-Online_Data" / "StreamingAssets" / "GameData"
    os.utime(game_data / "items.bin", (new_time, new_time))
    os.utime(game_data / "localization.bin", (new_time, new_time))

    monkeypatch.setattr(item_db, "DATA_DIR", data_dir)
    monkeypatch.setattr(item_db, "DEFAULT_INDEXED_PATHS", (data_dir / "indexedItems.json",))
    monkeypatch.setattr(item_db, "DEFAULT_ITEMS_PATHS", (data_dir / "items.json",))
    monkeypatch.setattr(item_db, "DEFAULT_MAP_INDEX_PATHS", (data_dir / "map_index.json",))
    monkeypatch.setattr(item_db, "_resolve_game_root", lambda _logger: game_root)

    health = item_db.get_game_database_health(logger=_Logger())

    assert health["ready"] is False
    assert "older than the Albion game files" in str(health["detail"])


def test_extractor_targets_supported_dotnet_sdk() -> None:
    project_path = item_db.REPO_ROOT / "tools" / "extract_items" / "ExtractItems.csproj"
    root = ET.parse(project_path).getroot()
    target = root.findtext("./PropertyGroup/TargetFramework")
    default_compile = root.findtext("./PropertyGroup/EnableDefaultCompileItems")

    assert target == "net8.0"
    assert default_compile == "false"
    compile_items = {node.attrib.get("Include", "") for node in root.findall("./ItemGroup/Compile")}
    assert compile_items == {"Program.cs", "src/**/*.cs"}


def test_extractor_scripts_allow_newer_dotnet_runtime() -> None:
    scripts = [
        item_db.REPO_ROOT / "tools" / "extract_items" / "run_extract_items.sh",
        item_db.REPO_ROOT / "tools" / "extract_items" / "run_extract_items.ps1",
    ]

    for script in scripts:
        assert "DOTNET_ROLL_FORWARD" in script.read_text(encoding="utf-8")


def test_dotnet_sdk_major_versions_parses_list_output() -> None:
    output = "8.0.301 [/usr/lib/dotnet/sdk]\n9.0.100 [/usr/lib/dotnet-9/sdk]\n"

    assert item_db._dotnet_sdk_major_versions(output) == {8, 9}


def test_dotnet_sdk_supported_rejects_missing_dotnet(monkeypatch) -> None:
    monkeypatch.setattr(item_db.shutil, "which", lambda _name: None)

    ok, detail = item_db._dotnet_sdk_supported(min_major=8)

    assert ok is False
    assert "dotnet is not available" in detail


def test_dotnet_sdk_supported_rejects_old_sdk(monkeypatch) -> None:
    class _Result:
        returncode = 0
        stdout = "7.0.410 [/usr/lib/dotnet/sdk]\n"
        stderr = ""

    monkeypatch.setattr(item_db.shutil, "which", lambda _name: "/usr/bin/dotnet")
    monkeypatch.setattr(item_db.subprocess, "run", lambda *_args, **_kwargs: _Result())

    ok, detail = item_db._dotnet_sdk_supported(min_major=8)

    assert ok is False
    assert "8.0 or newer" in detail


def test_dotnet_sdk_supported_accepts_newer_sdk(monkeypatch) -> None:
    class _Result:
        returncode = 0
        stdout = "9.0.100 [/usr/lib/dotnet/sdk]\n"
        stderr = ""

    monkeypatch.setattr(item_db.shutil, "which", lambda _name: "/usr/bin/dotnet")
    monkeypatch.setattr(item_db.subprocess, "run", lambda *_args, **_kwargs: _Result())

    ok, detail = item_db._dotnet_sdk_supported(min_major=8)

    assert ok is True
    assert detail == ""
