from __future__ import annotations

import json
from pathlib import Path
from pcap_fixtures import resolve_pcap

import pytest

from albion_dps.domain.name_registry import NameRegistry
from albion_dps.meter.aggregate import RollingMeter
from albion_dps.pipeline import replay_snapshots
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry


GOLDENS = [
    "albion_combat_8_walka_1_przeciwnik",
    "albion_combat_9_walka_2_przeciwnik",
    "albion_combat_10_walka_3_przeciwnik",
]


@pytest.mark.parametrize("name", GOLDENS)
def test_golden_outputs(name: str) -> None:
    golden_path = Path("tests/golden") / f"{name}.json"
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    pcap_path = resolve_pcap(name)
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    decoder = PhotonDecoder(registry=default_registry())
    meter = RollingMeter(window_seconds=10.0, session_timeout_seconds=None)
    mapper = CombatEventMapper()
    names = NameRegistry()

    snapshots = list(
        replay_snapshots(
            pcap_path,
            decoder,
            meter,
            name_registry=names,
            event_mapper=mapper.map,
            snapshot_interval=0.0,
        )
    )
    last = snapshots[-1]

    assert last.timestamp == pytest.approx(expected["timestamp"])

    expected_names = {int(key): value for key, value in expected["names"].items()}
    assert last.names == expected_names

    expected_totals = {int(key): value for key, value in expected["totals"].items()}
    assert set(last.totals.keys()) == set(expected_totals.keys())

    for source_id, stats in expected_totals.items():
        current = last.totals[source_id]
        assert current["damage"] == pytest.approx(stats["damage"])
        assert current["heal"] == pytest.approx(stats["heal"])
        assert current["dps"] == pytest.approx(stats["dps"])
