from __future__ import annotations

from albion_dps.domain.loot_import import loot_events_from_txt


def test_loot_import_parses_items_and_silver() -> None:
    payload = """timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name;item_id;item_name;quantity;looted_from__alliance;looted_from__guild;looted_from__name
1970-01-01T01:01:01.000Z;AAA;Guild A;Alice;T3_BAG;Journeyman's Bag;2;EEE;Guild E;Enemy
1970-01-01T01:01:02.000Z;;;Bob;SILVER;Silver;1500;;;
"""

    events = loot_events_from_txt(payload)

    assert len(events) == 2
    assert events[0].looted_by.player_name == "Bob"
    assert events[0].is_silver is True
    assert events[0].source_kind == "silver"
    assert events[1].looted_by.player_name == "Alice"
    assert events[1].is_silver is False
    assert events[1].source_kind == "player"
    assert events[1].looted_from is not None
    assert events[1].looted_from.player_name == "Enemy"


def test_loot_import_uses_source_kind_when_present() -> None:
    payload = """timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name;item_id;item_name;quantity;looted_from__alliance;looted_from__guild;looted_from__name;source_kind
1970-01-01T01:01:01.000Z;;;Alice;T4_SOUL;Adept's Soul;20;;;Loot Chest;system
"""

    events = loot_events_from_txt(payload)

    assert len(events) == 1
    assert events[0].source_kind == "system"
    assert events[0].source_name == "Loot Chest"
    assert events[0].looted_from is None
