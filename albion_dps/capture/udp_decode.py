from __future__ import annotations

import ipaddress
import struct

from albion_dps.models import RawPacket


PHOTON_UDP_PORTS = {5055, 5056, 5058}
PHOTON_MAGIC_PREFIXES = {0xF1, 0xF2, 0xFE}


def decode_udp_frame(frame: bytes, timestamp: float) -> RawPacket | None:
    if len(frame) < 14:
        return None
    eth_type = struct.unpack("!H", frame[12:14])[0]
    if eth_type not in (0x0800, 0x86DD):
        return None

    ip_offset = 14
    if eth_type == 0x0800:
        return _decode_ipv4_udp(frame, ip_offset, timestamp)
    return _decode_ipv6_udp(frame, ip_offset, timestamp)


def _format_ip(raw: bytes) -> str:
    return ".".join(str(part) for part in raw)


def _decode_ipv4_udp(frame: bytes, ip_offset: int, timestamp: float) -> RawPacket | None:
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


def _decode_ipv6_udp(frame: bytes, ip_offset: int, timestamp: float) -> RawPacket | None:
    if len(frame) < ip_offset + 40:
        return None

    version = frame[ip_offset] >> 4
    if version != 6:
        return None

    next_header = frame[ip_offset + 6]
    if next_header != 17:
        return None

    src_ip = _format_ip6(frame[ip_offset + 8 : ip_offset + 24])
    dst_ip = _format_ip6(frame[ip_offset + 24 : ip_offset + 40])

    udp_offset = ip_offset + 40
    if len(frame) < udp_offset + 8:
        return None

    src_port, dst_port, udp_len, _checksum = struct.unpack(
        "!HHHH", frame[udp_offset : udp_offset + 8]
    )
    payload_start = udp_offset + 8
    payload_len = max(0, udp_len - 8)
    payload_end = min(len(frame), payload_start + payload_len)
    payload = frame[payload_start:payload_end]

    return RawPacket(timestamp, src_ip, src_port, dst_ip, dst_port, payload)


def _format_ip6(raw: bytes) -> str:
    return str(ipaddress.IPv6Address(raw))


def looks_like_photon(payload: bytes) -> bool:
    if len(payload) < 3:
        return False
    return payload[0] in PHOTON_MAGIC_PREFIXES


def is_photon_packet(packet: RawPacket) -> bool:
    if not packet.payload:
        return False
    return (
        packet.src_port in PHOTON_UDP_PORTS
        or packet.dst_port in PHOTON_UDP_PORTS
        or looks_like_photon(packet.payload)
    )
