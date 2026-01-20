from __future__ import annotations

import struct

from albion_dps.models import RawPacket


def decode_udp_frame(frame: bytes, timestamp: float) -> RawPacket | None:
    if len(frame) < 14:
        return None
    eth_type = struct.unpack("!H", frame[12:14])[0]
    if eth_type != 0x0800:
        return None

    ip_offset = 14
    if len(frame) < ip_offset + 20:
        return None

    version_ihl = frame[ip_offset]
    version = version_ihl >> 4
    ihl = (version_ihl & 0x0F) * 4
    if version != 4 or ihl < 20:
        return None
    if len(frame) < ip_offset + ihl + 8:
        return None

    protocol = frame[ip_offset + 9]
    if protocol != 17:
        return None

    src_ip = _format_ip(frame[ip_offset + 12 : ip_offset + 16])
    dst_ip = _format_ip(frame[ip_offset + 16 : ip_offset + 20])

    udp_offset = ip_offset + ihl
    src_port, dst_port, udp_len, _checksum = struct.unpack(
        "!HHHH", frame[udp_offset : udp_offset + 8]
    )
    payload_start = udp_offset + 8
    payload_len = max(0, udp_len - 8)
    payload_end = min(len(frame), payload_start + payload_len)
    payload = frame[payload_start:payload_end]

    return RawPacket(timestamp, src_ip, src_port, dst_ip, dst_port, payload)


def _format_ip(raw: bytes) -> str:
    return ".".join(str(part) for part in raw)
