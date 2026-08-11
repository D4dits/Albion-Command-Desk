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

_PCAPNG_SECTION_HEADER = b"\x0a\x0d\x0d\x0a"
_PCAPNG_BYTE_ORDER = {
    b"\x4d\x3c\x2b\x1a": "<",
    b"\x1a\x2b\x3c\x4d": ">",
}
_PCAPNG_INTERFACE_DESCRIPTION = 0x00000001
_PCAPNG_SIMPLE_PACKET = 0x00000003
_PCAPNG_ENHANCED_PACKET = 0x00000006
_PCAPNG_OPTION_END = 0
_PCAPNG_OPTION_TS_RESOLUTION = 9


@dataclass(frozen=True)
class _PcapngInterface:
    link_type: int
    timestamp_resolution: float = 1e-6


def replay_pcap(path: str | Path) -> Iterable[RawPacket]:
    path = Path(path)
    with path.open("rb") as handle:
        yield from read_capture_stream(handle)


def read_capture_stream(handle: BinaryIO) -> Iterable[RawPacket]:
    """Read classic PCAP or PCAPNG without loading the capture into memory."""
    magic = handle.read(4)
    if len(magic) < 4:
        raise ValueError("Truncated capture header")
    try:
        handle.seek(-4, 1)
    except (OSError, AttributeError):
        handle = _PrefixedReader(magic, handle)
    if magic == _PCAPNG_SECTION_HEADER:
        yield from read_pcapng_stream(handle)
        return
    yield from read_pcap_stream(handle)


def read_pcap_stream(handle: BinaryIO) -> Iterable[RawPacket]:
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


def read_pcapng_stream(handle: BinaryIO) -> Iterable[RawPacket]:
    endian: str | None = None
    interfaces: list[_PcapngInterface] = []
    last_timestamp = 0.0

    while True:
        header = handle.read(12)
        if not header:
            break
        if len(header) < 12:
            raise ValueError("Truncated PCAPNG block header")

        raw_type = header[:4]
        if raw_type == _PCAPNG_SECTION_HEADER:
            section_endian = _PCAPNG_BYTE_ORDER.get(header[8:12])
            if section_endian is None:
                raise ValueError("Unsupported PCAPNG byte-order magic")
            total_length = struct.unpack(f"{section_endian}I", header[4:8])[0]
            endian = section_endian
            interfaces = []
        else:
            if endian is None:
                raise ValueError("PCAPNG block encountered before section header")
            total_length = struct.unpack(f"{endian}I", header[4:8])[0]

        if total_length < 12 or total_length % 4:
            raise ValueError("Invalid PCAPNG block length")
        remainder = handle.read(total_length - 12)
        if len(remainder) != total_length - 12:
            raise ValueError("Truncated PCAPNG block")
        block = header + remainder
        trailing_length = struct.unpack(f"{endian}I", block[-4:])[0]
        if trailing_length != total_length:
            raise ValueError("Mismatched PCAPNG block length")

        if raw_type == _PCAPNG_SECTION_HEADER:
            continue

        block_type = struct.unpack(f"{endian}I", raw_type)[0]
        body = block[8:-4]
        if block_type == _PCAPNG_INTERFACE_DESCRIPTION:
            if len(body) < 8:
                raise ValueError("Truncated PCAPNG interface description")
            link_type = struct.unpack(f"{endian}H", body[:2])[0]
            resolution = _pcapng_timestamp_resolution(body[8:], endian)
            interfaces.append(_PcapngInterface(link_type, resolution))
            continue

        if block_type == _PCAPNG_ENHANCED_PACKET:
            if len(body) < 20:
                raise ValueError("Truncated PCAPNG enhanced packet")
            interface_id, ts_high, ts_low, captured_len, _packet_len = struct.unpack(
                f"{endian}IIIII", body[:20]
            )
            if interface_id >= len(interfaces):
                continue
            interface = interfaces[interface_id]
            if interface.link_type != 1 or captured_len > len(body) - 20:
                continue
            timestamp_raw = (ts_high << 32) | ts_low
            last_timestamp = timestamp_raw * interface.timestamp_resolution
            raw = decode_udp_frame(body[20 : 20 + captured_len], last_timestamp)
            if raw is not None:
                yield raw
            continue

        if block_type == _PCAPNG_SIMPLE_PACKET:
            # Simple Packet Blocks do not carry a timestamp or interface id.
            if not interfaces or interfaces[0].link_type != 1 or len(body) < 4:
                continue
            original_len = struct.unpack(f"{endian}I", body[:4])[0]
            captured_len = min(original_len, len(body) - 4)
            raw = decode_udp_frame(body[4 : 4 + captured_len], last_timestamp)
            if raw is not None:
                yield raw


def _pcapng_timestamp_resolution(options: bytes, endian: str) -> float:
    offset = 0
    while offset + 4 <= len(options):
        code, length = struct.unpack_from(f"{endian}HH", options, offset)
        offset += 4
        value = options[offset : offset + length]
        offset += (length + 3) & ~3
        if code == _PCAPNG_OPTION_END:
            break
        if code != _PCAPNG_OPTION_TS_RESOLUTION or not value:
            continue
        raw = value[0]
        if raw & 0x80:
            return 2.0 ** -(raw & 0x7F)
        return 10.0 ** -raw
    return 1e-6


class _PrefixedReader:
    def __init__(self, prefix: bytes, handle: BinaryIO) -> None:
        self._prefix = bytearray(prefix)
        self._handle = handle

    def read(self, size: int = -1) -> bytes:
        if size == 0:
            return b""
        if size < 0:
            data = bytes(self._prefix)
            self._prefix.clear()
            return data + self._handle.read()
        head = bytes(self._prefix[:size])
        del self._prefix[:size]
        return head + self._handle.read(size - len(head))


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
