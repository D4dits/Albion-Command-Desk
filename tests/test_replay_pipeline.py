from __future__ import annotations

import struct

from albion_dps.meter.aggregate import RollingMeter
from albion_dps.models import CombatEvent
from albion_dps.pipeline import replay_snapshots
from albion_dps.protocol.photon_decode import PhotonDecoder
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


def test_replay_snapshots_from_pcap() -> None:
    tmp_path = mk_test_dir("replay_pipeline")
    payload_hex = "000100010000002A00000000060000000000001100000001000410AABB"
    frame = _udp_frame(
        "192.168.1.10",
        "10.0.0.5",
        1111,
        5055,
        bytes.fromhex(payload_hex),
    )
    pcap = _pcap_bytes([frame])
    path = tmp_path / "sample.pcap"
    path.write_bytes(pcap)

    decoder = PhotonDecoder()
    meter = RollingMeter(window_seconds=10.0)

    def mapper(message, packet):
        if message.event_code is None:
            return None
        return CombatEvent(packet.timestamp, 1, 2, 100, "damage")

    snapshots = list(
        replay_snapshots(path, decoder, meter, event_mapper=mapper, snapshot_interval=0.0)
    )

    assert snapshots
    last = snapshots[-1]
    assert last.totals[1]["damage"] == 100.0
    assert abs(last.totals[1]["dps"] - 10.0) < 1e-6
