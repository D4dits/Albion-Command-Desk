from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    Property,
    Signal,
    Slot,
)

from albion_dps.meter.session_meter import SessionEntry, SessionSummary
from albion_dps.domain.session_activity import SessionActivityEvent
from albion_dps.settings import AppSettings, load_app_settings, save_app_settings
from albion_dps.domain.weapon_colors import WEAPON_COLORS


SORT_KEY_MAP = {
    "dmg": "damage",
    "dps": "dps",
    "heal": "heal",
    "hps": "hps",
}

ROLE_COLORS = {
    "dps": "#ea5d5d",
    "heal": "#5deaa1",
    "tank": "#5da1ea",
    **WEAPON_COLORS,
}
FALLBACK_PALETTE = [
    "#7dd3fc",
    "#fbbf24",
    "#f472b6",
    "#34d399",
    "#a78bfa",
    "#f97316",
    "#22d3ee",
    "#e879f9",
]
FALLBACK_COLOR = "#9aa4af"
NON_PLAYER_NAME_PREFIXES = ("@",)
NON_PLAYER_NAMES = {"SYSTEM"}

HISTORY_LABEL_LIMIT = 14


@dataclass(frozen=True)
class PlayerRow:
    name: str
    damage: float
    heal: float
    dps: float
    hps: float
    bar_ratio: float
    role: str
    color: str
    weapon_name: str
    weapon_tier: str
    weapon_icon: str


@dataclass(frozen=True)
class HistoryRow:
    label: str
    meta: str
    players: str
    copy_text: str
    selected: bool


@dataclass(frozen=True)
class ActivityRow:
    title: str
    meta: str
    kind: str


class PlayerModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    DamageRole = Qt.UserRole + 2
    HealRole = Qt.UserRole + 3
    DpsRole = Qt.UserRole + 4
    HpsRole = Qt.UserRole + 5
    BarRole = Qt.UserRole + 6
    RoleRole = Qt.UserRole + 7
    BarColorRole = Qt.UserRole + 8
    WeaponNameRole = Qt.UserRole + 9
    WeaponTierRole = Qt.UserRole + 10
    WeaponIconRole = Qt.UserRole + 11

    def __init__(self) -> None:
        super().__init__()
        self._items: list[PlayerRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.NameRole:
            return item.name
        if role == self.DamageRole:
            return int(round(item.damage))
        if role == self.HealRole:
            return int(round(item.heal))
        if role == self.DpsRole:
            return float(item.dps)
        if role == self.HpsRole:
            return float(item.hps)
        if role == self.BarRole:
            return float(item.bar_ratio)
        if role == self.RoleRole:
            return item.role
        if role == self.BarColorRole:
            return item.color
        if role == self.WeaponNameRole:
            return item.weapon_name
        if role == self.WeaponTierRole:
            return item.weapon_tier
        if role == self.WeaponIconRole:
            return item.weapon_icon
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.NameRole: b"name",
            self.DamageRole: b"damage",
            self.HealRole: b"heal",
            self.DpsRole: b"dps",
            self.HpsRole: b"hps",
            self.BarRole: b"barRatio",
            self.RoleRole: b"role",
            self.BarColorRole: b"barColor",
            self.WeaponNameRole: b"weaponName",
            self.WeaponTierRole: b"weaponTier",
            self.WeaponIconRole: b"weaponIcon",
        }

    def set_items(self, items: list[PlayerRow]) -> None:
        if list(items) == self._items:
            return
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()


class HistoryModel(QAbstractListModel):
    LabelRole = Qt.UserRole + 1
    MetaRole = Qt.UserRole + 2
    PlayersRole = Qt.UserRole + 3
    CopyRole = Qt.UserRole + 4
    SelectedRole = Qt.UserRole + 5

    def __init__(self) -> None:
        super().__init__()
        self._items: list[HistoryRow] = []

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
        if role == self.MetaRole:
            return item.meta
        if role == self.PlayersRole:
            return item.players
        if role == self.CopyRole:
            return item.copy_text
        if role == self.SelectedRole:
            return item.selected
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.LabelRole: b"label",
            self.MetaRole: b"meta",
            self.PlayersRole: b"players",
            self.CopyRole: b"copyText",
            self.SelectedRole: b"selected",
        }

    def set_items(self, items: list[HistoryRow]) -> None:
        if list(items) == self._items:
            return
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

    def get_copy_text(self, index: int) -> str | None:
        if index < 0 or index >= len(self._items):
            return None
        return self._items[index].copy_text


class ActivityModel(QAbstractListModel):
    TitleRole = Qt.UserRole + 1
    MetaRole = Qt.UserRole + 2
    KindRole = Qt.UserRole + 3

    def __init__(self) -> None:
        super().__init__()
        self._items: list[ActivityRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.TitleRole:
            return item.title
        if role == self.MetaRole:
            return item.meta
        if role == self.KindRole:
            return item.kind
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.TitleRole: b"title",
            self.MetaRole: b"meta",
            self.KindRole: b"kind",
        }

    def set_items(self, items: list[ActivityRow]) -> None:
        if list(items) == self._items:
            return
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()


