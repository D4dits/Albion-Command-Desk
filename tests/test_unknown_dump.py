from __future__ import annotations

import logging

from albion_dps.models import RawPacket
from albion_dps.protocol.unknown_dump import dump_unknown
from tests.support_temp import mk_test_dir


def test_unknown_dump_writes_payload_and_logs(caplog) -> None:
    tmp_path = mk_test_dir("unknown_dump")
    packet = RawPacket(1234.567, "1.2.3.4", 1111, "5.6.7.8", 2222, b"\x10\x20")
    output_dir = tmp_path / "artifacts" / "unknown"

    caplog.set_level(logging.DEBUG)
    path = dump_unknown(packet, reason="unparsed", output_dir=output_dir)

    assert path.exists()
    assert path.read_bytes() == packet.payload
    assert path.parent == output_dir
    assert path.name.startswith(f"{int(packet.timestamp * 1000)}_")
    assert path.name.endswith(".bin")

    message = " ".join(record.getMessage() for record in caplog.records)
    assert "Unknown payload saved" in message
    assert "src=1.2.3.4:1111" in message
    assert "dst=5.6.7.8:2222" in message
    assert "len=2" in message
    assert "reason=unparsed" in message
