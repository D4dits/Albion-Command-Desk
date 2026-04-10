from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Property, Qt, Signal

from albion_dps.domain.loot_export import loot_events_to_txt
from albion_dps.domain.loot_types import LootEvent


@dataclass(frozen=True)
class LootRow:
    timestamp_text: str
    looted_by_name: str
    looted_by_guild: str
    looted_by_alliance: str
    item_id: str
    item_name: str
    quantity: int
    source_name: str
    source_kind: str
    is_silver: bool
    summary: str


class LootEventsModel(QAbstractListModel):
    TimestampRole = Qt.UserRole + 1
    LootedByNameRole = Qt.UserRole + 2
    LootedByGuildRole = Qt.UserRole + 3
    LootedByAllianceRole = Qt.UserRole + 4
    ItemIdRole = Qt.UserRole + 5
    ItemNameRole = Qt.UserRole + 6
    QuantityRole = Qt.UserRole + 7
    SourceNameRole = Qt.UserRole + 8
    SourceKindRole = Qt.UserRole + 9
    IsSilverRole = Qt.UserRole + 10
    SummaryRole = Qt.UserRole + 11

    def __init__(self) -> None:
        super().__init__()
        self._items: list[LootRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.TimestampRole:
            return item.timestamp_text
        if role == self.LootedByNameRole:
            return item.looted_by_name
        if role == self.LootedByGuildRole:
            return item.looted_by_guild
        if role == self.LootedByAllianceRole:
            return item.looted_by_alliance
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemNameRole:
            return item.item_name
        if role == self.QuantityRole:
            return item.quantity
        if role == self.SourceNameRole:
            return item.source_name
        if role == self.SourceKindRole:
            return item.source_kind
        if role == self.IsSilverRole:
            return item.is_silver
        if role == self.SummaryRole:
            return item.summary
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.TimestampRole: b"timestampText",
            self.LootedByNameRole: b"lootedByName",
            self.LootedByGuildRole: b"lootedByGuild",
            self.LootedByAllianceRole: b"lootedByAlliance",
            self.ItemIdRole: b"itemId",
            self.ItemNameRole: b"itemName",
            self.QuantityRole: b"quantity",
            self.SourceNameRole: b"sourceName",
            self.SourceKindRole: b"sourceKind",
            self.IsSilverRole: b"isSilver",
            self.SummaryRole: b"summary",
        }

    def set_items(self, items: list[LootRow]) -> None:
        if items == self._items:
            return
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()


class LootState(QObject):
    changed = Signal()

    def __init__(self, *, history_limit: int = 200) -> None:
        super().__init__()
        self._history_limit = max(1, int(history_limit))
        self._events_model = LootEventsModel()
        self._event_count = 0
        self._latest_summary = ""
        self._export_text = loot_events_to_txt([])
        self._log_path = ""

    @Property(QObject, constant=True)
    def eventsModel(self) -> LootEventsModel:
        return self._events_model

    @Property(int, notify=changed)
    def eventCount(self) -> int:
        return self._event_count

    @Property(str, notify=changed)
    def latestLootSummary(self) -> str:
        return self._latest_summary

    @Property(str, notify=changed)
    def exportText(self) -> str:
        return self._export_text

    @Property(str, notify=changed)
    def logPath(self) -> str:
        return self._log_path

    def set_log_path(self, value: str) -> None:
        next_value = str(value or "")
        if next_value == self._log_path:
            return
        self._log_path = next_value
        self.changed.emit()

    def update_from_tracker(self, tracker) -> None:
        events = list(tracker.events(limit=self._history_limit))
        rows = [_loot_event_to_row(event) for event in events]
        export_text = loot_events_to_txt(list(reversed(events)))
        latest_summary = rows[0].summary if rows else ""
        changed = (
            self._event_count != len(rows)
            or self._latest_summary != latest_summary
            or self._export_text != export_text
        )
        self._events_model.set_items(rows)
        self._event_count = len(rows)
        self._latest_summary = latest_summary
        self._export_text = export_text
        if changed:
            self.changed.emit()


def _loot_event_to_row(event: LootEvent) -> LootRow:
    item_name = ""
    item_id = ""
    if event.item is not None:
        item_name = event.item.display_name
        item_id = event.item.unique_name or ""
    source_name = event.source_name or ""
    if event.looted_from is not None:
        source_name = event.looted_from.player_name
    return LootRow(
        timestamp_text=_format_timestamp(event.timestamp),
        looted_by_name=event.looted_by.player_name,
        looted_by_guild=event.looted_by.guild_name or "",
        looted_by_alliance=event.looted_by.alliance_name or "",
        item_id=item_id,
        item_name=item_name,
        quantity=int(event.quantity),
        source_name=source_name,
        source_kind=event.source_kind,
        is_silver=bool(event.is_silver),
        summary=_format_summary(event, item_name=item_name, source_name=source_name),
    )


def _format_timestamp(timestamp: float) -> str:
    total_seconds = max(0, int(timestamp))
    hours = (total_seconds // 3600) % 24
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _format_summary(event: LootEvent, *, item_name: str, source_name: str) -> str:
    item_label = item_name or "Unknown item"
    source_label = source_name or "unknown source"
    return (
        f"{event.looted_by.player_name} looted {int(event.quantity)}x "
        f"{item_label} from {source_label}"
    )
