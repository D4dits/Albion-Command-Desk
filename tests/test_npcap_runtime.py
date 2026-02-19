from __future__ import annotations

from pathlib import Path
import uuid

from albion_dps.capture import npcap_runtime


def test_detect_npcap_runtime_non_windows(monkeypatch) -> None:
    monkeypatch.setattr(npcap_runtime.os, "name", "posix", raising=False)
    status = npcap_runtime.detect_npcap_runtime()
    assert status.state == npcap_runtime.RUNTIME_STATE_AVAILABLE
    assert status.available is True


def _tmp_dir() -> Path:
    base = Path("artifacts") / "tmp" / "npcap_runtime_tests" / str(uuid.uuid4())
    base.mkdir(parents=True, exist_ok=True)
    return base


def test_detect_npcap_runtime_windows_missing(monkeypatch) -> None:
    tmp_path = _tmp_dir()
    monkeypatch.setattr(npcap_runtime.os, "name", "nt", raising=False)
    monkeypatch.setattr(npcap_runtime, "_candidate_npcap_dlls", lambda: [tmp_path / "missing.dll"])
    monkeypatch.setattr(npcap_runtime, "_npcap_service_image_path", lambda: None)
    monkeypatch.setattr(npcap_runtime.ctypes.util, "find_library", lambda _: None)

    status = npcap_runtime.detect_npcap_runtime()
    assert status.state == npcap_runtime.RUNTIME_STATE_MISSING
    assert status.available is False
    assert "npcap.com/#download" in status.detail


def test_detect_npcap_runtime_windows_from_dll(monkeypatch) -> None:
    tmp_path = _tmp_dir()
    dll_dir = tmp_path / "Npcap"
    dll_dir.mkdir(parents=True, exist_ok=True)
    dll_file = dll_dir / "wpcap.dll"
    dll_file.write_bytes(b"")

    monkeypatch.setattr(npcap_runtime.os, "name", "nt", raising=False)
    monkeypatch.setattr(npcap_runtime, "_candidate_npcap_dlls", lambda: [dll_file])
    monkeypatch.setattr(npcap_runtime, "_npcap_service_image_path", lambda: None)
    monkeypatch.setattr(npcap_runtime.ctypes.util, "find_library", lambda _: None)

    status = npcap_runtime.detect_npcap_runtime()
    assert status.state == npcap_runtime.RUNTIME_STATE_AVAILABLE
    assert status.available is True
    assert status.install_path == str(dll_dir)


def test_detect_npcap_runtime_windows_blocked_service_only(monkeypatch) -> None:
    tmp_path = _tmp_dir()
    monkeypatch.setattr(npcap_runtime.os, "name", "nt", raising=False)
    monkeypatch.setattr(npcap_runtime, "_candidate_npcap_dlls", lambda: [tmp_path / "missing.dll"])
    monkeypatch.setattr(npcap_runtime, "_npcap_service_image_path", lambda: r"C:\Windows\System32\drivers\npcap.sys")
    monkeypatch.setattr(npcap_runtime.ctypes.util, "find_library", lambda _: None)

    status = npcap_runtime.detect_npcap_runtime()
    assert status.state == npcap_runtime.RUNTIME_STATE_BLOCKED
    assert status.available is False
    assert status.action_url == npcap_runtime.NPCAP_DOWNLOAD_URL
