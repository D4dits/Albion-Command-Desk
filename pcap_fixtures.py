from __future__ import annotations

from pathlib import Path
import os


def _pcap_dirs() -> list[Path]:
    env = os.environ.get("ALBION_DPS_PCAP_DIR")
    dirs: list[Path] = []
    if env:
        for entry in env.split(os.pathsep):
            if entry:
                dirs.append(Path(entry))
    dirs.extend([Path("albion_dps/artifacts/pcaps"), Path("artifacts/pcaps")])
    return dirs


def resolve_pcap(name: str | Path) -> Path:
    path = Path(name)
    if path.exists():
        return path
    if path.is_absolute() and path.exists():
        return path

    candidates: list[Path] = []
    if path.suffix != ".pcap":
        candidates.append(Path(f"{path}.pcap"))
    candidates.append(path)

    for base in _pcap_dirs():
        for candidate in candidates:
            resolved = base / candidate
            if resolved.exists():
                return resolved

    for base in _pcap_dirs():
        return base / candidates[0]
    return candidates[0]
