from __future__ import annotations

from functools import lru_cache

from pcap_fixtures import resolve_pcap

import pytest

from albion_dps.capture.replay_pcap import replay_pcap
from albion_dps.domain import LootTracker, NameRegistry, PartyRegistry, load_item_resolver
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry


@lru_cache(maxsize=None)
def _pcap_loot_summary(name: str) -> dict[str, object]:
    pcap_path = resolve_pcap(name)
    if not pcap_path.exists():
        pytest.skip(f"Missing PCAP fixture: {pcap_path}")

    decoder = PhotonDecoder(registry=default_registry())
    names = NameRegistry()
    party = PartyRegistry()
    tracker = LootTracker(
        item_resolver=load_item_resolver(),
        party_registry=party,
        include_silver=False,
        history_limit=5000,
    )

    for packet in replay_pcap(pcap_path):
        party.observe_packet(packet)
        messages = decoder.decode_all(packet)
        for message in messages:
            names.observe(message, packet)
            party.observe(message, packet)
            party.sync_guids(names)
            party.sync_names(names)
            party.infer_self_name_from_targets(names)
            party.try_resolve_self_id(names)
            party.sync_self_name(names)
            party.sync_id_names(names)
            tracker.observe(message, packet)

    events = tracker.events(limit=5000)
    item_events = [event for event in events if not event.is_silver]
    return {
        "total": len(events),
        "items": len(item_events),
        "looters": len({event.looted_by.player_name for event in events}),
        "item_names": {
            event.item.display_name
            for event in item_events
            if event.item is not None and event.item.display_name
        },
    }


@pytest.mark.parametrize(
    ("pcap_name", "expected_items"),
    [
        ("albion_combat_48_party_fight.pcap", 0),
        ("albion_combat_49_party_fight_all.pcap", 2),
        ("albion_combat_51_party.pcap", 0),
        ("albion_combat_52_party_full.pcap", 1),
        ("albion_combat_54_group_camps.pcap", 2),
        ("albion_combat_55_group_camps.pcap", 3),
        ("albion_combat_56_nowy.pcap", 1),
    ],
)
def test_loot_pcaps_match_expected_item_counts(
    pcap_name: str,
    expected_items: int,
) -> None:
    summary = _pcap_loot_summary(pcap_name)

    assert summary["total"] == expected_items
    assert summary["items"] == expected_items


def test_loot_pcap49_keeps_expected_item_drops_without_silver_noise() -> None:
    summary = _pcap_loot_summary("albion_combat_49_party_fight_all.pcap")

    assert summary["total"] == 2
    assert summary["item_names"] == {"Adept's Assassin Jacket", "Master's Rune"}


def test_loot_pcaps_keep_expected_item_samples() -> None:
    summary52 = _pcap_loot_summary("albion_combat_52_party_full.pcap")
    summary54 = _pcap_loot_summary("albion_combat_54_group_camps.pcap")
    summary55 = _pcap_loot_summary("albion_combat_55_group_camps.pcap")
    summary56 = _pcap_loot_summary("albion_combat_56_nowy.pcap")

    assert summary52["item_names"] == {"Adept's Rune"}
    assert summary54["item_names"] == {"Rotten Chocolate Egg", "Chocolate"}
    assert summary55["item_names"] == {"Chocolate"}
    assert summary56["item_names"] == {"Rotten Chocolate Egg"}
