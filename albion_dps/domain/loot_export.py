from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from pathlib import Path

from albion_dps.domain.loot_types import LootEvent

LOOT_EXPORT_HEADER = [
    "timestamp_utc",
    "looted_by__alliance",
    "looted_by__guild",
    "looted_by__name",
    "item_id",
    "item_name",
    "quantity",
    "looted_from__alliance",
    "looted_from__guild",
    "looted_from__name",
    "source_kind",
]


def loot_events_to_txt(events: list[LootEvent]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\n")
    writer.writerow(LOOT_EXPORT_HEADER)
    for event in events:
        writer.writerow(_loot_event_to_row(event))
    return buf.getvalue()


def write_loot_events_txt(path: str | Path, events: list[LootEvent]) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(loot_events_to_txt(events), encoding="utf-8")
    return target


def _loot_event_to_row(event: LootEvent) -> list[str]:
    looted_from_alliance = ""
    looted_from_guild = ""
    looted_from_name = ""
    if event.looted_from is not None:
        looted_from_alliance = event.looted_from.alliance_name or ""
        looted_from_guild = event.looted_from.guild_name or ""
        looted_from_name = event.looted_from.player_name
    elif event.source_name:
        looted_from_name = event.source_name

    item_id = ""
    item_name = ""
    if event.item is not None:
        item_id = event.item.unique_name or ""
        item_name = event.item.display_name

    return [
        _timestamp_to_iso8601_utc(event.timestamp),
        event.looted_by.alliance_name or "",
        event.looted_by.guild_name or "",
        event.looted_by.player_name,
        item_id,
        item_name,
        str(int(event.quantity)),
        looted_from_alliance,
        looted_from_guild,
        looted_from_name,
        event.source_kind,
    ]


def _timestamp_to_iso8601_utc(timestamp: float) -> str:
    dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
