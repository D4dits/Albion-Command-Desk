from __future__ import annotations

from dataclasses import dataclass
import os
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
    icon_url: str
    category: str
    quantity: int
    source_name: str
    source_kind: str
    is_silver: bool
    summary: str


@dataclass(frozen=True)
class LootAggregateRow:
    label: str
    sublabel: str
    icon_url: str
    quantity: int
    event_count: int


class LootEventsModel(QAbstractListModel):
    TimestampRole = Qt.UserRole + 1
    LootedByNameRole = Qt.UserRole + 2
    LootedByGuildRole = Qt.UserRole + 3
    LootedByAllianceRole = Qt.UserRole + 4
    ItemIdRole = Qt.UserRole + 5
    ItemNameRole = Qt.UserRole + 6
    IconUrlRole = Qt.UserRole + 7
    CategoryRole = Qt.UserRole + 8
    QuantityRole = Qt.UserRole + 9
    SourceNameRole = Qt.UserRole + 10
    SourceKindRole = Qt.UserRole + 11
    IsSilverRole = Qt.UserRole + 12
    SummaryRole = Qt.UserRole + 13

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
        if role == self.IconUrlRole:
            return item.icon_url
        if role == self.CategoryRole:
            return item.category
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
            self.IconUrlRole: b"iconUrl",
            self.CategoryRole: b"category",
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
    IconUrlRole = Qt.UserRole + 3
    QuantityRole = Qt.UserRole + 4
    EventCountRole = Qt.UserRole + 5

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
        if role == self.IconUrlRole:
            return item.icon_url
        if role == self.QuantityRole:
            return item.quantity
        if role == self.EventCountRole:
            return item.event_count
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.LabelRole: b"label",
            self.SublabelRole: b"sublabel",
            self.IconUrlRole: b"iconUrl",
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
        self._top_sources_model = LootAggregateModel()
        self._top_silver_looters_model = LootAggregateModel()
        self._live_events: list[LootEvent] = []
        self._imported_events: list[LootEvent] | None = None
        self._all_events: list[LootEvent] = []
        self._search_query = ""
        self._source_filter = "all"
        self._looter_filter = "all"
        self._category_filter = "all"
        self._kind_filter = "items"
        self._looter_filter_options: list[str] = ["all"]
        self._category_filter_options: list[str] = [
            "all",
            "weapon",
            "armor",
            "bag",
            "cape",
            "mount",
            "consumable",
            "resource",
            "artifact",
            "other",
        ]
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
    def topSourcesModel(self) -> LootAggregateModel:
        return self._top_sources_model

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
    def looterFilter(self) -> str:
        return self._looter_filter

    @Property(str, notify=changed)
    def categoryFilter(self) -> str:
        return self._category_filter

    @Property(str, notify=changed)
    def kindFilter(self) -> str:
        return self._kind_filter

    @Property("QVariantList", constant=True)
    def sourceFilterOptions(self) -> list[str]:
        return ["all", "player", "mob", "system"]

    @Property("QVariantList", constant=True)
    def kindFilterOptions(self) -> list[str]:
        return ["items"]

    @Property("QVariantList", notify=changed)
    def looterFilterOptions(self) -> list[str]:
        return list(self._looter_filter_options)

    @Property("QVariantList", notify=changed)
    def categoryFilterOptions(self) -> list[str]:
        return list(self._category_filter_options)

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
        self._refresh_models(force_changed=True)

    @Slot(str)
    def setSourceFilter(self, value: str) -> None:
        next_value = str(value or "all").strip().lower() or "all"
        if next_value not in {"all", "player", "mob", "system"}:
            next_value = "all"
        if next_value == self._source_filter:
            return
        self._source_filter = next_value
        self._refresh_models(force_changed=True)

    @Slot(str)
    def setLooterFilter(self, value: str) -> None:
        next_value = str(value or "all").strip() or "all"
        if next_value not in self._looter_filter_options:
            next_value = "all"
        if next_value == self._looter_filter:
            return
        self._looter_filter = next_value
        self._refresh_models(force_changed=True)

    @Slot(str)
    def setCategoryFilter(self, value: str) -> None:
        next_value = str(value or "all").strip().lower() or "all"
        if next_value not in self._category_filter_options:
            next_value = "all"
        if next_value == self._category_filter:
            return
        self._category_filter = next_value
        self._refresh_models(force_changed=True)

    @Slot(str)
    def setKindFilter(self, value: str) -> None:
        next_value = "items"
        if next_value == self._kind_filter:
            return
        self._kind_filter = next_value
        self._refresh_models(force_changed=True)

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

    def _refresh_models(self, *, force_changed: bool = False) -> None:
        visible_events = [event for event in self._all_events if not event.is_silver]
        looter_options = _build_looter_options(visible_events)
        if self._looter_filter not in looter_options:
            self._looter_filter = "all"
        base_events = _filter_events(
            visible_events,
            search_query=self._search_query,
            source_filter=self._source_filter,
            looter_filter=self._looter_filter,
            category_filter=self._category_filter,
        )
        item_events = [event for event in base_events if not event.is_silver]
        filtered_events = list(item_events)
        rows = [_loot_event_to_row(event) for event in filtered_events]
        item_rows = [_loot_event_to_row(event) for event in item_events]
        export_text = loot_events_to_txt(list(reversed(filtered_events)))
        latest_summary = rows[0].summary if rows else ""
        total_quantity = sum(row.quantity for row in rows)
        item_total_quantity = sum(row.quantity for row in item_rows)
        silver_total_quantity = 0
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
        top_sources = _build_top_sources(rows)
        top_silver_looters: list[LootAggregateRow] = []
        changed = force_changed or (
            self._event_count != len(rows)
            or self._latest_summary != latest_summary
            or self._export_text != export_text
            or self._total_quantity != total_quantity
            or self._item_event_count != len(item_rows)
            or self._item_total_quantity != item_total_quantity
            or self._silver_event_count != 0
            or self._silver_total_quantity != silver_total_quantity
            or self._unique_looters != unique_looters
            or self._unique_items != unique_items
            or self._looter_filter_options != looter_options
        )
        self._events_model.set_items(rows)
        self._top_looters_model.set_items(top_looters)
        self._top_items_model.set_items(top_items)
        self._top_sources_model.set_items(top_sources)
        self._top_silver_looters_model.set_items(top_silver_looters)
        self._looter_filter_options = looter_options
        self._event_count = len(rows)
        self._latest_summary = latest_summary
        self._export_text = export_text
        self._total_quantity = total_quantity
        self._item_event_count = len(item_rows)
        self._item_total_quantity = item_total_quantity
        self._silver_event_count = 0
        self._silver_total_quantity = silver_total_quantity
        self._unique_looters = unique_looters
        self._unique_items = unique_items
        if changed:
            self.changed.emit()

    def _copy_to_clipboard(self, value: str) -> bool:
        text = str(value or "")
        if not text:
            return False
        app = _qt_gui_application()
        if app is None:
            return False
        clipboard = app.clipboard()
        if clipboard is None:
            return False
        clipboard.setText(text)
        return True

    def _prompt_export_path(self, *, label: str, suggested_name: str, file_filter: str) -> str | None:
        base_dir = Path(self._log_path).expanduser().resolve().parent if self._log_path else Path.home()
        suggested_path = str((base_dir / suggested_name).resolve())
        return self._prompt_file_path(
            mode="save",
            title=f"Export {label}",
            start_path=suggested_path,
            file_filter=file_filter,
        )

    def _prompt_import_path(self, *, label: str, file_filter: str) -> str | None:
        base_dir = Path(self._log_path).expanduser().resolve().parent if self._log_path else Path.home()
        return self._prompt_file_path(
            mode="open",
            title=f"Import {label}",
            start_path=str(base_dir),
            file_filter=file_filter,
        )

    def _prompt_file_path(
        self,
        *,
        mode: str,
        title: str,
        start_path: str,
        file_filter: str,
    ) -> str | None:
        selected_path = self._prompt_file_path_qtwidgets(
            mode=mode,
            title=title,
            start_path=start_path,
            file_filter=file_filter,
        )
        if not selected_path:
            selected_path = self._prompt_file_path_tk(
                mode=mode,
                title=title,
                start_path=start_path,
                file_filter=file_filter,
            )
        selected = str(selected_path or "").strip()
        return selected or None

    def _prompt_file_path_qtwidgets(
        self,
        *,
        mode: str,
        title: str,
        start_path: str,
        file_filter: str,
    ) -> str | None:
        try:
            from PySide6.QtWidgets import QApplication, QFileDialog
        except Exception:
            return None
        app = _qt_gui_application()
        if app is None or not isinstance(app, QApplication):
            return None
        if mode == "save":
            selected_path, _selected_filter = QFileDialog.getSaveFileName(
                None,
                title,
                start_path,
                file_filter,
            )
        else:
            selected_path, _selected_filter = QFileDialog.getOpenFileName(
                None,
                title,
                start_path,
                file_filter,
            )
        return str(selected_path or "").strip() or None

    def _prompt_file_path_tk(
        self,
        *,
        mode: str,
        title: str,
        start_path: str,
        file_filter: str,
    ) -> str | None:
        try:
            from tkinter import Tk, filedialog
        except Exception:
            return None

        filetypes = _tk_filetypes(file_filter)
        initial_dir = start_path
        initial_file = ""
        path_obj = Path(start_path)
        if mode == "save":
            initial_dir = str(path_obj.parent)
            initial_file = path_obj.name
        elif path_obj.suffix:
            initial_dir = str(path_obj.parent)

        root = None
        try:
            root = Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            if mode == "save":
                selected_path = filedialog.asksaveasfilename(
                    title=title,
                    initialdir=initial_dir,
                    initialfile=initial_file,
                    filetypes=filetypes,
                    defaultextension=".txt",
                )
            else:
                selected_path = filedialog.askopenfilename(
                    title=title,
                    initialdir=initial_dir,
                    filetypes=filetypes,
                )
            return str(selected_path or "").strip() or None
        except Exception:
            return None
        finally:
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass


