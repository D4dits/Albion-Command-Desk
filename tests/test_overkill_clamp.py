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


def test_overkill_is_clamped_using_subtype7_health_values() -> None:
    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)
    names = NameRegistry()
    party = PartyRegistry()
    fame = FameTracker()
    meter = SessionMeter(mode="battle", history_limit=20, name_lookup=names.lookup)
    pcap_path = resolve_pcap(
        "albion_combat_23_walka_3_przeciwnik_portal.pcap"
    )
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    list(
        replay_snapshots(
            pcap_path,
            decoder,
            meter,
            name_registry=names,
            party_registry=party,
            fame_tracker=fame,
            event_mapper=mapper.map,
            snapshot_interval=0.0,
        )
    )

    history = meter.history(limit=1)
    assert history, "expected at least one battle session"
    assert history[0].total_damage == 1143.0
