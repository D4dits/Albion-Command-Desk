from albion_dps.models import CombatEvent, MeterSnapshot, PhotonMessage, RawPacket


def test_sanity_models() -> None:
    packet = RawPacket(0.0, "127.0.0.1", 1, "127.0.0.1", 2, b"")
    message = PhotonMessage(1, None, b"")
    event = CombatEvent(0.0, 10, 11, 50, "damage")
    snapshot = MeterSnapshot(0.0, {10: {"damage": 50.0, "heal": 0.0}})

    assert packet.payload == b""
    assert message.opcode == 1
    assert event.kind == "damage"
    assert snapshot.totals[10]["damage"] == 50.0
