from __future__ import annotations

from pcap_fixtures import resolve_pcap

import pytest

from albion_dps.domain import NameRegistry, PartyRegistry
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.pipeline import replay_snapshots
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry
from albion_dps.qt.models import _build_player_rows
from albion_dps.qt.runner import _allowed_display_names_for_snapshot


def test_pcap50_live_view_keeps_rows_visible_during_party_bootstrap() -> None:
    pcap_path = resolve_pcap("albion_combat_50_party.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)
    names = NameRegistry()
    party = PartyRegistry()
    meter = SessionMeter(mode="battle", history_limit=20, name_lookup=names.lookup)

    saw_rows = False
    for snap in replay_snapshots(
        pcap_path,
        decoder,
        meter,
        name_registry=names,
        party_registry=party,
        event_mapper=mapper.map,
        snapshot_interval=0.0,
    ):
        if not snap.totals:
            continue
        label_filter = _allowed_display_names_for_snapshot(
            snapshot=snap,
            names=snap.names or {},
            party=party,
            name_registry=names,
        )
        rows = _build_player_rows(
            snap.totals,
            names=snap.names or {},
            sort_key="dps",
            top_n=10,
            allowed_player_names=label_filter or None,
        )
        if rows:
            saw_rows = True
            break

    assert saw_rows, "Party bootstrap regression hides all live rows"

