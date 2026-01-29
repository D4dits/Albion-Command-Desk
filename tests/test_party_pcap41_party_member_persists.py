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


def test_pcap41_party_members_persist() -> None:
    pcap_path = resolve_pcap("albion_combat_41_party_withsocialfur.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)
    names = NameRegistry()
    party = PartyRegistry()
    meter = SessionMeter(mode="battle", history_limit=20, name_lookup=names.lookup)

    for _snap in replay_snapshots(
        pcap_path,
        decoder,
        meter,
        name_registry=names,
        party_registry=party,
        event_mapper=mapper.map,
        snapshot_interval=0.0,
    ):
        pass

    history = meter.history(limit=10)
    assert history
    for summary in history:
        labels = {entry.label for entry in summary.entries}
        assert "D4dits" in labels
        assert "SocialFur3" in labels
