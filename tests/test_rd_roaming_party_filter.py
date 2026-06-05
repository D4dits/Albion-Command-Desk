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


def test_rd_roaming_does_not_show_nearby_looters_before_party_resolves() -> None:
    pcap_path = Path("rd__roaming.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    names = NameRegistry()
    party = PartyRegistry()
    loot = LootTracker(party_registry=party, include_silver=True)
    meter = SessionMeter(mode="battle", history_limit=100, name_lookup=names.lookup)
    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)

    rows_before_self: list[str] = []
    rows_after_roster: set[str] = set()

    for packet_count, packet in enumerate(replay_pcap(pcap_path), start=1):
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
        for message in messages:
            event = mapper.map(message, packet)
            if event is None:
                continue
            for item in (event if isinstance(event, list) else [event]):
                if party.strict and not party.has_ids():
                    party.observe_combat_event(item, names)
                    party.try_resolve_self_id(names)
                if _allow_event(item, party, names):
                    meter.push(item)
        party.sync_names(names, timestamp=packet.timestamp)

        if packet_count == 10_000:
            snapshot = meter.snapshot()
            allowed_names = _allowed_display_names_for_snapshot(
                snapshot=snapshot,
                names=names.snapshot(),
                party=party,
                name_registry=names,
            )
            rows_before_self = [
                row.name
                for row in _build_player_rows(
                    snapshot.totals,
                    names=names.snapshot(),
                    sort_key="dps",
                    top_n=30,
                    allowed_player_names=allowed_names,
                )
            ]
        if packet_count == 100_000:
            snapshot = meter.snapshot()
            allowed_names = _allowed_display_names_for_snapshot(
                snapshot=snapshot,
                names=names.snapshot(),
                party=party,
                name_registry=names,
            )
            rows_after_roster = {
                row.name
                for row in _build_player_rows(
                    snapshot.totals,
                    names=names.snapshot(),
                    sort_key="dps",
                    top_n=30,
                    allowed_player_names=allowed_names,
                )
            }
            break

    assert rows_before_self == []
    assert party.self_name() == "D4dits"
    assert "D4dits" in rows_after_roster
    assert "Selling opium" not in party.snapshot_names()
    assert "The Highlanders Tavern" not in party.snapshot_names()
    assert not any(" " in name for name in party.snapshot_names())
