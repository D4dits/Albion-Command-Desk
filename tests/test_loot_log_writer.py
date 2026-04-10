from __future__ import annotations

from datetime import datetime

from albion_dps.domain.loot_log_writer import LootLogWriter
from albion_dps.domain.loot_types import LootEvent, LootItemRef, LootPlayer
from tests.support_temp import mk_test_dir


def test_loot_log_writer_creates_session_file_and_syncs_payload() -> None:
    tmp_dir = mk_test_dir("loot_log_writer")
    writer = LootLogWriter(
        output_dir=tmp_dir,
        session_started_at=datetime(2026, 4, 10, 12, 34, 56),
    )
    events = [
        LootEvent(
            timestamp=1.5,
            looted_by=LootPlayer(player_name="Alice"),
            looted_from=LootPlayer(player_name="Enemy"),
            source_name="Enemy",
            source_kind="player",
            item=LootItemRef(item_num_id=3130, unique_name="T3_BAG", display_name="Journeyman's Bag"),
            quantity=2,
            is_silver=False,
            raw_event_code=1,
            raw_subtype=275,
        )
    ]

    path = writer.sync_events(events)

    assert path.name == "loot-events-2026-04-10-12-34-56.txt"
    payload = path.read_text(encoding="utf-8")
    assert "timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name" in payload
    assert "Journeyman's Bag" in payload

    second_path = writer.sync_events(events)
    assert second_path == path
