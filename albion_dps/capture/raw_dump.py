from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from albion_dps.models import RawPacket


def dump_raw(packet: RawPacket, output_dir: str | Path = "artifacts/raw") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    ts_ms = int(packet.timestamp * 1000)
    digest = hashlib.sha256(packet.payload).hexdigest()
    file_path = output_path / f"{ts_ms}_{digest}.bin"
    file_path.write_bytes(packet.payload)

    logging.getLogger(__name__).info(
        "Raw payload saved path=%s ts=%s src=%s:%s dst=%s:%s len=%s",
        file_path,
        ts_ms,
        packet.src_ip,
        packet.src_port,
        packet.dst_ip,
        packet.dst_port,
        len(packet.payload),
    )
    return file_path
