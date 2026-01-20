from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from albion_dps.models import RawPacket


def dump_unknown(
    packet: RawPacket,
    reason: str | None = None,
    output_dir: str | Path = "artifacts/unknown",
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    ts_ms = int(packet.timestamp * 1000)
    digest = hashlib.sha256(packet.payload).hexdigest()
    file_path = output_path / f"{ts_ms}_{digest}.bin"
    file_path.write_bytes(packet.payload)

    log_reason = reason or "unknown"
    logging.getLogger(__name__).debug(
        "Unknown payload saved path=%s ts=%s src=%s:%s dst=%s:%s len=%s reason=%s",
        file_path,
        ts_ms,
        packet.src_ip,
        packet.src_port,
        packet.dst_ip,
        packet.dst_port,
        len(packet.payload),
        log_reason,
    )
    return file_path
