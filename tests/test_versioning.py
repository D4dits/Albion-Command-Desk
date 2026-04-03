from __future__ import annotations

from albion_dps import __version__
from albion_dps import cli
from albion_dps.qt import runner
from albion_dps.qt import scanner
from albion_dps.versioning import resolve_app_version


def test_resolve_app_version_falls_back_to_local_dev(monkeypatch) -> None:
    monkeypatch.setattr("albion_dps.versioning._read_checkout_version", lambda: None)
    monkeypatch.setattr("albion_dps.versioning._read_installed_version", lambda: None)

    assert resolve_app_version() == "local-dev"


def test_cli_and_runner_share_same_version_source(monkeypatch) -> None:
    monkeypatch.setattr("albion_dps.versioning._read_checkout_version", lambda: None)
    monkeypatch.setattr("albion_dps.versioning._read_installed_version", lambda: "9.9.9")

    assert resolve_app_version() == "9.9.9"
    assert cli._resolve_cli_version() == "9.9.9"
    assert runner._current_app_version() == "9.9.9"


def test_scanner_state_uses_shared_version_helper(monkeypatch) -> None:
    monkeypatch.setattr(scanner, "resolve_app_version", lambda: "9.9.9")

    state = scanner.ScannerState()

    assert state.appVersion == "9.9.9"


def test_module_version_tracks_shared_version_helper(monkeypatch) -> None:
    _ = monkeypatch
    assert __version__ == resolve_app_version()


def test_resolve_app_version_prefers_checkout_version_over_stale_metadata(monkeypatch) -> None:
    monkeypatch.setattr("albion_dps.versioning._read_checkout_version", lambda: "0.1.24")
    monkeypatch.setattr("albion_dps.versioning._read_installed_version", lambda: "0.1.20")

    assert resolve_app_version() == "0.1.24"
