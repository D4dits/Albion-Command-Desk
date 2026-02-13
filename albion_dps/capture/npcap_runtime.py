from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ctypes.util
import os

NPCAP_DOWNLOAD_URL = "https://npcap.com/#download"


@dataclass(frozen=True)
class NpcapRuntimeStatus:
    available: bool
    install_path: str | None = None
    detail: str = ""


def detect_npcap_runtime() -> NpcapRuntimeStatus:
    if os.name != "nt":
        return NpcapRuntimeStatus(available=True, detail="Npcap check is only required on Windows.")

    for candidate in _candidate_npcap_dlls():
        if candidate.exists():
            return NpcapRuntimeStatus(
                available=True,
                install_path=str(candidate.parent),
                detail=f"Found {candidate.name}",
            )

    service_path = _npcap_service_image_path()
    if service_path:
        return NpcapRuntimeStatus(
            available=True,
            install_path=service_path,
            detail="Found Npcap service registration.",
        )

    library_hint = ctypes.util.find_library("wpcap")
    if library_hint:
        return NpcapRuntimeStatus(
            available=True,
            install_path=library_hint,
            detail="Found wpcap via system library lookup.",
        )

    return NpcapRuntimeStatus(
        available=False,
        detail=(
            "Npcap Runtime was not detected. "
            f"Install it from {NPCAP_DOWNLOAD_URL}"
        ),
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
