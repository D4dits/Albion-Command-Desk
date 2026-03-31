from __future__ import annotations

from pcap_fixtures import resolve_pcap

import pytest

from albion_dps.domain import NameRegistry, PartyRegistry
from albion_dps.domain.session_activity import MapTrailTracker
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.pipeline import replay_snapshots
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry


def test_pcap49_bootstraps_party_context_across_map_change() -> None:
    pcap_path = resolve_pcap("albion_combat_49_party_fight_all.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)
    names = NameRegistry()
    party = PartyRegistry()
    activity = MapTrailTracker()
    meter = SessionMeter(mode="battle", history_limit=50, name_lookup=names.lookup)

    labels: set[str] = set()

    for _snap in replay_snapshots(
        pcap_path,
        decoder,
        meter,
        name_registry=names,
        party_registry=party,
        activity_tracker=activity,
        event_mapper=mapper.map,
        snapshot_interval=0.0,
    ):
        history = meter.history(limit=20)
        labels = {entry.label for summary in history for entry in summary.entries}
        if (
            len(activity.events()) >= 2
            and any(event.detail == "Map changed" for event in activity.events())
            and (party.snapshot_ids() or party.snapshot_names())
            and labels
        ):
            break

    assert any(event.detail == "Map changed" for event in activity.events())
    assert party.snapshot_ids() or party.snapshot_names()
    assert labels
    assert not any(label.startswith("@MOB_") for label in labels)

