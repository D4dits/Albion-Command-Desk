from __future__ import annotations

from albion_dps.domain.session_activity import MapTrailTracker
from albion_dps.models import PhotonMessage, RawPacket


def _packet(timestamp: float) -> RawPacket:
    return RawPacket(
        timestamp=timestamp,
        src_ip="193.169.238.126",
        src_port=5056,
        dst_ip="10.0.0.1",
        dst_port=12345,
        payload=b"",
    )


def test_map_trail_tracker_records_unique_transitions(monkeypatch) -> None:
    sequence = iter(["forest_map", "forest_map", "city_map"])
    monkeypatch.setattr(
        "albion_dps.domain.session_activity.extract_map_index",
        lambda message: next(sequence, None),
    )
    tracker = MapTrailTracker(map_lookup=lambda idx: {"forest_map": "Adren's Hill", "city_map": "Bridgewatch"}.get(idx))
    message = PhotonMessage(opcode=0, event_code=1, payload=b"")

    tracker.observe_message(message, _packet(100.0))
    tracker.observe_message(message, _packet(101.0))
    tracker.observe_message(message, _packet(140.0))

    events = tracker.events()
    assert [event.title for event in events] == ["Bridgewatch", "Adren's Hill"]
    assert events[0].detail == "Map changed"
    assert events[1].detail == "Map entered"
