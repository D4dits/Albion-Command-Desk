from __future__ import annotations

from pathlib import Path
from pcap_fixtures import resolve_pcap

import pytest

from albion_dps.domain import NameRegistry, PartyRegistry
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.pipeline import replay_snapshots
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry


def test_pcap27_does_not_include_non_party_sources() -> None:
    pcap_path = resolve_pcap("albion_combat_27_party.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)
    names = NameRegistry()
    party = PartyRegistry()
    meter = SessionMeter(mode="battle", history_limit=20, name_lookup=names.lookup)

    last_snapshot = None
    for snap in replay_snapshots(
        pcap_path,
        decoder,
        meter,
        name_registry=names,
        party_registry=party,
        event_mapper=mapper.map,
        snapshot_interval=0.0,
    ):
        last_snapshot = snap

    assert last_snapshot is not None

    history = meter.history(limit=10)
    assert history, "expected at least one battle session"
    labels = {entry.label for summary in history for entry in summary.entries}
    if party._self_name:
        assert all(label == party._self_name or label.isdigit() for label in labels)
    else:
        assert all(label.isdigit() for label in labels)
    numeric_labels = {label for label in labels if label.isdigit()}
    assert len(numeric_labels) <= 1