def _tk_filetypes(file_filter: str) -> list[tuple[str, str]]:
    filetypes: list[tuple[str, str]] = []
    raw = str(file_filter or "").strip()
    if not raw:
        return [("All Files", "*.*")]
    for part in raw.split(";;"):
        label, sep, pattern_part = part.partition("(")
        if not sep:
            continue
        patterns = pattern_part.rstrip(") ").strip() or "*.*"
        normalized_patterns = " ".join(
            token if token.startswith("*.") or token == "*"
            else ("*." + token.lstrip("."))
            for token in patterns.split()
        ).strip() or "*.*"
        filetypes.append((label.strip() or "Files", normalized_patterns))
    return filetypes or [("All Files", "*.*")]


def _filter_events(
    events: list[LootEvent],
    *,
    search_query: str,
    source_filter: str,
    looter_filter: str,
    category_filter: str,
) -> list[LootEvent]:
    query = search_query.strip().lower()
    looter = str(looter_filter or "all").strip()
    category = str(category_filter or "all").strip().lower()
    filtered: list[LootEvent] = []
    for event in events:
        if event.is_silver:
            continue
        if source_filter != "all" and event.source_kind != source_filter:
            continue
        if looter != "all" and event.looted_by.player_name != looter:
            continue
        event_category = _item_category(
            event.item.unique_name if event.item is not None and event.item.unique_name else ""
        )
        if category != "all" and event_category != category:
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
    return [event for event in events if not event.is_silver]


