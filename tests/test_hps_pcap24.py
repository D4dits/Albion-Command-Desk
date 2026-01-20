from __future__ import annotations

from pathlib import Path

import pytest

from albion_dps.domain import FameTracker, NameRegistry, PartyRegistry
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.pipeline import replay_snapshots
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry


def test_pcap24_includes_heal_and_hps_in_snapshots_and_history() -> None:
    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)
    names = NameRegistry()
    party = PartyRegistry()
    fame = FameTracker()
    meter = SessionMeter(mode="battle", history_limit=20, name_lookup=names.lookup)
    pcap_path = Path(
        "albion_dps/artifacts/pcaps/albion_combat_24_walka_3_przeciwnik_leczenie_portal.pcap"
    )
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    saw_heal_snapshot = False
    for snap in replay_snapshots(
        pcap_path,
        decoder,
        meter,
        name_registry=names,
        party_registry=party,
        fame_tracker=fame,
        event_mapper=mapper.map,
        snapshot_interval=0.0,
    ):
        for stats in snap.totals.values():
            if stats.get("heal", 0.0) > 0.0:
                assert stats.get("hps", 0.0) > 0.0
                saw_heal_snapshot = True

    history = meter.history(limit=50)
    assert any(summary.total_heal > 0.0 for summary in history)
    assert saw_heal_snapshot
