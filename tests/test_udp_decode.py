from __future__ import annotations

import ipaddress
import struct

from albion_dps.capture.udp_decode import decode_udp_frame, is_photon_packet, looks_like_photon
from albion_dps.models import RawPacket


def _build_eth(eth_type: int, payload: bytes) -> bytes:
    return b"\x00" * 12 + struct.pack("!H", eth_type) + payload


def _ipv4_bytes(ip: str) -> bytes:
    return bytes(int(part) for part in ip.split("."))


def _ipv6_bytes(ip: str) -> bytes:
    return ipaddress.IPv6Address(ip).packed


def _build_ipv4_udp(
    payload: bytes,
    *,
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
) -> bytes:
    version_ihl = 0x45
    total_len = 20 + 8 + len(payload)
    ip_header = struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl,
        0,
        total_len,
        0,
        0,
        64,
        17,
        0,
        _ipv4_bytes(src_ip),
        _ipv4_bytes(dst_ip),
    )
    udp_len = 8 + len(payload)
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_len, 0)
    return ip_header + udp_header + payload


def _build_ipv6_udp(
    payload: bytes,
    *,
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
) -> bytes:
    udp_len = 8 + len(payload)
    ip_header = struct.pack(
        "!IHBB16s16s",
        0x60000000,
        udp_len,
        17,
        64,
        _ipv6_bytes(src_ip),
        _ipv6_bytes(dst_ip),
    )
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_len, 0)
    return ip_header + udp_header + payload


def test_decode_ipv4_udp_frame() -> None:
    payload = b"\xf1\x00\x00hello"
    frame = _build_eth(
        0x0800,
        _build_ipv4_udp(
            payload,
            src_ip="1.2.3.4",
            dst_ip="5.6.7.8",
            src_port=1234,
            dst_port=5056,
        ),
    )
    packet = decode_udp_frame(frame, 1.0)
    assert packet is not None
    assert packet.src_ip == "1.2.3.4"
    assert packet.dst_ip == "5.6.7.8"
    assert packet.src_port == 1234
    assert packet.dst_port == 5056
    assert packet.payload == payload


def test_decode_ipv6_udp_frame() -> None:
    payload = b"\xf2\x00\x00world"
    frame = _build_eth(
        0x86DD,
        _build_ipv6_udp(
            payload,
            src_ip="2001:db8::1",
            dst_ip="2001:db8::2",
            src_port=5555,
            dst_port=6000,
        ),
    )
    packet = decode_udp_frame(frame, 2.0)
    assert packet is not None
    assert packet.src_ip == "2001:db8::1"
    assert packet.dst_ip == "2001:db8::2"
    assert packet.src_port == 5555
    assert packet.dst_port == 6000
    assert packet.payload == payload


def test_photon_fallback_checks() -> None:
    assert looks_like_photon(b"\xf1\x00\x00") is True
    assert looks_like_photon(b"\x00\x00") is False

    via_magic = RawPacket(0.0, "::1", 4000, "::1", 4001, b"\xfe\x00\x00")
    assert is_photon_packet(via_magic) is True

    via_port = RawPacket(0.0, "127.0.0.1", 5056, "127.0.0.1", 4001, b"\x01\x02\x03")
    assert is_photon_packet(via_port) is True

    empty_payload = RawPacket(0.0, "127.0.0.1", 5056, "127.0.0.1", 4001, b"")
    assert is_photon_packet(empty_payload) is False
