from __future__ import annotations

from importlib.metadata import PackageNotFoundError

from albion_dps import __version__
from albion_dps import cli
from albion_dps.qt import runner
from albion_dps.versioning import resolve_app_version


def test_resolve_app_version_falls_back_to_local_dev(monkeypatch) -> None:
    def _raise(_name: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr("albion_dps.versioning.package_version", _raise)

    assert resolve_app_version() == "local-dev"


def test_cli_and_runner_share_same_version_source(monkeypatch) -> None:
    monkeypatch.setattr("albion_dps.versioning.package_version", lambda _name: "9.9.9")

    assert resolve_app_version() == "9.9.9"
    assert cli._resolve_cli_version() == "9.9.9"
    assert runner._current_app_version() == "9.9.9"


def test_module_version_tracks_shared_version_helper(monkeypatch) -> None:
    _ = monkeypatch
    assert __version__ == resolve_app_version()
