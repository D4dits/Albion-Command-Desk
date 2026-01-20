from __future__ import annotations

from albion_dps.models import PhotonMessage, RawPacket
from albion_dps.protocol.combat_mapper import CombatEventMapper


def _packet() -> RawPacket:
    return RawPacket(123.456, "1.1.1.1", 1111, "2.2.2.2", 2222, b"")


_NEGATIVE_PAYLOAD_HEX = (
    "010009006b58170169002000310266c329000003664495c000046201056202066b5809076b0d34fc6b0006"
)
_POSITIVE_PAYLOAD_HEX = (
    "010009006b580901690020228f026642280000036645141000046202056205066b5809076b0f43fc6b0006"
)
_LIST_PAYLOAD_HEX = (
    "010009006900013aff0179000269005976c8005977540279000266c2ec000041a8000003790002664500d0004502200004780000000202020578000000020303067900026900013a0300013aff077900026b0bd50eb6fc6b0007"
)


def test_combat_mapper_damage_event() -> None:
    mapper = CombatEventMapper()
    message = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_NEGATIVE_PAYLOAD_HEX),
    )
    event = mapper.map(message, _packet())

    assert event is not None
    assert event.kind == "damage"
    assert event.amount == 169
    assert event.source_id == 22537
    assert event.target_id == 22551


def test_combat_mapper_heal_event() -> None:
    mapper = CombatEventMapper()
    message = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_POSITIVE_PAYLOAD_HEX),
    )
    event = mapper.map(message, _packet())

    assert event is not None
    assert event.kind == "heal"
    assert event.amount == 42


def test_combat_mapper_list_event() -> None:
    mapper = CombatEventMapper()
    message = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_LIST_PAYLOAD_HEX),
    )
    event = mapper.map(message, _packet())

    assert isinstance(event, list)
    assert len(event) == 2
    assert {item.amount for item in event} == {118, 21}
    assert {item.kind for item in event} == {"damage", "heal"}
    assert {item.target_id for item in event} == {80639}
    assert {item.source_id for item in event} == {80387, 80639}
