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
        ),
        LootEvent(
            timestamp=1.6,
            looted_by=LootPlayer(player_name="Alice"),
            looted_from=None,
            source_name=None,
            source_kind="silver",
            item=LootItemRef(item_num_id=None, unique_name="SILVER", display_name="Silver"),
            quantity=1500,
            is_silver=True,
            raw_event_code=1,
            raw_subtype=275,
        )
    ]

    path = writer.sync_events(events)

    assert path.name == "loot-events-2026-04-10-12-34-56.txt"
    payload = path.read_text(encoding="utf-8")
    assert "timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name" in payload
    assert "Journeyman's Bag" in payload
    assert "SILVER;Silver;1500" not in payload

    second_path = writer.sync_events(events)
    assert second_path == path


def test_loot_log_writer_prunes_old_files() -> None:
    tmp_dir = mk_test_dir("loot_log_writer_prune")
    events: list[LootEvent] = []

    first = LootLogWriter(
        output_dir=tmp_dir,
        session_started_at=datetime(2026, 4, 10, 12, 0, 0),
        keep_files=2,
    )
    second = LootLogWriter(
        output_dir=tmp_dir,
        session_started_at=datetime(2026, 4, 10, 12, 5, 0),
        keep_files=2,
    )
    third = LootLogWriter(
        output_dir=tmp_dir,
        session_started_at=datetime(2026, 4, 10, 12, 10, 0),
        keep_files=2,
    )

    first.sync_events(events)
    second.sync_events(events)
    third.sync_events(events)

    remaining = sorted(path.name for path in tmp_dir.glob("loot-events-*.txt"))
    assert remaining == [
        "loot-events-2026-04-10-12-05-00.txt",
        "loot-events-2026-04-10-12-10-00.txt",
    ]
