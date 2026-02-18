from __future__ import annotations

from pathlib import Path
from pcap_fixtures import resolve_pcap

import pytest

from albion_dps.domain import FameTracker, NameRegistry, PartyRegistry
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.pipeline import replay_snapshots
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry


def test_pcap26_zone_mode_does_not_flip_between_5055_and_5056() -> None:
    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)
    names = NameRegistry()
    party = PartyRegistry()
    fame = FameTracker()
    meter = SessionMeter(mode="zone", history_limit=50, name_lookup=names.lookup)
    pcap_path = resolve_pcap("albion_combat_26_walka_bzm_dluga.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    for _snap in replay_snapshots(
        pcap_path,
        decoder,
        meter,
        name_registry=names,
        party_registry=party,
        fame_tracker=fame,
        event_mapper=mapper.map,
        snapshot_interval=0.0,
    ):
        pass

    history = meter.history(limit=None)
    assert history
    assert len(history) <= 3

    labels = [summary.label or "" for summary in history]
    assert not any(label.endswith(":5055") for label in labels)
    assert not any(label.endswith(":5056") for label in labels)

    non_empty_labels = [label for label in labels if label]
    assert non_empty_labels
    # Zone mode should remain stable and not flap between multiple zone identifiers.
    assert len(set(non_empty_labels)) == 1
