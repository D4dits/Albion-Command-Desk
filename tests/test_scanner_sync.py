from __future__ import annotations

import json
import zipfile
from pathlib import Path

from albion_dps.capture.npcap_runtime import NpcapRuntimeStatus, RUNTIME_STATE_AVAILABLE
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


def test_scanner_sync_is_blocked_while_running(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_scanner_blocked_sync")
    state = ScannerState()
    state.clearLog()
    state._process = object()  # type: ignore[assignment]

    state.syncClientRepo()

    assert "Stop scanner before syncing the repository." in state.logText


def test_scanner_update_check_is_blocked_while_running(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_scanner_blocked_update")
    state = ScannerState()
    state.clearLog()
    state._process = object()  # type: ignore[assignment]

    state.checkForUpdates()

    assert "Stop scanner before checking repository updates." in state.logText


def test_scanner_runtime_reconciliation_when_runtime_added_late(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_scanner_runtime_reconcile")
    monkeypatch.setattr("albion_dps.qt.scanner._is_windows", lambda: True)
    monkeypatch.setattr(
        "albion_dps.qt.scanner.detect_npcap_runtime",
        lambda: NpcapRuntimeStatus(
            state=RUNTIME_STATE_AVAILABLE,
            available=True,
            detail="Found wpcap.dll",
        ),
    )
    monkeypatch.setattr("albion_dps.qt.scanner.capture_backend_available", lambda: True)
    monkeypatch.setattr(ScannerState, "_resolve_cli_executable", lambda self: Path("C:/tmp/albion-command-desk.exe"))

    state = ScannerState(app_mode="core")

    assert state.captureRuntimeState == "available"
    assert state.captureRuntimeActionLabel == "Switch shortcuts to live"
    assert "core mode" in state.captureRuntimeInstallHint.lower()
    assert state.captureRuntimeInstallCommand.endswith('" live')


def test_scanner_runtime_reconciliation_not_offered_in_live_mode(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_scanner_runtime_live_mode")
    monkeypatch.setattr("albion_dps.qt.scanner._is_windows", lambda: True)
    monkeypatch.setattr(
        "albion_dps.qt.scanner.detect_npcap_runtime",
        lambda: NpcapRuntimeStatus(
            state=RUNTIME_STATE_AVAILABLE,
            available=True,
            detail="Found wpcap.dll",
        ),
    )
    monkeypatch.setattr("albion_dps.qt.scanner.capture_backend_available", lambda: True)
    monkeypatch.setattr(ScannerState, "_resolve_cli_executable", lambda self: Path("C:/tmp/albion-command-desk.exe"))

    state = ScannerState(app_mode="live")

    assert state.captureRuntimeState == "available"
    assert state.captureRuntimeActionLabel == ""
    assert state.captureRuntimeInstallCommand == ""


def test_open_capture_runtime_action_repairs_shortcuts_when_reconcile_available(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", "artifacts/tmp/test_scanner_runtime_repair_action")
    monkeypatch.setattr("albion_dps.qt.scanner._is_windows", lambda: True)
    monkeypatch.setattr(
        "albion_dps.qt.scanner.detect_npcap_runtime",
        lambda: NpcapRuntimeStatus(
            state=RUNTIME_STATE_AVAILABLE,
            available=True,
            detail="Found wpcap.dll",
        ),
    )
    monkeypatch.setattr("albion_dps.qt.scanner.capture_backend_available", lambda: True)
    monkeypatch.setattr(ScannerState, "_resolve_cli_executable", lambda self: Path("C:/tmp/albion-command-desk.exe"))
    repaired: list[tuple[str, str]] = []

    def _fake_create(self, cli_path: Path, launch_mode: str) -> list[Path]:
        repaired.append((str(cli_path), launch_mode))
        return [Path("C:/Users/Test/Desktop/Albion Command Desk.lnk")]

    monkeypatch.setattr(ScannerState, "_create_windows_shortcuts", _fake_create)

    state = ScannerState(app_mode="core")
    state.clearLog()

    state.openCaptureRuntimeAction()

    assert repaired == [("C:\\tmp\\albion-command-desk.exe", "live")]
    assert "Updated Albion Command Desk shortcuts to launch live mode." in state.logText
