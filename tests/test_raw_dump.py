from __future__ import annotations

from albion_dps.capture.raw_dump import dump_raw
from albion_dps.models import RawPacket


def test_dump_raw_writes_payload(tmp_path) -> None:
    packet = RawPacket(12.345, "1.1.1.1", 1111, "2.2.2.2", 2222, b"\x01\x02")
    output_dir = tmp_path / "raw"

    path = dump_raw(packet, output_dir=output_dir)

    assert path.exists()
    assert path.read_bytes() == packet.payload
    assert path.parent == output_dir
