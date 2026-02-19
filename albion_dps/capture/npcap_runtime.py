from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ctypes.util
import os

NPCAP_DOWNLOAD_URL = "https://npcap.com/#download"
RUNTIME_STATE_AVAILABLE = "available"
RUNTIME_STATE_MISSING = "missing"
RUNTIME_STATE_BLOCKED = "blocked"
RUNTIME_STATE_UNKNOWN = "unknown"


@dataclass(frozen=True)
class NpcapRuntimeStatus:
    state: str
    available: bool
    install_path: str | None = None
    detail: str = ""
    action_url: str | None = None


def detect_npcap_runtime() -> NpcapRuntimeStatus:
    if os.name != "nt":
        return NpcapRuntimeStatus(
            state=RUNTIME_STATE_AVAILABLE,
            available=True,
            detail="Npcap check is only required on Windows.",
        )

    try:
        for candidate in _candidate_npcap_dlls():
            if candidate.exists():
                return NpcapRuntimeStatus(
                    state=RUNTIME_STATE_AVAILABLE,
                    available=True,
                    install_path=str(candidate.parent),
                    detail=f"Found {candidate.name}",
                )

        service_path = _npcap_service_image_path()
        if service_path:
            return NpcapRuntimeStatus(
                state=RUNTIME_STATE_BLOCKED,
                available=False,
                install_path=service_path,
                detail=(
                    "Npcap service registration exists, but runtime DLLs were not found "
                    "in standard locations."
                ),
                action_url=NPCAP_DOWNLOAD_URL,
            )

        library_hint = ctypes.util.find_library("wpcap")
        if library_hint:
            return NpcapRuntimeStatus(
                state=RUNTIME_STATE_AVAILABLE,
                available=True,
                install_path=library_hint,
                detail="Found wpcap via system library lookup.",
            )
    except PermissionError as exc:
        return NpcapRuntimeStatus(
            state=RUNTIME_STATE_BLOCKED,
            available=False,
            detail=f"Permission denied while checking Npcap runtime: {exc}",
            action_url=NPCAP_DOWNLOAD_URL,
        )
    except Exception as exc:  # pragma: no cover - defensive branch
        return NpcapRuntimeStatus(
            state=RUNTIME_STATE_UNKNOWN,
            available=False,
            detail=f"Unexpected runtime detection failure: {exc}",
            action_url=NPCAP_DOWNLOAD_URL,
        )

    return NpcapRuntimeStatus(
        state=RUNTIME_STATE_MISSING,
        available=False,
        detail=(
            "Npcap Runtime was not detected. "
            f"Install it from {NPCAP_DOWNLOAD_URL}"
        ),
        action_url=NPCAP_DOWNLOAD_URL,
    )


def _candidate_npcap_dlls() -> list[Path]:
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    return [
        windir / "System32" / "Npcap" / "wpcap.dll",
        windir / "System32" / "Npcap" / "Packet.dll",
        windir / "SysWOW64" / "Npcap" / "wpcap.dll",
        windir / "SysWOW64" / "Npcap" / "Packet.dll",
    ]


def _npcap_service_image_path() -> str | None:
    try:
        import winreg
    except Exception:
        return None

    keys = (
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\npcap", "ImagePath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Npcap", "InstallLocation"),
    )
    for root, key_path, value_name in keys:
        try:
            with winreg.OpenKey(root, key_path) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
        except OSError:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
