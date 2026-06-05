from __future__ import annotations

from pathlib import Path

import pytest

from albion_dps.capture.replay_pcap import replay_pcap
from albion_dps.domain import LootTracker, NameRegistry, PartyRegistry
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.pipeline import _allow_event
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry
from albion_dps.qt.models import _build_player_rows
from albion_dps.qt.runner import _allowed_display_names_for_snapshot


def test_rz_chects_keeps_party_before_self_is_confirmed() -> None:
    pcap_path = Path("rz_chects.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    names = NameRegistry()
    party = PartyRegistry()
    loot = LootTracker(party_registry=party, include_silver=True)
    meter = SessionMeter(mode="battle", history_limit=100, name_lookup=names.lookup)
    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)

    false_self_names: list[str] = []
    allowed_names_seen: set[str] = set()

    for packet in replay_pcap(pcap_path):
        party.observe_packet(packet)
        messages = decoder.decode_all(packet)
        for message in messages:
            names.observe(message, packet)
            party.observe(message, packet)
            party.sync_guids(names)
            party.sync_names(names, timestamp=packet.timestamp)
            party.infer_self_name_from_targets(names)
            party.try_resolve_self_id(names)
            party.sync_self_name(names)
            party.sync_id_names(names)
            loot.observe(message, packet)
            meter.observe_message(message, packet)
        if party.self_name() not in (None, "D4dits"):
            false_self_names.append(str(party.self_name()))
        for message in messages:
            event = mapper.map(message, packet)
            if event is None:
                continue
            for item in (event if isinstance(event, list) else [event]):
                if party.strict and not party.has_ids():
                    party.observe_combat_event(item, names)
                    party.try_resolve_self_id(names)
                name = names.lookup(item.source_id)
                if _allow_event(item, party, names):
                    if name:
                        allowed_names_seen.add(name)
                    meter.push(item)
        party.sync_names(names, timestamp=packet.timestamp)

    assert false_self_names == []
    assert party.self_name() == "D4dits"
    assert names.lookup(next(iter(party.snapshot_self_ids()))) == "D4dits"
    assert {"D4dits", "FiressnakeTH", "AthenaLarc", "PalacinkaNutela"}.issubset(
        party.snapshot_names()
    )
    assert {"AthenaLarc", "FiressnakeTH", "PalacinkaNutela"}.issubset(
        allowed_names_seen
    )

    loot_events = loot.events(limit=5000)
    assert len(loot_events) >= 100
    assert {"D4dits", "FiressnakeTH", "Lozetobg"}.issubset(
        {event.looted_by.player_name for event in loot_events}
    )

    snapshot = meter.snapshot()
    allowed_display_names = _allowed_display_names_for_snapshot(
        snapshot=snapshot,
        names=names.snapshot(),
        party=party,
        name_registry=names,
    )
    rows = _build_player_rows(
        snapshot.totals,
        names=names.snapshot(),
        sort_key="dps",
        top_n=80,
        allowed_player_names=allowed_display_names or None,
    )
    row_names = {row.name for row in rows}
    assert {"D4dits", "FiressnakeTH", "PalacinkaNutela"}.issubset(row_names)
