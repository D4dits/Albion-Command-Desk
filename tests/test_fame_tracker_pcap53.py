from __future__ import annotations

from pcap_fixtures import resolve_pcap

import pytest

from albion_dps.capture.replay_pcap import replay_pcap
from albion_dps.domain.fame_tracker import FameTracker
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry


def test_pcap53_fame_and_silver_totals_match_observed_session() -> None:
    pcap_path = resolve_pcap("albion_combat_53_gold_fame.pcap")
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    decoder = PhotonDecoder(registry=default_registry())
    tracker = FameTracker()

    for packet in replay_pcap(pcap_path):
        for message in decoder.decode_all(packet):
            tracker.observe(message, packet)

    assert tracker.total() == 8794
    assert tracker.silver_total() == 1279
    assert tracker.per_hour() > 0.0
    assert tracker.silver_per_hour() > 0.0