def _build_looter_options(events: list[LootEvent]) -> list[str]:
    names = sorted(
        {
            event.looted_by.player_name
            for event in events
            if not event.is_silver and event.looted_by.player_name
        },
        key=str.lower,
    )
    return ["all", *names]


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
            icon_url="",
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
            {
                "quantity": 0,
                "events": 0,
                "label": row.item_name or row.item_id or "Unknown item",
                "sublabel": row.item_id if row.item_id and row.item_id != row.item_name else "",
                "icon_url": row.icon_url,
            },
        )
        entry["quantity"] = int(entry["quantity"]) + row.quantity
        entry["events"] = int(entry["events"]) + 1
    ordered = sorted(
        stats.items(),
        key=lambda item: (-int(item[1]["quantity"]), -int(item[1]["events"]), item[0].lower()),
    )
    return [
        LootAggregateRow(
            label=str(values.get("label") or name),
            sublabel=str(values["sublabel"]),
            icon_url=str(values.get("icon_url", "")),
            quantity=int(values["quantity"]),
            event_count=int(values["events"]),
        )
        for name, values in ordered[:10]
    ]


def _build_top_sources(rows: list[LootRow]) -> list[LootAggregateRow]:
    stats: dict[str, dict[str, int | str]] = {}
    for row in rows:
        if row.source_kind != "player" or not row.source_name:
            continue
        entry = stats.setdefault(
            row.source_name,
            {"quantity": 0, "events": 0, "sublabel": ""},
        )
        entry["quantity"] = int(entry["quantity"]) + row.quantity
        entry["events"] = int(entry["events"]) + 1
    ordered = sorted(
        stats.items(),
        key=lambda item: (-int(item[1]["events"]), -int(item[1]["quantity"]), item[0].lower()),
    )
    return [
        LootAggregateRow(
            label=name,
            sublabel=str(values["sublabel"]),
            icon_url="",
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
        icon_url=_loot_icon_url(item_id),
        category=_item_category(item_id),
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


def _loot_icon_url(item_id: str) -> str:
    unique = str(item_id or "").strip()
    if not unique or unique == "SILVER":
        return ""
    base = os.environ.get("ALBION_DPS_ICON_BASE", "https://render.albiononline.com/v1/item").strip()
    if not base:
        return ""
    return f"{base.rstrip('/')}/{unique}?size=64"


def _item_category(item_id: str) -> str:
    unique = str(item_id or "").upper()
    if not unique:
        return "other"
    if "ARTEFACT" in unique:
        return "artifact"
    if "_BAG" in unique or unique.endswith("BAG"):
        return "bag"
    if "_CAPE" in unique or unique.endswith("CAPE"):
        return "cape"
    if "MOUNT" in unique or "RIDING" in unique:
        return "mount"
    if any(token in unique for token in ("HEAD_", "ARMOR_", "SHOES_", "_HEAD_", "_ARMOR_", "_SHOES_")):
        return "armor"
    if "POTION" in unique or "MEAL" in unique or "FISH" in unique or "FOOD" in unique:
        return "consumable"
    if any(
        token in unique
        for token in ("METALBAR", "PLANKS", "LEATHER", "CLOTH", "ORE", "WOOD", "FIBER", "ROCK", "HIDE")
    ):
        return "resource"
    if any(
        token in unique
        for token in (
            "SWORD",
            "BOW",
            "STAFF",
            "DAGGER",
            "AXE",
            "MACE",
            "HAMMER",
            "SPEAR",
            "CROSSBOW",
            "KNUCKLES",
            "ORB",
            "TOTEM",
            "SHIELD",
            "BOOK",
        )
    ):
        return "weapon"
    return "other"


def _qt_gui_application():
    try:
        from PySide6.QtGui import QGuiApplication
    except Exception:
        return None
    return QGuiApplication.instance()
