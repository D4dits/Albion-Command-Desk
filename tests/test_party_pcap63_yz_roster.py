from __future__ import annotations

import pytest

from pcap_fixtures import resolve_pcap

from albion_dps.domain import NameRegistry, PartyRegistry
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.pipeline import replay_snapshots
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry


def test_pcap63_role_flag_does_not_add_non_party_healer() -> None:
    pcap_path = resolve_pcap("albion_combat_63_full_yz.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    names = NameRegistry()
    party = PartyRegistry()
    meter = SessionMeter(mode="battle", history_limit=50, name_lookup=names.lookup)

    for _snap in replay_snapshots(
        pcap_path,
        PhotonDecoder(registry=default_registry()),
        meter,
        name_registry=names,
        party_registry=party,
        event_mapper=CombatEventMapper().map,
        snapshot_interval=30.0,
    ):
        pass

    assert "emosterim" not in party.snapshot_names()
    for summary in meter.history(limit=50):
        assert all(entry.label != "emosterim" for entry in summary.entries)
