from __future__ import annotations

from albion_dps.domain import NameRegistry, PartyRegistry
from albion_dps.models import MeterSnapshot, PhotonMessage, RawPacket
from albion_dps.qt.runner import _allowed_display_names_for_snapshot


_PORTAL_PAYLOAD_HEX = (
    "01002800690001d56b017300096b726f7869676f727a026212057800000005050006030306780000000500040900060778000000108848c929e0b8a54286bfe811e08fda800a7300000b69000000000c69000000000d73000010780000000810c76e0afdecaff911780000000810c76e0afdecaff91269004ac42a136643327bfa14664147c28f1666452eb0001766452eb0001966428bc0b31a69004ac42a1b6643cd80001c6643cd80001e6640ae1f391f69004ac42a2066447b80002166447b800023664120f5c32469004ac42a2566465b71b1266c08de49f4e80ccf8f2762002879000a6b18ed000011230fc2123c0b3c09cc0bde000000002b79000e6b0aff0b090b1f0ea40ee10f1affffffffffffffffffffffff104e100d33730000356203366200377900076bffffffffffffffffffffffff013938620339620c3f6900000000fc6b001d"
)


def test_allowed_display_names_keeps_bootstrap_name_fallback_before_party_ids() -> None:
    party = PartyRegistry()
    party.seed_self_ids([100])
    party.seed_names(["D4dits", "SocialFur3"])
    snapshot = MeterSnapshot(timestamp=10.0, totals={}, names={100: "D4dits"})

    allowed = _allowed_display_names_for_snapshot(
        snapshot=snapshot,
        names=snapshot.names or {},
        party=party,
        name_registry=None,
    )

    assert allowed == {"D4dits", "SocialFur3"}


def test_allowed_display_names_filters_nonlocal_party_ids_after_resolution() -> None:
    party = PartyRegistry()
    party.seed_self_ids([100])
    party.seed_names(["D4dits", "SocialFur3"])
    party.seed_ids([200])
    names = NameRegistry()
    names.record(200, "SocialFur3")
    snapshot = MeterSnapshot(timestamp=50.0, totals={}, names={100: "D4dits", 200: "SocialFur3"})

    allowed = _allowed_display_names_for_snapshot(
        snapshot=snapshot,
        names=snapshot.names or {},
        party=party,
        name_registry=names,
    )

    assert allowed == {"D4dits"}


def test_allowed_display_names_keeps_self_id_label_when_name_unresolved() -> None:
    party = PartyRegistry()
    party.seed_self_ids([744616])
    snapshot = MeterSnapshot(timestamp=50.0, totals={744616: {"damage": 267.0}}, names={})

    allowed = _allowed_display_names_for_snapshot(
        snapshot=snapshot,
        names=snapshot.names or {},
        party=party,
        name_registry=None,
    )

    assert allowed == {"744616"}


def test_allowed_display_names_keeps_self_when_roster_is_unresolved_after_self_id() -> None:
    party = PartyRegistry()
    party.seed_self_ids([100])
    snapshot = MeterSnapshot(
        timestamp=50.0,
        totals={100: {"damage": 100.0}, 200: {"damage": 75.0}},
        names={100: "D4dits", 200: "PartyCandidate"},
    )

    allowed = _allowed_display_names_for_snapshot(
        snapshot=snapshot,
        names=snapshot.names or {},
        party=party,
        name_registry=None,
    )

    assert allowed == {"D4dits"}


def test_allowed_display_names_keeps_recently_local_party_member() -> None:
    party = PartyRegistry()
    party.seed_self_ids([100])
    party.seed_names(["D4dits", "kroxigorz"])
    party.seed_ids([120171])
    names = NameRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_PORTAL_PAYLOAD_HEX))
    packet = RawPacket(
        timestamp=42.0,
        src_ip="193.169.238.17",
        src_port=5056,
        dst_ip="10.0.0.1",
        dst_port=51000,
        payload=message.payload,
    )
    names.observe(message, packet)
    snapshot = MeterSnapshot(timestamp=50.0, totals={}, names={100: "D4dits", 120171: "kroxigorz"})

    allowed = _allowed_display_names_for_snapshot(
        snapshot=snapshot,
        names=snapshot.names or {},
        party=party,
        name_registry=names,
    )

    assert allowed == {"D4dits", "kroxigorz"}


def test_allowed_display_names_keeps_active_party_id_once_local_party_exists() -> None:
    party = PartyRegistry()
    party.seed_self_ids([100])
    party.seed_names(["D4dits", "SocialFur3", "SocialFur4"])
    party.seed_ids([200, 300])
    names = NameRegistry()
    names.record(100, "D4dits")
    names.record_local(200, "SocialFur3", 100.0)
    names.record(300, "SocialFur4")
    snapshot = MeterSnapshot(
        timestamp=105.0,
        totals={
            100: {"damage": 50.0},
            200: {"damage": 25.0},
            300: {"damage": 10.0},
        },
        names={100: "D4dits", 200: "SocialFur3", 300: "SocialFur4"},
    )

    allowed = _allowed_display_names_for_snapshot(
        snapshot=snapshot,
        names=snapshot.names or {},
        party=party,
        name_registry=names,
    )

    assert allowed == {"D4dits", "SocialFur3", "SocialFur4"}


def test_allowed_display_names_keeps_active_party_member_without_recent_local_event() -> None:
    party = PartyRegistry()
    party.seed_self_ids([100])
    party.seed_names(["D4dits", "SocialFur3", "SocialFur4"])
    party.seed_ids([200, 300])
    names = NameRegistry()
    names.record(100, "D4dits")
    names.record_local(200, "SocialFur3", 100.0)
    names.record(300, "SocialFur4")
    snapshot = MeterSnapshot(
        timestamp=105.0,
        totals={
            100: {"damage": 50.0},
            300: {"damage": 10.0},
        },
        names={100: "D4dits", 200: "SocialFur3", 300: "SocialFur4"},
    )

    allowed = _allowed_display_names_for_snapshot(
        snapshot=snapshot,
        names=snapshot.names or {},
        party=party,
        name_registry=names,
    )

    assert allowed == {"D4dits", "SocialFur3", "SocialFur4"}
