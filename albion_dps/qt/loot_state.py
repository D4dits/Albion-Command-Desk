from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication

from albion_dps.domain.loot_export import loot_events_to_txt
from albion_dps.domain.loot_import import read_loot_events_txt
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


@dataclass(frozen=True)
class LootAggregateRow:
    label: str
    sublabel: str
    quantity: int
    event_count: int


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


class LootAggregateModel(QAbstractListModel):
    LabelRole = Qt.UserRole + 1
    SublabelRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    EventCountRole = Qt.UserRole + 4

    def __init__(self) -> None:
        super().__init__()
        self._items: list[LootAggregateRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.LabelRole:
            return item.label
        if role == self.SublabelRole:
            return item.sublabel
        if role == self.QuantityRole:
            return item.quantity
        if role == self.EventCountRole:
            return item.event_count
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.LabelRole: b"label",
            self.SublabelRole: b"sublabel",
            self.QuantityRole: b"quantity",
            self.EventCountRole: b"eventCount",
        }

    def set_items(self, items: list[LootAggregateRow]) -> None:
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
        self._top_looters_model = LootAggregateModel()
        self._top_items_model = LootAggregateModel()
        self._top_silver_looters_model = LootAggregateModel()
        self._live_events: list[LootEvent] = []
        self._imported_events: list[LootEvent] | None = None
        self._all_events: list[LootEvent] = []
        self._search_query = ""
        self._source_filter = "all"
        self._kind_filter = "all"
        self._event_count = 0
        self._total_quantity = 0
        self._item_event_count = 0
        self._item_total_quantity = 0
        self._silver_event_count = 0
        self._silver_total_quantity = 0
        self._unique_looters = 0
        self._unique_items = 0
        self._latest_summary = ""
        self._export_text = loot_events_to_txt([])
        self._log_path = ""
        self._log_directory_url = ""
        self._imported_log_path = ""

    @Property(QObject, constant=True)
    def eventsModel(self) -> LootEventsModel:
        return self._events_model

    @Property(QObject, constant=True)
    def topLootersModel(self) -> LootAggregateModel:
        return self._top_looters_model

    @Property(QObject, constant=True)
    def topItemsModel(self) -> LootAggregateModel:
        return self._top_items_model

    @Property(QObject, constant=True)
    def topSilverLootersModel(self) -> LootAggregateModel:
        return self._top_silver_looters_model

    @Property(int, notify=changed)
    def eventCount(self) -> int:
        return self._event_count

    @Property(int, notify=changed)
    def totalQuantity(self) -> int:
        return self._total_quantity

    @Property(int, notify=changed)
    def itemEventCount(self) -> int:
        return self._item_event_count

    @Property(int, notify=changed)
    def itemTotalQuantity(self) -> int:
        return self._item_total_quantity

    @Property(int, notify=changed)
    def silverEventCount(self) -> int:
        return self._silver_event_count

    @Property(int, notify=changed)
    def silverTotalQuantity(self) -> int:
        return self._silver_total_quantity

    @Property(int, notify=changed)
    def uniqueLooters(self) -> int:
        return self._unique_looters

    @Property(int, notify=changed)
    def uniqueItems(self) -> int:
        return self._unique_items

    @Property(str, notify=changed)
    def latestLootSummary(self) -> str:
        return self._latest_summary

    @Property(str, notify=changed)
    def exportText(self) -> str:
        return self._export_text

    @Property(str, notify=changed)
    def logPath(self) -> str:
        return self._imported_log_path or self._log_path

    @Property(str, notify=changed)
    def logDirectoryUrl(self) -> str:
        if self._imported_log_path:
            try:
                return Path(self._imported_log_path).expanduser().resolve().parent.as_uri()
            except Exception:
                return ""
        return self._log_directory_url

    @Property(bool, notify=changed)
    def importedLogActive(self) -> bool:
        return bool(self._imported_log_path)

    @Property(str, notify=changed)
    def searchQuery(self) -> str:
        return self._search_query

    @Property(str, notify=changed)
    def sourceFilter(self) -> str:
        return self._source_filter

    @Property(str, notify=changed)
    def kindFilter(self) -> str:
        return self._kind_filter

    @Property("QVariantList", constant=True)
    def sourceFilterOptions(self) -> list[str]:
        return ["all", "player", "mob", "silver", "system"]

    @Property("QVariantList", constant=True)
    def kindFilterOptions(self) -> list[str]:
        return ["all", "items", "silver"]

    def set_log_path(self, value: str) -> None:
        next_value = str(value or "")
        next_dir_url = ""
        if next_value:
            try:
                next_dir_url = Path(next_value).expanduser().resolve().parent.as_uri()
            except Exception:
                next_dir_url = ""
        if next_value == self._log_path and next_dir_url == self._log_directory_url:
            return
        self._log_path = next_value
        self._log_directory_url = next_dir_url
        self.changed.emit()

    @Slot(str)
    def setSearchQuery(self, value: str) -> None:
        next_value = str(value or "").strip()
        if next_value == self._search_query:
            return
        self._search_query = next_value
        self._refresh_models()

    @Slot(str)
    def setSourceFilter(self, value: str) -> None:
        next_value = str(value or "all").strip().lower() or "all"
        if next_value not in {"all", "player", "mob", "silver", "system"}:
            next_value = "all"
        if next_value == self._source_filter:
            return
        self._source_filter = next_value
        self._refresh_models()

    @Slot(str)
    def setKindFilter(self, value: str) -> None:
        next_value = str(value or "all").strip().lower() or "all"
        if next_value not in {"all", "items", "silver"}:
            next_value = "all"
        if next_value == self._kind_filter:
            return
        self._kind_filter = next_value
        self._refresh_models()

    @Slot(result=bool)
    def copyLatestSummary(self) -> bool:
        if not self._latest_summary:
            return False
        return self._copy_to_clipboard(self._latest_summary)

    @Slot(result=bool)
    def copyCurrentView(self) -> bool:
        if not self._export_text:
            return False
        return self._copy_to_clipboard(self._export_text)

    @Slot(result=str)
    def exportCurrentViewInteractive(self) -> str:
        if not self._export_text:
            return ""
        path = self._prompt_export_path(
            label="Loot view",
            suggested_name="acd-loot-view.txt",
            file_filter="Text Files (*.txt);;All Files (*)",
        )
        if not path:
            return ""
        try:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self._export_text, encoding="utf-8")
        except Exception:
            return ""
        return str(target)

    @Slot(result=str)
    def importLogInteractive(self) -> str:
        path = self._prompt_import_path(
            label="Loot log",
            file_filter="Text Files (*.txt);;All Files (*)",
        )
        if not path:
            return ""
        try:
            imported = read_loot_events_txt(path)
        except Exception:
            return ""
        self._imported_events = imported
        self._imported_log_path = str(Path(path).expanduser().resolve())
        self._all_events = list(imported)
        self._refresh_models()
        return self._imported_log_path

    @Slot()
    def useLiveLog(self) -> None:
        if not self._imported_log_path:
            return
        self._imported_log_path = ""
        self._imported_events = None
        self._all_events = list(self._live_events)
        self._refresh_models()

    def update_from_tracker(self, tracker) -> None:
        self._live_events = list(tracker.events(limit=self._history_limit))
        if self._imported_events is not None:
            return
        self._all_events = list(self._live_events)
        self._refresh_models()

    def _refresh_models(self) -> None:
        base_events = _filter_events(
            self._all_events,
            search_query=self._search_query,
            source_filter=self._source_filter,
        )
        item_events = [event for event in base_events if not event.is_silver]
        silver_events = [event for event in base_events if event.is_silver]
        filtered_events = _filter_events_by_kind(base_events, kind_filter=self._kind_filter)
        rows = [_loot_event_to_row(event) for event in filtered_events]
        item_rows = [_loot_event_to_row(event) for event in item_events]
        silver_rows = [_loot_event_to_row(event) for event in silver_events]
        export_text = loot_events_to_txt(list(reversed(filtered_events)))
        latest_summary = rows[0].summary if rows else ""
        total_quantity = sum(row.quantity for row in rows)
        item_total_quantity = sum(row.quantity for row in item_rows)
        silver_total_quantity = sum(row.quantity for row in silver_rows)
        unique_looters = len({row.looted_by_name for row in rows if row.looted_by_name})
        unique_items = len(
            {
                row.item_id or row.item_name
                for row in rows
                if not row.is_silver and (row.item_id or row.item_name)
            }
        )
        top_looters = _build_top_looters(rows)
        top_items = _build_top_items(item_rows)
        top_silver_looters = _build_top_looters(silver_rows)
        changed = (
            self._event_count != len(rows)
            or self._latest_summary != latest_summary
            or self._export_text != export_text
            or self._total_quantity != total_quantity
            or self._item_event_count != len(item_rows)
            or self._item_total_quantity != item_total_quantity
            or self._silver_event_count != len(silver_rows)
            or self._silver_total_quantity != silver_total_quantity
            or self._unique_looters != unique_looters
            or self._unique_items != unique_items
        )
        self._events_model.set_items(rows)
        self._top_looters_model.set_items(top_looters)
        self._top_items_model.set_items(top_items)
        self._top_silver_looters_model.set_items(top_silver_looters)
        self._event_count = len(rows)
        self._latest_summary = latest_summary
        self._export_text = export_text
        self._total_quantity = total_quantity
        self._item_event_count = len(item_rows)
        self._item_total_quantity = item_total_quantity
        self._silver_event_count = len(silver_rows)
        self._silver_total_quantity = silver_total_quantity
        self._unique_looters = unique_looters
        self._unique_items = unique_items
        if changed:
            self.changed.emit()

    def _copy_to_clipboard(self, value: str) -> bool:
        text = str(value or "")
        if not text:
            return False
        try:
            clipboard = QGuiApplication.clipboard()
        except Exception:
            return False
        if clipboard is None:
            return False
        clipboard.setText(text)
        return True

    def _prompt_export_path(self, *, label: str, suggested_name: str, file_filter: str) -> str | None:
        try:
            from PySide6.QtWidgets import QFileDialog
        except Exception:
            return None
        base_dir = Path(self._log_path).expanduser().resolve().parent if self._log_path else Path.home()
        suggested_path = str((base_dir / suggested_name).resolve())
        selected_path, _selected_filter = QFileDialog.getSaveFileName(
            None,
            f"Export {label}",
            suggested_path,
            file_filter,
        )
        selected = str(selected_path or "").strip()
        return selected or None

    def _prompt_import_path(self, *, label: str, file_filter: str) -> str | None:
        try:
            from PySide6.QtWidgets import QFileDialog
        except Exception:
            return None
        base_dir = Path(self._log_path).expanduser().resolve().parent if self._log_path else Path.home()
        selected_path, _selected_filter = QFileDialog.getOpenFileName(
            None,
            f"Import {label}",
            str(base_dir),
            file_filter,
        )
        selected = str(selected_path or "").strip()
        return selected or None


