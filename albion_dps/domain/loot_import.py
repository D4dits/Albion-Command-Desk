from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from albion_dps.domain.loot_types import LootEvent, LootItemRef, LootPlayer


def read_loot_events_txt(path: str | Path) -> list[LootEvent]:
    target = Path(path).expanduser().resolve()
    payload = target.read_text(encoding="utf-8")
    return loot_events_from_txt(payload)


def loot_events_from_txt(payload: str) -> list[LootEvent]:
    reader = csv.DictReader(payload.splitlines(), delimiter=";")
    events: list[LootEvent] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        timestamp = _parse_timestamp(row.get("timestamp_utc", ""))
        looted_by_name = str(row.get("looted_by__name", "") or "").strip()
        if not looted_by_name:
            continue
        item_id = str(row.get("item_id", "") or "").strip()
        item_name = str(row.get("item_name", "") or "").strip()
        quantity = _parse_int(row.get("quantity", 0))
        if quantity <= 0:
            continue

        looted_from_name = str(row.get("looted_from__name", "") or "").strip()
        is_silver = item_id == "SILVER" or item_name.lower() == "silver"
        source_kind = str(row.get("source_kind", "") or "").strip().lower()
        if source_kind not in {"player", "mob", "system", "unknown", "silver"}:
            source_kind = _infer_source_kind(looted_from_name, is_silver=is_silver)
        looted_from = None
        if looted_from_name and source_kind == "player":
            looted_from = LootPlayer(
                player_name=looted_from_name,
                guild_name=str(row.get("looted_from__guild", "") or "").strip() or None,
                alliance_name=str(row.get("looted_from__alliance", "") or "").strip() or None,
            )

        item = None
        if item_id or item_name:
            item = LootItemRef(
                item_num_id=None,
                unique_name=item_id or None,
                display_name=item_name or item_id or "Unknown item",
                quality=_parse_optional_quality(row.get("quality", "")),
            )

        events.append(
            LootEvent(
                timestamp=timestamp,
                looted_by=LootPlayer(
                    player_name=looted_by_name,
                    guild_name=str(row.get("looted_by__guild", "") or "").strip() or None,
                    alliance_name=str(row.get("looted_by__alliance", "") or "").strip() or None,
                ),
                looted_from=looted_from,
                source_name=looted_from_name or None,
                source_kind=source_kind,
                item=item,
                quantity=quantity,
                is_silver=is_silver,
                raw_event_code=0,
                raw_subtype=0,
                event_id=str(row.get("event_id", "") or "").strip(),
                eligibility_reason=str(
                    row.get("eligibility_reason", "imported") or "imported"
                ).strip(),
            )
        )
    return list(reversed(events))


def _parse_timestamp(value: str) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
    except ValueError:
        return 0.0


def _parse_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_optional_quality(value) -> int | None:
    quality = _parse_int(value)
    if 1 <= quality <= 5:
        return quality
    return None


def _infer_source_kind(looted_from_name: str, *, is_silver: bool) -> str:
    if is_silver:
        return "silver"
    if looted_from_name.startswith("@MOB"):
        return "mob"
    if looted_from_name:
        return "player"
    return "system"
