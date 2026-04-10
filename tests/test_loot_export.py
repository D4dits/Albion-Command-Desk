from __future__ import annotations

from albion_dps.domain.loot_export import loot_events_to_txt, write_loot_events_txt
from albion_dps.domain.loot_types import LootEvent, LootItemRef, LootPlayer
from tests.support_temp import mk_test_dir


def test_loot_events_to_txt_matches_expected_header_and_rows() -> None:
    events = [
        LootEvent(
            timestamp=1.5,
            looted_by=LootPlayer(player_name="Alice", guild_name="Guild A", alliance_name="AAA"),
            looted_from=LootPlayer(player_name="Enemy", guild_name="Guild E", alliance_name="EEE"),
            source_name="Enemy",
            source_kind="player",
            item=LootItemRef(item_num_id=3130, unique_name="T3_BAG", display_name="Journeyman's Bag"),
            quantity=2,
            is_silver=False,
            raw_event_code=1,
            raw_subtype=275,
        ),
        LootEvent(
            timestamp=2.0,
            looted_by=LootPlayer(player_name="Bob"),
            looted_from=None,
            source_name="@MOB_KEEPER_DRUID_CHAMPION",
            source_kind="mob",
            item=LootItemRef(item_num_id=562, unique_name="T4_POTION", display_name="Adept's Potion"),
            quantity=1,
            is_silver=False,
            raw_event_code=1,
            raw_subtype=275,
        ),
    ]

    payload = loot_events_to_txt(events)

    assert payload.startswith(
        "timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name;item_id;item_name;quantity;looted_from__alliance;looted_from__guild;looted_from__name\n"
    )
    assert "1970-01-01T00:00:01.500Z;AAA;Guild A;Alice;T3_BAG;Journeyman's Bag;2;EEE;Guild E;Enemy\n" in payload
    assert "1970-01-01T00:00:02.000Z;;;Bob;T4_POTION;Adept's Potion;1;;;@MOB_KEEPER_DRUID_CHAMPION\n" in payload

    tmp_path = mk_test_dir("loot_export")
    export_path = tmp_path / "loot-events.txt"
    write_loot_events_txt(export_path, events)
    assert export_path.read_text(encoding="utf-8") == payload