def _filter_events(
    events: list[LootEvent],
    *,
    search_query: str,
    source_filter: str,
) -> list[LootEvent]:
    query = search_query.strip().lower()
    filtered: list[LootEvent] = []
    for event in events:
        if source_filter != "all" and event.source_kind != source_filter:
            continue
        if query:
            haystack = " ".join(
                part
                for part in (
                    event.looted_by.player_name,
                    event.looted_by.guild_name or "",
                    event.looted_by.alliance_name or "",
                    event.item.unique_name if event.item is not None and event.item.unique_name else "",
                    event.item.display_name if event.item is not None else "",
                    event.source_name or "",
                )
                if part
            ).lower()
            if query not in haystack:
                continue
        filtered.append(event)
    return filtered


def _filter_events_by_kind(events: list[LootEvent], *, kind_filter: str) -> list[LootEvent]:
    if kind_filter == "items":
        return [event for event in events if not event.is_silver]
    if kind_filter == "silver":
        return [event for event in events if event.is_silver]
    return list(events)


def _build_top_looters(rows: list[LootRow]) -> list[LootAggregateRow]:
    stats: dict[str, dict[str, int | str]] = {}
    for row in rows:
        entry = stats.setdefault(
            row.looted_by_name,
            {"quantity": 0, "events": 0, "sublabel": row.looted_by_guild or row.looted_by_alliance or ""},
        )
        entry["quantity"] = int(entry["quantity"]) + row.quantity
        entry["events"] = int(entry["events"]) + 1
    ordered = sorted(
        stats.items(),
        key=lambda item: (-int(item[1]["quantity"]), -int(item[1]["events"]), item[0].lower()),
    )
    return [
        LootAggregateRow(
            label=name,
            sublabel=str(values["sublabel"]),
            quantity=int(values["quantity"]),
            event_count=int(values["events"]),
        )
        for name, values in ordered[:10]
    ]


def _build_top_items(rows: list[LootRow]) -> list[LootAggregateRow]:
    stats: dict[str, dict[str, int | str]] = {}
    for row in rows:
        key = row.item_id or row.item_name or "Unknown item"
        entry = stats.setdefault(
            key,
            {"quantity": 0, "events": 0, "sublabel": row.item_id or row.source_kind},
        )
        entry["quantity"] = int(entry["quantity"]) + row.quantity
        entry["events"] = int(entry["events"]) + 1
    ordered = sorted(
        stats.items(),
        key=lambda item: (-int(item[1]["quantity"]), -int(item[1]["events"]), item[0].lower()),
    )
    return [
        LootAggregateRow(
            label=name,
            sublabel=str(values["sublabel"]),
            quantity=int(values["quantity"]),
            event_count=int(values["events"]),
        )
        for name, values in ordered[:10]
    ]


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
    if event.is_silver:
        return f"{event.looted_by.player_name} looted {int(event.quantity)} Silver"
    item_label = item_name or "Unknown item"
    source_label = source_name or "unknown source"
    return (
        f"{event.looted_by.player_name} looted {int(event.quantity)}x "
        f"{item_label} from {source_label}"
    )
