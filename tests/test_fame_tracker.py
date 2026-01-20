from __future__ import annotations

from albion_dps.domain.fame_tracker import FameTracker
from albion_dps.models import PhotonMessage, RawPacket


_UPDATE_FAME_ONE_HEX = (
    "01000700690000e3d8016c00000528380be7bb02690011b980036900096640"
    "056f0106663dccccd0fc6b0052"
)
_UPDATE_FAME_TWO_HEX = (
    "01000700690000e3d8016c00000528381da13b02690011b980036900096640"
    "056f0106663dccccd0fc6b0052"
)


def _packet(timestamp: float) -> RawPacket:
    return RawPacket(
        timestamp=timestamp,
        src_ip="193.169.238.126",
        src_port=5056,
        dst_ip="10.0.0.1",
        dst_port=12345,
        payload=b"",
    )


def _message(hex_payload: str) -> PhotonMessage:
    return PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(hex_payload),
    )


def test_fame_tracker_counts_update_fame() -> None:
    tracker = FameTracker()

    tracker.observe(_message(_UPDATE_FAME_ONE_HEX), _packet(100.0))
    assert tracker.total() == 174

    tracker.observe(_message(_UPDATE_FAME_TWO_HEX), _packet(110.0))
    assert tracker.total() == 348
    assert tracker.per_hour() > 0.0

    tracker.observe(_message(_UPDATE_FAME_TWO_HEX), _packet(111.0))
    assert tracker.total() == 348

    tracker.reset()
    assert tracker.total() == 0
