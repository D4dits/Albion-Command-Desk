from __future__ import annotations

import json
import zipfile

from albion_dps.qt.scanner import ScannerState, _parse_rev_list_counts
from albion_dps.settings import AppSettings, save_app_settings


def test_parse_rev_list_counts_ok() -> None:
    assert _parse_rev_list_counts("3\t7") == (3, 7)
    assert _parse_rev_list_counts("0 0") == (0, 0)


def test_parse_rev_list_counts_invalid() -> None:
    assert _parse_rev_list_counts(None) is None
    assert _parse_rev_list_counts("") is None
    assert _parse_rev_list_counts("bad output") is None
    assert _parse_rev_list_counts("1") is None


def test_scanner_state_restores_repo_and_log_settings(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_scanner_state_settings")
    save_app_settings(
        AppSettings(
            scanner_repo_dir="artifacts/custom-client",
            scanner_repo_url="https://example.invalid/custom.git",
            log_level="DEBUG",
        )
    )
    state = ScannerState()
    assert state.scannerRepoDir.endswith("artifacts\\custom-client") or state.scannerRepoDir.endswith("artifacts/custom-client")
    assert state.scannerRepoUrl == "https://example.invalid/custom.git"
    assert state.appLogLevel == "DEBUG"


def test_scanner_state_exports_diagnostics_bundle(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_scanner_diagnostics")
    state = ScannerState()
    bundle_path = state.exportDiagnosticsBundle("Up to date", "Prices live", "line 1\nline 2")
    with zipfile.ZipFile(bundle_path, "r") as archive:
        names = set(archive.namelist())
        assert "summary.json" in names
        assert "scanner.log.txt" in names
        assert "market.diagnostics.txt" in names
        summary = json.loads(archive.read("summary.json").decode("utf-8"))
        assert summary["update_status"] == "Up to date"
        assert summary["market"]["status"] == "Prices live"
        assert summary["market"]["diagnostics_lines"] == 2
