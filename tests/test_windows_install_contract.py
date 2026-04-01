from __future__ import annotations

from pathlib import Path


def test_windows_installer_exposes_prebuilt_capture_wheel_contract() -> None:
    script = Path("tools/install/windows/install.ps1").read_text(encoding="utf-8")
    assert '[string]$CaptureWheelPath = ""' in script
    assert "function Resolve-WindowsCaptureBackendWheel" in script
    assert "Installing prebuilt Windows live capture backend" in script
    assert "Use a release that bundles the Windows live capture component" in script


def test_windows_capture_audit_records_prebuilt_strategy() -> None:
    audit = Path("docs/release/WINDOWS_CAPTURE_AUDIT.md").read_text(encoding="utf-8")
    assert "Recommended strategy: **prebuilt Windows capture backend artifact**" in audit
    assert "Windows installer must prefer a bundled/prebuilt backend wheel" in audit


def test_windows_bootstrap_knows_capture_bundle_contract() -> None:
    script = Path("tools/release/windows/build_bootstrap_setup.ps1").read_text(encoding="utf-8")
    assert "AlbionCommandDesk-WindowsCapture-" in script
    assert "TryStageWindowsCaptureBundle" in script


def test_windows_capture_bundle_builder_contract() -> None:
    script = Path("tools/release/windows/build_capture_bundle.ps1").read_text(encoding="utf-8")
    assert "AlbionCommandDesk-WindowsCapture-" in script
    assert "bundle-manifest.json" in script
    assert "No wheel files found" in script


def test_windows_capture_backend_workflow_exists() -> None:
    workflow = Path(".github/workflows/windows-capture-backend.yml").read_text(encoding="utf-8")
    assert "name: windows-capture-backend" in workflow
    assert "build_capture_bundle.ps1" in workflow
    assert "dist/windows-capture/*.zip" in workflow
