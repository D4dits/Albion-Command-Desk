from __future__ import annotations

import struct

from albion_dps.capture.replay_pcap import replay_pcap
from tests.support_temp import mk_test_dir


def _ip_bytes(ip: str) -> bytes:
    return bytes(int(part) for part in ip.split("."))


def _udp_frame(
    src_ip: str, dst_ip: str, src_port: int, dst_port: int, payload: bytes
) -> bytes:
    eth_header = (
        b"\xaa\xbb\xcc\xdd\xee\xff"
        + b"\x11\x22\x33\x44\x55\x66"
        + struct.pack("!H", 0x0800)
    )
    src_ip_bytes = _ip_bytes(src_ip)
    dst_ip_bytes = _ip_bytes(dst_ip)
    total_length = 20 + 8 + len(payload)
    ip_header = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        total_length,
        0,
        0,
        64,
        17,
        0,
        src_ip_bytes,
        dst_ip_bytes,
    )
    udp_length = 8 + len(payload)
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_length, 0)
    return eth_header + ip_header + udp_header + payload


def _pcap_bytes(frames: list[bytes]) -> bytes:
    header = b"\xd4\xc3\xb2\xa1" + struct.pack("<HHIIII", 2, 4, 0, 0, 65535, 1)
    chunks = [header]
    for index, frame in enumerate(frames):
        ts_sec = 100 + index
        ts_usec = 123456
        record_header = struct.pack("<IIII", ts_sec, ts_usec, len(frame), len(frame))
        chunks.append(record_header)
        chunks.append(frame)
    return b"".join(chunks)


def test_replay_pcap_deterministic() -> None:
    tmp_path = mk_test_dir("replay_pcap")
    frame1 = _udp_frame("192.168.1.10", "10.0.0.5", 1111, 5055, b"\x01\x02\x03")
    frame2 = _udp_frame("192.168.1.10", "10.0.0.5", 1111, 5055, b"\x04\x05")
    pcap = _pcap_bytes([frame1, frame2])
    path = tmp_path / "sample.pcap"
    path.write_bytes(pcap)

    first = list(replay_pcap(path))
    second = list(replay_pcap(path))

    assert len(first) == 2
    assert first == second
    assert first[0].payload == b"\x01\x02\x03"
    assert first[0].src_ip == "192.168.1.10"
    assert first[0].dst_port == 5055
