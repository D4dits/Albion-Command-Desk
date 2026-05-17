from __future__ import annotations

from pathlib import Path

import pytest

from albion_dps.domain import NameRegistry, PartyRegistry
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.pipeline import replay_snapshots
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry
from albion_dps.qt.models import _build_player_rows
from albion_dps.qt.runner import _allowed_display_names_for_snapshot


def test_group1_maps_party_members_before_their_first_damage() -> None:
    pcap_path = Path("group_1.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    names = NameRegistry()
    party = PartyRegistry()
    meter = SessionMeter(mode="battle", history_limit=20, name_lookup=names.lookup)
    decoder = PhotonDecoder(registry=default_registry())
    mapper = CombatEventMapper(clamp_overkill=True)

    cascade_seen_ts: float | None = None
    mertler_seen_ts: float | None = None
    row_names: set[str] = set()

    for snap in replay_snapshots(
        pcap_path,
        decoder,
        meter,
        name_registry=names,
        party_registry=party,
        event_mapper=mapper.map,
        snapshot_interval=0.0,
    ):
        ids = party.snapshot_ids()
        if cascade_seen_ts is None and 996330 in ids:
            cascade_seen_ts = snap.timestamp
        if mertler_seen_ts is None and 999092 in ids:
            mertler_seen_ts = snap.timestamp
        allowed_names = _allowed_display_names_for_snapshot(
            snapshot=snap,
            names=snap.names or {},
            party=party,
            name_registry=names,
        )
        rows = _build_player_rows(
            snap.totals,
            names=snap.names or {},
            sort_key="dps",
            top_n=20,
            allowed_player_names=allowed_names or None,
        )
        row_names.update(row.name for row in rows)

    assert not {"owner", "friend", "user"}.intersection(party.snapshot_names())
    assert cascade_seen_ts is not None
    assert mertler_seen_ts is not None
    assert cascade_seen_ts < 1779043402.653
    assert mertler_seen_ts < 1779043420.920
    assert {"D4dits", "CascadeJP", "MERTLER", "NaoD", "Smmmo"}.issubset(row_names)
