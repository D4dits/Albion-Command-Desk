from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable

from albion_dps.capture.udp_decode import decode_udp_frame
from albion_dps.models import RawPacket


@dataclass(frozen=True)
class _PcapConfig:
    endian: str
    ns_resolution: bool


_MAGIC = {
    b"\xd4\xc3\xb2\xa1": _PcapConfig("<", False),
    b"\xa1\xb2\xc3\xd4": _PcapConfig(">", False),
    b"\x4d\x3c\xb2\xa1": _PcapConfig("<", True),
    b"\xa1\xb2\x3c\x4d": _PcapConfig(">", True),
}


def replay_pcap(path: str | Path) -> Iterable[RawPacket]:
    path = Path(path)
    with path.open("rb") as handle:
        config = _read_global_header(handle)
        while True:
            header = handle.read(16)
            if not header:
                break
            if len(header) < 16:
                raise ValueError("Truncated pcap record header")
            ts_sec, ts_subsec, incl_len, _orig_len = struct.unpack(
                f"{config.endian}IIII", header
            )
            packet = handle.read(incl_len)
            if len(packet) < incl_len:
                raise ValueError("Truncated pcap record data")
            timestamp = _to_timestamp(ts_sec, ts_subsec, config)
            raw = decode_udp_frame(packet, timestamp)
            if raw is not None:
                yield raw


def _read_global_header(handle: BinaryIO) -> _PcapConfig:
    header = handle.read(24)
    if len(header) < 24:
        raise ValueError("Truncated pcap global header")
    config = _MAGIC.get(header[:4])
    if config is None:
        raise ValueError("Unsupported pcap magic")
    _version_major, _version_minor, _thiszone, _sigfigs, _snaplen, network = struct.unpack(
        f"{config.endian}HHIIII", header[4:]
    )
    if network != 1:
        raise ValueError(f"Unsupported link type: {network}")
    return config


def _to_timestamp(ts_sec: int, ts_subsec: int, config: _PcapConfig) -> float:
    divisor = 1_000_000_000 if config.ns_resolution else 1_000_000
    return ts_sec + ts_subsec / divisor