class UiState(QObject):
    modeChanged = Signal()
    zoneChanged = Signal()
    timeChanged = Signal()
    fameChanged = Signal()
    sortChanged = Signal()
    meterDisplayChanged = Signal()
    durationChanged = Signal()
    historyLimitChanged = Signal()
    historySelectionChanged = Signal()
    updateBannerChanged = Signal()
    updateControlChanged = Signal()
    manualUpdateCheckRequested = Signal()
    updateAutoCheckToggled = Signal(bool)
    sessionExported = Signal(str, str)
    sessionCompareChanged = Signal()

    def __init__(
        self,
        *,
        sort_key: str,
        top_n: int,
        history_limit: int,
        set_mode_callback: Callable[[str], None] | None = None,
        set_history_limit_callback: Callable[[int], None] | None = None,
        delete_history_callback: Callable[[str], bool] | None = None,
        clear_history_callback: Callable[[str | None], int] | None = None,
        toggle_manual_callback: Callable[[], bool] | None = None,
        role_lookup: Callable[[int], str | None] | None = None,
        weapon_lookup: Callable[[int], object | None] | None = None,
        update_auto_check: bool = True,
    ) -> None:
        super().__init__()
        self._mode = "battle"
        self._manual_active = False
        self._zone = "-"
        self._time_text = "-"
        self._duration_text = "00:00"
        self._fame_text = "0"
        self._fame_per_hour_text = "0.0"
        self._silver_text = "0"
        self._silver_per_hour_text = "0.0"
        self._sort_key = sort_key
        self._top_n = top_n
        self._history_limit = history_limit
        self._set_mode_callback = set_mode_callback
        self._set_history_limit_callback = set_history_limit_callback
        self._delete_history_callback = delete_history_callback
        self._clear_history_callback = clear_history_callback
        self._toggle_manual_callback = toggle_manual_callback
        self._players = PlayerModel()
        self._history = HistoryModel()
        self._activity = ActivityModel()
        self._last_snapshot = None
        self._last_names: dict[int, str] = {}
        self._last_history: list[SessionSummary] = []
        self._role_lookup = role_lookup
        self._weapon_lookup = weapon_lookup
        self._selected_history_index = -1
        self._selected_history_key: tuple[Any, ...] | None = None
        self._update_banner_visible = False
        self._update_banner_text = ""
        self._update_banner_url = ""
        self._update_banner_notes_url = ""
        self._update_auto_check = bool(update_auto_check)
        self._update_check_status = ""
        self._latest_update_version = ""
        self._dismissed_update_version = ""
        self._allowed_player_names: set[str] | None = None
        self._app_settings = load_app_settings()
        self._meter_export_dir = str(self._app_settings.meter_export_dir or "").strip()
        self._session_compare_title = ""
        self._session_compare_text = ""
        self._contributor_count = 0
        self._roster_count = 0

    @Property(str, notify=modeChanged)
    def mode(self) -> str:
        return self._mode

    @Property(bool, notify=modeChanged)
    def manualActive(self) -> bool:
        return self._manual_active

    @Property(str, notify=zoneChanged)
    def zone(self) -> str:
        return self._zone

    @Property(str, notify=timeChanged)
    def timeText(self) -> str:
        return self._time_text

    @Property(str, notify=durationChanged)
    def durationText(self) -> str:
        return self._duration_text

    @Property(str, notify=fameChanged)
    def fameText(self) -> str:
        return self._fame_text

    @Property(str, notify=fameChanged)
    def famePerHourText(self) -> str:
        return self._fame_per_hour_text

    @Property(str, notify=fameChanged)
    def silverText(self) -> str:
        return self._silver_text

    @Property(str, notify=fameChanged)
    def silverPerHourText(self) -> str:
        return self._silver_per_hour_text

    @Property(str, notify=sortChanged)
    def sortKey(self) -> str:
        return self._sort_key

    @Property(QObject, constant=True)
    def playersModel(self) -> QObject:
        return self._players

    @Property(QObject, constant=True)
    def historyModel(self) -> QObject:
        return self._history

    @Property(QObject, constant=True)
    def sessionActivityModel(self) -> QObject:
        return self._activity

    @Property(int, notify=meterDisplayChanged)
    def meterTopN(self) -> int:
        return self._top_n

    @Property(int, notify=meterDisplayChanged)
    def contributorCount(self) -> int:
        return self._contributor_count

    @Property(int, notify=meterDisplayChanged)
    def rosterCount(self) -> int:
        return self._roster_count

    @Property(int, notify=historyLimitChanged)
    def historyLimit(self) -> int:
        return self._history_limit

    @Property(int, notify=historySelectionChanged)
    def selectedHistoryIndex(self) -> int:
        return self._selected_history_index

    @Property(bool, notify=updateBannerChanged)
    def updateBannerVisible(self) -> bool:
        return self._update_banner_visible

    @Property(str, notify=updateBannerChanged)
    def updateBannerText(self) -> str:
        return self._update_banner_text

    @Property(str, notify=updateBannerChanged)
    def updateBannerUrl(self) -> str:
        return self._update_banner_url

    @Property(str, notify=updateBannerChanged)
    def updateBannerNotesUrl(self) -> str:
        return self._update_banner_notes_url

    @Property(bool, notify=updateControlChanged)
    def updateAutoCheck(self) -> bool:
        return self._update_auto_check

    @Property(str, notify=updateControlChanged)
    def updateCheckStatus(self) -> str:
        return self._update_check_status

    @Property(bool, notify=sessionCompareChanged)
    def sessionCompareAvailable(self) -> bool:
        return bool(self._session_compare_text)

    @Property(str, notify=sessionCompareChanged)
    def sessionCompareTitle(self) -> str:
        return self._session_compare_title

    @Property(str, notify=sessionCompareChanged)
    def sessionCompareText(self) -> str:
        return self._session_compare_text

    @Slot(str)
    def setSortKey(self, key: str) -> None:
        if key not in SORT_KEY_MAP:
            return
        if key == self._sort_key:
            return
        self._sort_key = key
        self.sortChanged.emit()
        self._refresh_player_table()

    @Slot(int)
    def setMeterTopN(self, value: int) -> None:
        try:
            top_n = int(value)
        except (TypeError, ValueError):
            return
        top_n = max(1, min(40, top_n))
        if top_n == self._top_n:
            return
        self._top_n = top_n
        self.meterDisplayChanged.emit()
        self._persist_app_settings()
        self._refresh_player_table()

    @Slot(int)
    def setHistoryLimit(self, value: int) -> None:
        try:
            limit = int(value)
        except (TypeError, ValueError):
            return
        limit = max(1, min(200, limit))
        if limit == self._history_limit:
            return
        self._history_limit = limit
        if self._set_history_limit_callback is not None:
            self._set_history_limit_callback(limit)
        self.historyLimitChanged.emit()
        self._persist_app_settings()
        self._refresh_history_table()

    @Slot(str)
    def setMode(self, mode: str) -> None:
        if mode not in ("battle", "zone", "manual"):
            return
        if self._set_mode_callback is not None:
            self._set_mode_callback(mode)
        self._set_mode(mode)

    def _copy_to_clipboard(self, text: str) -> bool:
        if not text:
            return False
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return False
        clipboard.setText(text)
        return True

    @Slot(int, result=bool)
    def copyHistory(self, index: int) -> bool:
        return self.copyHistoryFull(index)

    @Slot(int, result=bool)
    def copyHistoryShort(self, index: int) -> bool:
        if index < 0 or index >= len(self._last_history):
            return False
        return self._copy_to_clipboard(
            _format_session_copy(
                self._last_history[index],
                names=self._last_names,
                sort_key=self._sort_key,
                full=False,
            )
        )

    @Slot(int, result=bool)
    def copyHistoryFull(self, index: int) -> bool:
        if index < 0 or index >= len(self._last_history):
            return False
        return self._copy_to_clipboard(
            _format_session_copy(
                self._last_history[index],
                names=self._last_names,
                sort_key=self._sort_key,
                full=True,
            )
        )

    @Slot(bool, result=bool)
    def copyCurrent(self, full: bool) -> bool:
        if 0 <= self._selected_history_index < len(self._last_history):
            summary = self._last_history[self._selected_history_index]
            return self._copy_to_clipboard(
                _format_session_copy(
                    summary,
                    names=self._last_names,
                    sort_key=self._sort_key,
                    full=bool(full),
                )
            )
        if self._last_snapshot is None:
            return False
        return self._copy_to_clipboard(
            _format_live_copy(
                self._last_snapshot,
                names=self._last_names,
                sort_key=self._sort_key,
                full=bool(full),
                allowed_player_names=self._allowed_player_names,
            )
        )

    @Slot(result=bool)
    def toggleManual(self) -> bool:
        if self._toggle_manual_callback is None:
            return False
        self._manual_active = bool(self._toggle_manual_callback())
        self.modeChanged.emit()
        return self._manual_active

    @Slot(result=bool)
    def deleteSelectedHistory(self) -> bool:
        if not (0 <= self._selected_history_index < len(self._last_history)):
            return False
        summary = self._last_history[self._selected_history_index]
        if self._delete_history_callback is None:
            return False
        if not self._delete_history_callback(summary.encounter_id):
            return False
        self._last_history.pop(self._selected_history_index)
        self.clearHistorySelection()
        self._refresh_history_table()
        return True

    @Slot(result=bool)
    def clearCurrentHistory(self) -> bool:
        if self._clear_history_callback is None:
            return False
        self._clear_history_callback(self._mode)
        self._last_history.clear()
        self.clearHistorySelection()
        self._refresh_history_table()
        return True

    @Slot(result=str)
    def exportHistoryTxtInteractive(self) -> str:
        payload = _history_to_txt(self._last_history, names=self._last_names)
        return self._export_meter_payload_interactive(
            payload=payload,
            label="History TXT",
            suggested_name="acd-history.txt",
            file_filter="Text Files (*.txt);;All Files (*)",
        )

    @Slot(result=str)
    def exportHistoryCsvInteractive(self) -> str:
        payload = _history_to_csv(self._last_history, names=self._last_names)
        return self._export_meter_payload_interactive(
            payload=payload,
            label="History CSV",
            suggested_name="acd-history.csv",
            file_filter="CSV Files (*.csv);;All Files (*)",
        )

    @Slot(result=str)
    def exportHistoryJsonInteractive(self) -> str:
        payload = _history_to_json(self._last_history, names=self._last_names)
        return self._export_meter_payload_interactive(
            payload=payload,
            label="History JSON",
            suggested_name="acd-history.json",
            file_filter="JSON Files (*.json);;All Files (*)",
        )

    @Slot(result=bool)
    def copySessionCompare(self) -> bool:
        if not self._session_compare_text:
            return False
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return False
        payload = self._session_compare_title
        if payload and self._session_compare_text:
            payload = f"{payload}\n{self._session_compare_text}"
        else:
            payload = self._session_compare_text
        clipboard.setText(payload)
        return True

    @Slot(result=str)
    def exportSessionCompareInteractive(self) -> str:
        if not self._session_compare_text:
            return ""
        payload = self._session_compare_title
        if payload:
            payload = f"{payload}\n{self._session_compare_text}"
        else:
            payload = self._session_compare_text
        return self._export_meter_payload_interactive(
            payload=payload,
            label="Session compare",
            suggested_name="acd-session-compare.txt",
            file_filter="Text Files (*.txt);;All Files (*)",
        )

    @Slot(int)
    def selectHistory(self, index: int) -> None:
        if index < 0 or index >= len(self._last_history):
            return
        if index == self._selected_history_index:
            self.clearHistorySelection()
            return
        summary = self._last_history[index]
        self._selected_history_key = _summary_key(summary)
        self._set_selected_history_index(index)
        self._refresh_player_table()
        self._refresh_history_table()

    @Slot()
    def clearHistorySelection(self) -> None:
        if self._selected_history_index < 0 and self._selected_history_key is None:
            return
        self._selected_history_key = None
        self._set_selected_history_index(-1)
        self._refresh_player_table()
        self._refresh_history_table()

    @Slot(bool, str, str, str, str)
    def setUpdateStatus(
        self,
        available: bool,
        current_version: str,
        latest_version: str,
        release_url: str,
        notes_url: str = "",
    ) -> None:
        if not available:
            return
        self._latest_update_version = str(latest_version or "")
        banner_text = f"Update available: {current_version} -> {latest_version}"
        effective_notes_url = str(notes_url or release_url or "")
        changed = (
            banner_text != self._update_banner_text
            or release_url != self._update_banner_url
            or effective_notes_url != self._update_banner_notes_url
        )
        self._update_banner_text = banner_text
        self._update_banner_url = release_url
        self._update_banner_notes_url = effective_notes_url
        self._update_banner_visible = latest_version != self._dismissed_update_version
        self._update_check_status = banner_text
        if changed:
            self.updateBannerChanged.emit()
        self.updateControlChanged.emit()

    @Slot()
    def dismissUpdateBanner(self) -> None:
        if not self._update_banner_visible:
            return
        self._update_banner_visible = False
        self._dismissed_update_version = self._latest_update_version
        self.updateBannerChanged.emit()

    @Slot(bool)
    def setUpdateAutoCheck(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._update_auto_check:
            return
        self._update_auto_check = enabled
        self.updateControlChanged.emit()
        self.updateAutoCheckToggled.emit(enabled)

    @Slot()
    def requestManualUpdateCheck(self) -> None:
        self.setUpdateCheckStatus("Checking updates...")
        self.manualUpdateCheckRequested.emit()

    @Slot(str)
    def setUpdateCheckStatus(self, text: str) -> None:
        text = str(text or "")
        if text == self._update_check_status:
            return
        self._update_check_status = text
        self.updateControlChanged.emit()

    def update(
        self,
        snapshot,
        *,
        names: dict[int, str],
        history: list[SessionSummary],
        mode: str,
        zone: str | None,
        fame_total: int,
        fame_per_hour: float,
        silver_total: int,
        silver_per_hour: float,
        activity: list[SessionActivityEvent] | None = None,
        allowed_player_names: set[str] | None = None,
    ) -> None:
        self._last_snapshot = snapshot
        self._last_names = dict(names)
        self._last_history = list(history)
        self._allowed_player_names = (
            {name for name in allowed_player_names if isinstance(name, str) and name}
            if allowed_player_names is not None
            else None
        )
        self._set_mode(mode)
        self._set_zone(zone or "-")
        self._set_time(snapshot.timestamp)
        self._set_duration(getattr(snapshot, "duration", 0.0))
        self._set_meter_gains(
            fame_total,
            fame_per_hour,
            silver_total,
            silver_per_hour,
        )
        self._activity.set_items(_build_activity_rows(activity or []))
        self._sync_selected_history_index()
        self._refresh_player_table()
        self._refresh_history_table()

    def _set_mode(self, mode: str) -> None:
        if mode != self._mode:
            self._mode = mode
            if mode != "manual":
                self._manual_active = False
            self.modeChanged.emit()

    def _set_zone(self, zone: str) -> None:
        if zone != self._zone:
            self._zone = zone
            self.zoneChanged.emit()

    def _set_time(self, timestamp: float) -> None:
        text = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        if text != self._time_text:
            self._time_text = text
            self.timeChanged.emit()

    def _set_duration(self, seconds: float) -> None:
        text = _format_duration(seconds)
        if text != self._duration_text:
            self._duration_text = text
            self.durationChanged.emit()

    def _set_meter_gains(
        self,
        fame_total: int,
        fame_per_hour: float,
        silver_total: int,
        silver_per_hour: float,
    ) -> None:
        fame_total_text = str(int(fame_total))
        fame_per_hour_text = f"{fame_per_hour:.1f}"
        silver_total_text = str(int(silver_total))
        silver_per_hour_text = f"{silver_per_hour:.1f}"
        if (
            fame_total_text != self._fame_text
            or fame_per_hour_text != self._fame_per_hour_text
            or silver_total_text != self._silver_text
            or silver_per_hour_text != self._silver_per_hour_text
        ):
            self._fame_text = fame_total_text
            self._fame_per_hour_text = fame_per_hour_text
            self._silver_text = silver_total_text
            self._silver_per_hour_text = silver_per_hour_text
            self.fameChanged.emit()

    def _set_selected_history_index(self, index: int) -> None:
        if index == self._selected_history_index:
            return
        self._selected_history_index = index
        self.historySelectionChanged.emit()

    def _sync_selected_history_index(self) -> None:
        if self._selected_history_key is None:
            self._set_selected_history_index(-1)
            return
        for idx, summary in enumerate(self._last_history):
            if _summary_key(summary) == self._selected_history_key:
                self._set_selected_history_index(idx)
                return
        self._selected_history_key = None
        self._set_selected_history_index(-1)

    def _refresh_player_table(self) -> None:
        if self._selected_history_index >= 0 and self._selected_history_index < len(self._last_history):
            summary = self._last_history[self._selected_history_index]
            self._set_duration(summary.duration)
            rows = _build_player_rows_from_entries(
                    summary.entries,
                    sort_key=self._sort_key,
                    top_n=self._top_n,
                    names=self._last_names,
                    role_lookup=self._role_lookup,
                    weapon_lookup=self._weapon_lookup,
                )
            self._players.set_items(rows)
            self._set_meter_counts(
                len(rows), len(summary.roster_names) or len(summary.participant_names)
            )
            return
        if self._last_snapshot is None:
            self._set_duration(0.0)
            self._players.set_items([])
            self._set_meter_counts(0, 0)
            return
        self._set_duration(getattr(self._last_snapshot, "duration", 0.0))
        rows = _build_player_rows(
                self._last_snapshot.totals,
                names=self._last_names,
                sort_key=self._sort_key,
                top_n=self._top_n,
                role_lookup=self._role_lookup,
                weapon_lookup=self._weapon_lookup,
                allowed_player_names=self._allowed_player_names,
            )
        self._players.set_items(rows)
        self._set_meter_counts(
            len(rows), len(self._allowed_player_names or set())
        )

    def _set_meter_counts(self, contributors: int, roster: int) -> None:
        if contributors == self._contributor_count and roster == self._roster_count:
            return
        self._contributor_count = contributors
        self._roster_count = roster
        self.meterDisplayChanged.emit()

    def _refresh_history_table(self) -> None:
        self._history.set_items(
            _build_history_rows(
                self._last_history,
                names=self._last_names,
                limit=self._history_limit,
                selected_index=self._selected_history_index,
            )
        )
        self._refresh_session_compare()

    def _refresh_session_compare(self) -> None:
        title = ""
        text = ""
        if 0 <= self._selected_history_index < len(self._last_history):
            summary = self._last_history[self._selected_history_index]
            compare_index = self._selected_history_index + 1
            if compare_index >= len(self._last_history) and self._selected_history_index > 0:
                compare_index = self._selected_history_index - 1
            if 0 <= compare_index < len(self._last_history) and compare_index != self._selected_history_index:
                other = self._last_history[compare_index]
                title, text = _build_session_compare_text(
                    summary,
                    other,
                    names=self._last_names,
                    current_index=self._selected_history_index,
                    other_index=compare_index,
                )
        if title == self._session_compare_title and text == self._session_compare_text:
            return
        self._session_compare_title = title
        self._session_compare_text = text
        self.sessionCompareChanged.emit()

    def _export_meter_payload_interactive(
        self,
        *,
        payload: str,
        label: str,
        suggested_name: str,
        file_filter: str,
    ) -> str:
        path = self._prompt_export_path(label=label, suggested_name=suggested_name, file_filter=file_filter)
        if not path:
            return ""
        if not self._write_meter_export(raw_path=path, payload=payload):
            return ""
        self.sessionExported.emit(label, path)
        return path

    def _prompt_export_path(self, *, label: str, suggested_name: str, file_filter: str) -> str | None:
        try:
            from PySide6.QtWidgets import QFileDialog
        except Exception:
            return None
        base_dir = Path(self._meter_export_dir).expanduser() if self._meter_export_dir else Path.home()
        suggested_path = str((base_dir / suggested_name).resolve())
        selected_path, _selected_filter = QFileDialog.getSaveFileName(
            None,
            f"Export {label}",
            suggested_path,
            file_filter,
        )
        selected = str(selected_path or "").strip()
        if not selected:
            return None
        try:
            self._meter_export_dir = str(Path(selected).expanduser().resolve().parent)
            self._persist_app_settings()
        except Exception:
            pass
        return selected

    def _write_meter_export(self, *, raw_path: str, payload: str) -> bool:
        path_text = raw_path.strip()
        if not path_text or not payload:
            return False
        try:
            path = Path(path_text)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
        except Exception:
            return False
        self._meter_export_dir = str(path.parent)
        self._persist_app_settings()
        return True

    def _persist_app_settings(self) -> None:
        try:
            self._app_settings = AppSettings(
                update_auto_check=self._update_auto_check,
                market_selected_preset=self._app_settings.market_selected_preset,
                market_export_dir=self._app_settings.market_export_dir,
                meter_export_dir=self._meter_export_dir,
                meter_top_n=self._top_n,
                meter_history_limit=self._history_limit,
                loot_log_keep_files=self._app_settings.loot_log_keep_files,
                loot_buffer_seconds=self._app_settings.loot_buffer_seconds,
                loot_price_region=self._app_settings.loot_price_region,
                loot_price_city=self._app_settings.loot_price_city,
                loot_self_guild=self._app_settings.loot_self_guild,
                loot_self_alliance=self._app_settings.loot_self_alliance,
                scanner_repo_dir=self._app_settings.scanner_repo_dir,
                scanner_repo_url=self._app_settings.scanner_repo_url,
                log_level=self._app_settings.log_level,
            )
            save_app_settings(self._app_settings)
        except Exception:
            pass


def _build_player_rows(
    totals: dict[int, dict[str, float]],
    *,
    names: dict[int, str],
    sort_key: str,
    top_n: int,
    role_lookup: Callable[[int], str | None] | None = None,
    weapon_lookup: Callable[[int], object | None] | None = None,
    label_overrides: dict[int, str] | None = None,
    allowed_player_names: set[str] | None = None,
) -> list[PlayerRow]:
    rows: list[PlayerRow] = []
    metric = SORT_KEY_MAP.get(sort_key, "dps")
    max_damage = max((stats.get("damage", 0.0) for stats in totals.values()), default=0.0)
    max_heal = max((stats.get("heal", 0.0) for stats in totals.values()), default=0.0)
    for source_id, stats in totals.items():
        label = (
            (label_overrides or {}).get(source_id)
            or names.get(source_id)
            or str(source_id)
        )
        if not _is_player_label(label):
            continue
        if allowed_player_names is not None and label not in allowed_player_names:
            continue
        damage = float(stats.get("damage", 0.0))
        heal = float(stats.get("heal", 0.0))
        dps = float(stats.get("dps", 0.0))
        hps = float(stats.get("hps", 0.0))
        role = None
        if role_lookup is not None:
            role = role_lookup(source_id)
        if not role:
            role = _infer_role(damage, heal, max_damage=max_damage, max_heal=max_heal)
        weapon_name = ""
        weapon_tier = ""
        weapon_icon = ""
        if weapon_lookup is not None:
            info = weapon_lookup(source_id)
            if info is not None:
                weapon_name = str(getattr(info, "name", "") or getattr(info, "unique", "") or "")
                tier = getattr(info, "tier", None)
                enchant = getattr(info, "enchant", None)
                if isinstance(tier, int):
                    if not isinstance(enchant, int):
                        enchant = 0
                    weapon_tier = f"{tier}.{enchant}"
                weapon_icon = str(getattr(info, "icon_url", "") or "")
        color = _color_for_label(label, role)
        rows.append(
            PlayerRow(
                name=label,
                damage=damage,
                heal=heal,
                dps=dps,
                hps=hps,
                bar_ratio=0.0,
                role=role or "",
                color=color,
                weapon_name=weapon_name,
                weapon_tier=weapon_tier,
                weapon_icon=weapon_icon,
            )
        )
    rows = _collapse_player_rows(rows)
    rows.sort(key=lambda item: _metric_value(item, metric), reverse=True)
    rows = rows[: max(top_n, 1)]
    max_value = max((_metric_value(item, metric) for item in rows), default=0.0)
    if max_value <= 0:
        return rows
    with_ratio = []
    for item in rows:
        ratio = _metric_value(item, metric) / max_value if max_value else 0.0
        with_ratio.append(
            PlayerRow(
                name=item.name,
                damage=item.damage,
                heal=item.heal,
                dps=item.dps,
                hps=item.hps,
                bar_ratio=ratio,
                role=item.role,
                color=item.color,
                weapon_name=item.weapon_name,
                weapon_tier=item.weapon_tier,
                weapon_icon=item.weapon_icon,
            )
        )
    return with_ratio


def _metric_value(item: PlayerRow, metric: str) -> float:
    if metric == "damage":
        return item.damage
    if metric == "heal":
        return item.heal
    if metric == "hps":
        return item.hps
    return item.dps


def _infer_role(damage: float, heal: float, *, max_damage: float, max_heal: float) -> str | None:
    if heal > 0.0:
        if damage <= 0.0 or heal >= damage * 0.7 or (max_heal > 0.0 and heal >= max_heal * 0.5):
            return "heal"
    if max_damage > 0.0 and damage >= max_damage * 0.6:
        return "dps"
    if damage > 0.0 or heal > 0.0:
        return "tank"
    return None


def _color_for_label(label: str, role: str | None) -> str:
    if role and role in ROLE_COLORS:
        return ROLE_COLORS[role]
    if not label:
        return FALLBACK_PALETTE[0]
    idx = sum(ord(ch) for ch in label) % len(FALLBACK_PALETTE)
    return FALLBACK_PALETTE[idx]


def _build_history_rows(
    history: list[SessionSummary],
    *,
    names: dict[int, str],
    limit: int,
    selected_index: int = -1,
) -> list[HistoryRow]:
    rows: list[HistoryRow] = []
    for index, summary in enumerate(history[: max(limit, 1)]):
        label = summary.mode
        if summary.mode == "zone" and summary.label:
            label = f"zone {summary.label}"
        duration = _format_duration(summary.duration)
        totals = _format_totals(summary.total_damage, summary.total_heal)
        collapsed_entries = _collapse_history_entries(
            summary.entries,
            names=names,
            duration=summary.duration,
        )
        players_count = len(collapsed_entries)
        started = (
            datetime.fromtimestamp(summary.start_ts).strftime("%Y-%m-%d %H:%M:%S")
            if summary.start_ts > 0
            else "unknown time"
        )
        players = _format_players_preview(collapsed_entries, names=names, max_players=3)
        copy_text = _format_history_copy(summary, names=names, entries=collapsed_entries)
        rows.append(
            HistoryRow(
                label=f"{started} · {label} · {duration}",
                meta=(
                    f"{summary.source} | {totals} | contributors {players_count}"
                    f" / party {len(summary.roster_names) or len(summary.participant_names)}"
                ),
                players=players,
                copy_text=copy_text,
                selected=index == selected_index,
            )
        )
    return rows


def _format_duration(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if hours:
        return f"{hours}:{minutes % 60:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _format_totals(total_damage: float, total_heal: float) -> str:
    return f"total dmg {_format_int(total_damage)} heal {_format_int(total_heal)}"


def _format_players_preview(
    entries: list[SessionEntry],
    *,
    names: dict[int, str],
    max_players: int,
) -> str:
    players = entries[:max_players]
    parts = [
        f"{_shorten_label(_resolve_label(entry.label, names))} dmg {_format_int(entry.damage)} dps {entry.dps:.1f}"
        for entry in players
    ]
    extra = len(entries) - len(players)
    if extra > 0:
        parts.append(f"+{extra} others")
    return ", ".join(parts) if parts else "(no data)"


def _format_history_copy(
    summary: SessionSummary,
    *,
    names: dict[int, str],
    entries: list[SessionEntry] | None = None,
) -> str:
    label = summary.mode
    if summary.mode == "zone" and summary.label:
        label = f"zone {summary.label}"
    duration = _format_duration(summary.duration)
    totals = _format_totals(summary.total_damage, summary.total_heal)
    display_entries = entries if entries is not None else summary.entries
    header = f"{label} {duration} | {totals} | players {len(display_entries)}"
    lines = [header]
    for idx, entry in enumerate(display_entries, start=1):
        resolved = _resolve_label(entry.label, names)
        lines.append(
            f"{idx:02d}. {resolved} | dmg {_format_int(entry.damage)} | heal {_format_int(entry.heal)} | dps {entry.dps:.1f} | hps {entry.hps:.1f}"
        )
    return "\n".join(lines)


def _format_session_copy(
    summary: SessionSummary,
    *,
    names: dict[int, str],
    sort_key: str,
    full: bool,
) -> str:
    entries = _collapse_history_entries(
        summary.entries, names=names, duration=summary.duration
    )
    return _format_copy_rows(
        entries,
        title=(
            f"{datetime.fromtimestamp(summary.start_ts).strftime('%Y-%m-%d %H:%M:%S')} "
            f"| {summary.mode} | {summary.source} | {_format_duration(summary.duration)}"
        ),
        sort_key=sort_key,
        full=full,
        participant_count=len(summary.participant_names),
        roster_count=len(summary.roster_names),
    )


def _format_live_copy(
    snapshot,
    *,
    names: dict[int, str],
    sort_key: str,
    full: bool,
    allowed_player_names: set[str] | None,
) -> str:
    entries = [
        SessionEntry(
            label=names.get(source_id, str(source_id)),
            damage=float(stats.get("damage", 0.0)),
            heal=float(stats.get("heal", 0.0)),
            dps=float(stats.get("dps", 0.0)),
            hps=float(stats.get("hps", 0.0)),
            source_id=source_id,
        )
        for source_id, stats in snapshot.totals.items()
        if _is_player_label(names.get(source_id, str(source_id)))
        and (
            allowed_player_names is None
            or names.get(source_id, str(source_id)) in allowed_player_names
        )
    ]
    return _format_copy_rows(
        entries,
        title=f"live | {_format_duration(getattr(snapshot, 'duration', 0.0))}",
        sort_key=sort_key,
        full=full,
        participant_count=len(entries),
        roster_count=len(allowed_player_names or set()),
    )


def _format_copy_rows(
    entries: list[SessionEntry],
    *,
    title: str,
    sort_key: str,
    full: bool,
    participant_count: int,
    roster_count: int,
) -> str:
    metric = SORT_KEY_MAP.get(sort_key, "dps")
    ordered = sorted(entries, key=lambda entry: getattr(entry, metric), reverse=True)
    lines = [
        f"{title} | contributors {len(ordered)} | participants {participant_count}"
        f" | party {roster_count} | sorted {sort_key}"
    ]
    total_damage = sum(entry.damage for entry in ordered)
    total_heal = sum(entry.heal for entry in ordered)
    for index, entry in enumerate(ordered, start=1):
        if full:
            damage_share = (entry.damage / total_damage * 100.0) if total_damage else 0.0
            heal_share = (entry.heal / total_heal * 100.0) if total_heal else 0.0
            lines.append(
                f"{index:02d}. {entry.label} | dmg {_format_int(entry.damage)} "
                f"({damage_share:.1f}%) | dps {entry.dps:.1f} | heal {_format_int(entry.heal)} "
                f"({heal_share:.1f}%) | hps {entry.hps:.1f}"
            )
        elif sort_key in {"heal", "hps"}:
            share = (entry.heal / total_heal * 100.0) if total_heal else 0.0
            lines.append(
                f"{index:02d}. {entry.label} | heal {_format_int(entry.heal)} "
                f"| hps {entry.hps:.1f} | {share:.1f}%"
            )
        else:
            share = (entry.damage / total_damage * 100.0) if total_damage else 0.0
            lines.append(
                f"{index:02d}. {entry.label} | dmg {_format_int(entry.damage)} "
                f"| dps {entry.dps:.1f} | {share:.1f}%"
            )
    return "\n".join(lines)


def _history_to_txt(history: list[SessionSummary], *, names: dict[int, str]) -> str:
    blocks = [
        _format_history_copy(summary, names=names, entries=_collapse_history_entries(summary.entries, names=names, duration=summary.duration))
        for summary in history
    ]
    return "\n\n".join(blocks).strip()


def _history_to_csv(history: list[SessionSummary], *, names: dict[int, str]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "session_index",
            "encounter_id",
            "source",
            "mode",
            "label",
            "duration_seconds",
            "total_damage",
            "total_heal",
            "player_count",
            "player_rank",
            "player_name",
            "damage",
            "heal",
            "dps",
            "hps",
        ]
    )
    for index, summary in enumerate(history, start=1):
        entries = _collapse_history_entries(summary.entries, names=names, duration=summary.duration)
        session_label = summary.label or ""
        for rank, entry in enumerate(entries, start=1):
            writer.writerow(
                [
                    index,
                    summary.encounter_id,
                    summary.source,
                    summary.mode,
                    session_label,
                    round(summary.duration, 2),
                    _format_int(summary.total_damage),
                    _format_int(summary.total_heal),
                    len(entries),
                    rank,
                    _resolve_label(entry.label, names),
                    _format_int(entry.damage),
                    _format_int(entry.heal),
                    f"{entry.dps:.1f}",
                    f"{entry.hps:.1f}",
                ]
            )
    return buf.getvalue()


def _history_to_json(history: list[SessionSummary], *, names: dict[int, str]) -> str:
    payload: list[dict[str, Any]] = []
    for index, summary in enumerate(history, start=1):
        entries = _collapse_history_entries(summary.entries, names=names, duration=summary.duration)
        payload.append(
            {
                "session_index": index,
                "encounter_id": summary.encounter_id,
                "source": summary.source,
                "mode": summary.mode,
                "label": summary.label,
                "start_ts": summary.start_ts,
                "end_ts": summary.end_ts,
                "duration_seconds": round(summary.duration, 2),
                "total_damage": _format_int(summary.total_damage),
                "total_heal": _format_int(summary.total_heal),
                "reason": summary.reason,
                "roster_names": list(summary.roster_names),
                "participant_names": list(summary.participant_names),
                "player_count": len(entries),
                "entries": [
                    {
                        "player_name": _resolve_label(entry.label, names),
                        "damage": _format_int(entry.damage),
                        "heal": _format_int(entry.heal),
                        "dps": round(entry.dps, 1),
                        "hps": round(entry.hps, 1),
                        "source_id": entry.source_id,
                    }
                    for entry in entries
                ],
            }
        )
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _build_session_compare_text(
    current: SessionSummary,
    other: SessionSummary,
    *,
    names: dict[int, str],
    current_index: int,
    other_index: int,
) -> tuple[str, str]:
    current_entries = _collapse_history_entries(current.entries, names=names, duration=current.duration)
    other_entries = _collapse_history_entries(other.entries, names=names, duration=other.duration)
    current_top = current_entries[0] if current_entries else None
    other_top = other_entries[0] if other_entries else None
    relation = "older" if other_index > current_index else "newer"
    title = f"Compare history #{current_index + 1} vs {relation} #{other_index + 1}"
    lines = [
        _compare_metric_line("Duration", current.duration, other.duration, unit="s"),
        _compare_metric_line("Total damage", current.total_damage, other.total_damage),
        _compare_metric_line("Total heal", current.total_heal, other.total_heal),
        _compare_metric_line("Players", len(current_entries), len(other_entries)),
    ]
    if current_top is not None or other_top is not None:
        current_top_label = _resolve_label(current_top.label, names) if current_top is not None else "-"
        other_top_label = _resolve_label(other_top.label, names) if other_top is not None else "-"
        current_top_dps = current_top.dps if current_top is not None else 0.0
        other_top_dps = other_top.dps if other_top is not None else 0.0
        lines.append(
            "Top DPS: "
            f"{current_top_label} ({current_top_dps:.1f}) vs "
            f"{other_top_label} ({other_top_dps:.1f})"
        )
    return title, "\n".join(lines)


def _compare_metric_line(label: str, current: float, other: float, *, unit: str = "") -> str:
    delta = current - other
    delta_prefix = "+" if delta >= 0 else ""
    current_text = f"{current:.1f}" if unit == "s" else str(_format_int(current))
    other_text = f"{other:.1f}" if unit == "s" else str(_format_int(other))
    delta_text = f"{delta_prefix}{delta:.1f}" if unit == "s" else f"{delta_prefix}{_format_int(delta)}"
    suffix = unit if unit else ""
    if suffix:
        current_text = f"{current_text}{suffix}"
        other_text = f"{other_text}{suffix}"
        delta_text = f"{delta_text}{suffix}"
    return f"{label}: {current_text} vs {other_text} ({delta_text})"


def _build_activity_rows(events: list[SessionActivityEvent]) -> list[ActivityRow]:
    rows: list[ActivityRow] = []
    for event in events:
        timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S") if event.timestamp > 0 else "--:--:--"
        rows.append(
            ActivityRow(
                title=event.title,
                meta=f"{event.detail} | {timestamp}",
                kind=event.kind,
            )
        )
    return rows


def _format_int(value: float) -> int:
    return int(round(value))


def _resolve_label(label: str, names: dict[int, str]) -> str:
    if label.isdigit():
        mapped = names.get(int(label))
        if mapped:
            return mapped
    return label


def _shorten_label(label: str, limit: int = HISTORY_LABEL_LIMIT) -> str:
    if len(label) <= limit:
        return label
    if limit <= 3:
        return label[:limit]
    return f"{label[: limit - 3]}..."


def _build_player_rows_from_entries(
    entries: list[SessionEntry],
    *,
    sort_key: str,
    top_n: int,
    names: dict[int, str],
    allowed_player_names: set[str] | None = None,
    role_lookup: Callable[[int], str | None] | None = None,
    weapon_lookup: Callable[[int], object | None] | None = None,
) -> list[PlayerRow]:
    metric = SORT_KEY_MAP.get(sort_key, "dps")
    max_damage = max((entry.damage for entry in entries), default=0.0)
    max_heal = max((entry.heal for entry in entries), default=0.0)
    rows: list[PlayerRow] = []
    for entry in entries:
        label = _resolve_label(entry.label, names)
        if not _is_player_label(label):
            continue
        if allowed_player_names is not None and label not in allowed_player_names:
            continue
        role = None
        if role_lookup is not None and entry.source_id is not None:
            role = role_lookup(entry.source_id)
        role = role or _infer_role(entry.damage, entry.heal, max_damage=max_damage, max_heal=max_heal) or ""
        weapon_name = ""
        weapon_tier = ""
        weapon_icon = ""
        if weapon_lookup is not None and entry.source_id is not None:
            info = weapon_lookup(entry.source_id)
            if info is not None:
                weapon_name = str(getattr(info, "name", "") or getattr(info, "unique", "") or "")
                tier = getattr(info, "tier", None)
                enchant = getattr(info, "enchant", None)
                if isinstance(tier, int):
                    if not isinstance(enchant, int):
                        enchant = 0
                    weapon_tier = f"{tier}.{enchant}"
                weapon_icon = str(getattr(info, "icon_url", "") or "")
        rows.append(
            PlayerRow(
                name=label,
                damage=entry.damage,
                heal=entry.heal,
                dps=entry.dps,
                hps=entry.hps,
                bar_ratio=0.0,
                role=role,
                color=_color_for_label(label, role),
                weapon_name=weapon_name,
                weapon_tier=weapon_tier,
                weapon_icon=weapon_icon,
            )
        )
    rows = _collapse_player_rows(rows)
    rows.sort(key=lambda item: _metric_value(item, metric), reverse=True)
    rows = rows[: max(top_n, 1)]
    max_value = max((_metric_value(item, metric) for item in rows), default=0.0)
    if max_value <= 0:
        return rows
    out: list[PlayerRow] = []
    for item in rows:
        ratio = _metric_value(item, metric) / max_value if max_value else 0.0
        out.append(
            PlayerRow(
                name=item.name,
                damage=item.damage,
                heal=item.heal,
                dps=item.dps,
                hps=item.hps,
                bar_ratio=ratio,
                role=item.role,
                color=item.color,
                weapon_name=item.weapon_name,
                weapon_tier=item.weapon_tier,
                weapon_icon=item.weapon_icon,
            )
        )
    return out


def _collapse_player_rows(rows: list[PlayerRow]) -> list[PlayerRow]:
    if not rows:
        return []
    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        current = grouped.get(row.name)
        if current is None:
            grouped[row.name] = {
                "damage": float(row.damage),
                "heal": float(row.heal),
                "dps": float(row.dps),
                "hps": float(row.hps),
                "role": row.role or "",
                "weapon_name": row.weapon_name,
                "weapon_tier": row.weapon_tier,
                "weapon_icon": row.weapon_icon,
            }
            continue
        current["damage"] = float(current["damage"]) + float(row.damage)
        current["heal"] = float(current["heal"]) + float(row.heal)
        current["dps"] = float(current["dps"]) + float(row.dps)
        current["hps"] = float(current["hps"]) + float(row.hps)
        if row.role in WEAPON_COLORS:
            current["role"] = row.role
        elif not current["role"] and row.role:
            current["role"] = row.role
        if not current["weapon_name"] and row.weapon_name:
            current["weapon_name"] = row.weapon_name
            current["weapon_tier"] = row.weapon_tier
            current["weapon_icon"] = row.weapon_icon

    max_damage = max((float(item["damage"]) for item in grouped.values()), default=0.0)
    max_heal = max((float(item["heal"]) for item in grouped.values()), default=0.0)
    collapsed: list[PlayerRow] = []
    for name, item in grouped.items():
        damage = float(item["damage"])
        heal = float(item["heal"])
        dps = float(item["dps"])
        hps = float(item["hps"])
        role = str(item.get("role") or "")
        if not role:
            role = _infer_role(damage, heal, max_damage=max_damage, max_heal=max_heal) or ""
        collapsed.append(
            PlayerRow(
                name=name,
                damage=damage,
                heal=heal,
                dps=dps,
                hps=hps,
                bar_ratio=0.0,
                role=role,
                color=_color_for_label(name, role),
                weapon_name=str(item["weapon_name"] or ""),
                weapon_tier=str(item["weapon_tier"] or ""),
                weapon_icon=str(item["weapon_icon"] or ""),
            )
        )
    return collapsed


def _collapse_history_entries(
    entries: list[SessionEntry],
    *,
    names: dict[int, str],
    duration: float,
) -> list[SessionEntry]:
    grouped: dict[str, tuple[float, float]] = {}
    for entry in entries:
        label = _resolve_label(entry.label, names)
        if not _is_player_label(label):
            continue
        damage, heal = grouped.get(label, (0.0, 0.0))
        grouped[label] = (damage + float(entry.damage), heal + float(entry.heal))
    collapsed: list[SessionEntry] = []
    for label, (damage, heal) in grouped.items():
        if duration > 0:
            dps = damage / duration
            hps = heal / duration
        else:
            dps = 0.0
            hps = 0.0
        collapsed.append(
            SessionEntry(
                label=label,
                damage=damage,
                heal=heal,
                dps=dps,
                hps=hps,
                source_id=None,
            )
        )
    collapsed.sort(key=lambda item: item.damage, reverse=True)
    return collapsed


def _summary_key(summary: SessionSummary) -> tuple[Any, ...]:
    if summary.encounter_id:
        return (summary.encounter_id,)
    return (
        summary.mode,
        round(summary.start_ts, 3),
        round(summary.end_ts, 3),
        round(summary.duration, 3),
        summary.label or "",
        summary.reason,
    )


def _is_player_label(label: str | None) -> bool:
    if not isinstance(label, str):
        return False
    normalized = label.strip()
    if not normalized:
        return False
    if normalized.isdigit():
        return False
    if normalized in NON_PLAYER_NAMES:
        return False
    upper = normalized.upper()
    if upper.startswith("MOB_") or upper.startswith("NPC_"):
        return False
    return not normalized.startswith(NON_PLAYER_NAME_PREFIXES)
