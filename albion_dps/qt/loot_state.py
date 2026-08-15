from __future__ import annotations

from dataclasses import dataclass
import csv
import io
import os
from pathlib import Path
import re
import threading
import time
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
from albion_dps.domain.loot_session_store import LootSessionStore
from albion_dps.domain.loot_types import LootEvent, LootItemRef, LootPlayer
from albion_dps.market.models import MarketRegion
from albion_dps.settings import load_app_settings, update_app_settings


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
    event_id: str = ""
    quality: int = 0
    quality_text: str = "Q?"
    eligibility_reason: str = "unknown"
    market_unit: int = 0
    liquidation_unit: int = 0
    market_value: int = 0
    liquidation_value: int = 0
    value_estimated: bool = False
    settlement_status: str = "pending"
    outstanding_quantity: int = 0
    returned_quantity: int = 0
    sold_quantity: int = 0
    lost_quantity: int = 0
    allowed_quantity: int = 0
    unreturned_quantity: int = 0
    excluded_quantity: int = 0
    actual_sold_value: int = 0
    item_tier: int = 0
    item_enchant: int = 0
    item_tier_text: str = ""


@dataclass(frozen=True)
class LootAggregateRow:
    label: str
    sublabel: str
    icon_url: str
    quantity: int
    event_count: int
    market_value: int = 0
    liquidation_value: int = 0
    outstanding_value: int = 0


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
    EventIdRole = Qt.UserRole + 14
    QualityRole = Qt.UserRole + 15
    QualityTextRole = Qt.UserRole + 16
    EligibilityReasonRole = Qt.UserRole + 17
    MarketUnitRole = Qt.UserRole + 18
    LiquidationUnitRole = Qt.UserRole + 19
    MarketValueRole = Qt.UserRole + 20
    LiquidationValueRole = Qt.UserRole + 21
    ValueEstimatedRole = Qt.UserRole + 22
    SettlementStatusRole = Qt.UserRole + 23
    OutstandingQuantityRole = Qt.UserRole + 24
    ItemTierRole = Qt.UserRole + 25
    ItemEnchantRole = Qt.UserRole + 26
    ItemTierTextRole = Qt.UserRole + 27

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
        if role == self.EventIdRole:
            return item.event_id
        if role == self.QualityRole:
            return item.quality
        if role == self.QualityTextRole:
            return item.quality_text
        if role == self.EligibilityReasonRole:
            return item.eligibility_reason
        if role == self.MarketUnitRole:
            return item.market_unit
        if role == self.LiquidationUnitRole:
            return item.liquidation_unit
        if role == self.MarketValueRole:
            return item.market_value
        if role == self.LiquidationValueRole:
            return item.liquidation_value
        if role == self.ValueEstimatedRole:
            return item.value_estimated
        if role == self.SettlementStatusRole:
            return item.settlement_status
        if role == self.OutstandingQuantityRole:
            return item.outstanding_quantity
        if role == self.ItemTierRole:
            return item.item_tier
        if role == self.ItemEnchantRole:
            return item.item_enchant
        if role == self.ItemTierTextRole:
            return item.item_tier_text
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
            self.EventIdRole: b"eventId",
            self.QualityRole: b"quality",
            self.QualityTextRole: b"qualityText",
            self.EligibilityReasonRole: b"eligibilityReason",
            self.MarketUnitRole: b"marketUnit",
            self.LiquidationUnitRole: b"liquidationUnit",
            self.MarketValueRole: b"marketValue",
            self.LiquidationValueRole: b"liquidationValue",
            self.ValueEstimatedRole: b"valueEstimated",
            self.SettlementStatusRole: b"settlementStatus",
            self.OutstandingQuantityRole: b"outstandingQuantity",
            self.ItemTierRole: b"itemTier",
            self.ItemEnchantRole: b"itemEnchant",
            self.ItemTierTextRole: b"itemTierText",
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
    MarketValueRole = Qt.UserRole + 6
    LiquidationValueRole = Qt.UserRole + 7
    OutstandingValueRole = Qt.UserRole + 8

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
        if role == self.MarketValueRole:
            return item.market_value
        if role == self.LiquidationValueRole:
            return item.liquidation_value
        if role == self.OutstandingValueRole:
            return item.outstanding_value
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.LabelRole: b"label",
            self.SublabelRole: b"sublabel",
            self.IconUrlRole: b"iconUrl",
            self.QuantityRole: b"quantity",
            self.EventCountRole: b"eventCount",
            self.MarketValueRole: b"marketValue",
            self.LiquidationValueRole: b"liquidationValue",
            self.OutstandingValueRole: b"outstandingValue",
        }

    def set_items(self, items: list[LootAggregateRow]) -> None:
        if items == self._items:
            return
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()


class LootState(QObject):
    changed = Signal()
    pricingReady = Signal(object, str)

    def __init__(
        self,
        *,
        history_limit: int = 200,
        session_store: LootSessionStore | None = None,
        market_service=None,
    ) -> None:
        super().__init__()
        app_settings = load_app_settings()
        self._history_limit = max(1, int(history_limit))
        self._session_store = session_store
        self._market_service = market_service
        self._tracker = None
        self._observation_versions: dict[str, tuple[object, ...]] = {}
        self._stored_rows: dict[str, dict[str, object]] = {}
        self._selected_session_id = ""
        self._session_ids: list[str] = []
        self._session_options: list[str] = []
        self._session_active = False
        self._session_title = ""
        self._session_started_at = 0.0
        self._session_ended_at = 0.0
        self._pending_scope_count = 0
        self._total_market_value = 0
        self._total_liquidation_value = 0
        self._outstanding_market_value = 0
        self._pricing_status = "idle"
        self._pricing_running = False
        self._last_price_refresh_at = 0.0
        self._price_region = app_settings.loot_price_region
        self._price_city = app_settings.loot_price_city
        self._buffer_seconds = int(app_settings.loot_buffer_seconds)
        self._self_guild = app_settings.loot_self_guild
        self._self_alliance = app_settings.loot_self_alliance
        self._last_prune_at = 0.0
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
        self._source_name_filter = ""
        self._looter_filter = "all"
        self._category_filter = "all"
        self._kind_filter = "items"
        self._sort_order = "newest"
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
        self.pricingReady.connect(self._apply_price_results)
        self._refresh_session_list()

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
    def sourceNameFilter(self) -> str:
        return self._source_name_filter

    @Property(str, notify=changed)
    def looterFilter(self) -> str:
        return self._looter_filter

    @Property(str, notify=changed)
    def categoryFilter(self) -> str:
        return self._category_filter

    @Property(str, notify=changed)
    def kindFilter(self) -> str:
        return self._kind_filter

    @Property(str, notify=changed)
    def sortOrder(self) -> str:
        return self._sort_order

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

    @Property(bool, notify=changed)
    def sessionActive(self) -> bool:
        return self._session_active

    @Property(str, notify=changed)
    def sessionTitle(self) -> str:
        return self._session_title

    @Property(str, notify=changed)
    def selectedSessionId(self) -> str:
        return self._selected_session_id

    @Property(str, notify=changed)
    def sessionDurationText(self) -> str:
        if self._session_started_at <= 0:
            return "00:00"
        end = time.time() if self._session_active else self._session_ended_at
        return _format_duration(max(0.0, end - self._session_started_at))

    @Property("QVariantList", notify=changed)
    def sessionOptions(self) -> list[str]:
        return list(self._session_options)

    @Property(int, notify=changed)
    def pendingScopeCount(self) -> int:
        return self._pending_scope_count

    @Property(int, notify=changed)
    def totalMarketValue(self) -> int:
        return self._total_market_value

    @Property(int, notify=changed)
    def totalLiquidationValue(self) -> int:
        return self._total_liquidation_value

    @Property(int, notify=changed)
    def outstandingMarketValue(self) -> int:
        return self._outstanding_market_value

    @Property(str, notify=changed)
    def pricingStatus(self) -> str:
        return self._pricing_status

    @Property(str, notify=changed)
    def priceRegion(self) -> str:
        return self._price_region

    @Property(str, notify=changed)
    def priceCity(self) -> str:
        return self._price_city

    @Property(int, notify=changed)
    def bufferSeconds(self) -> int:
        return self._buffer_seconds

    @Property(str, notify=changed)
    def selfGuild(self) -> str:
        return self._self_guild

    @Property(str, notify=changed)
    def selfAlliance(self) -> str:
        return self._self_alliance

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
        if next_value != "player":
            self._source_name_filter = ""
        self._refresh_models(force_changed=True)

    @Slot(str)
    def setSourceNameFilter(self, value: str) -> None:
        next_value = str(value or "").strip()
        if next_value == self._source_name_filter:
            return
        self._source_name_filter = next_value
        if next_value:
            self._source_filter = "player"
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

    @Slot(str)
    def setSortOrder(self, value: str) -> None:
        next_value = str(value or "newest").strip().lower() or "newest"
        if next_value not in {"newest", "tier_desc", "item_name"}:
            next_value = "newest"
        if next_value == self._sort_order:
            return
        self._sort_order = next_value
        self._refresh_models(force_changed=True)

    @Slot(str, result=bool)
    def startSession(self, title: str = "") -> bool:
        if self._session_store is None:
            return False
        record = self._session_store.start_session(
            title=str(title or ""),
            lookback_seconds=self._buffer_seconds,
        )
        self._selected_session_id = record.session_id
        self._reload_from_store(force_changed=True)
        return True

    @Slot(result=bool)
    def stopSession(self) -> bool:
        if self._session_store is None:
            return False
        record = self._session_store.stop_session()
        if record is None:
            return False
        self._selected_session_id = record.session_id
        self._reload_from_store(force_changed=True)
        return True

    @Slot(int)
    def selectSession(self, index: int) -> None:
        if index < 0 or index >= len(self._session_ids):
            return
        self._selected_session_id = self._session_ids[index]
        self._imported_events = None
        self._imported_log_path = ""
        self._reload_from_store(force_changed=True)

    @Slot()
    def showLiveBuffer(self) -> None:
        self._selected_session_id = ""
        self._imported_events = None
        self._imported_log_path = ""
        self._reload_from_store(force_changed=True)

    @Slot(result=bool)
    def deleteSelectedSession(self) -> bool:
        if self._session_store is None or not self._selected_session_id or self._session_active:
            return False
        deleted = self._session_store.delete_session(self._selected_session_id)
        if deleted:
            self._selected_session_id = ""
            self._reload_from_store(force_changed=True)
        return deleted

    @Slot(str, str, int, int, str, result=bool)
    def settleEvent(
        self,
        event_id: str,
        action: str,
        quantity: int = 0,
        actual_value: int = 0,
        note: str = "",
    ) -> bool:
        if self._session_store is None:
            return False
        ok = self._session_store.add_settlement(
            event_id,
            action=action,
            quantity=quantity,
            actual_value=actual_value,
            note=note,
        )
        if ok:
            self._reload_from_store(force_changed=True)
        return ok

    @Slot(str, result=bool)
    def resetEventSettlement(self, event_id: str) -> bool:
        if self._session_store is None:
            return False
        ok = self._session_store.reset_settlements(event_id, note="Reset from Loot UI")
        if ok:
            self._reload_from_store(force_changed=True)
        return ok

    @Slot(str, str, result=int)
    def settlePlayer(self, player_name: str, action: str) -> int:
        if self._session_store is None or not self._selected_session_id:
            return 0
        changed = self._session_store.settle_player(
            self._selected_session_id,
            player_name,
            action=action,
            note="Bulk player settlement from Loot UI",
        )
        if changed:
            self._reload_from_store(force_changed=True)
        return changed

    @Slot(str, int, result=bool)
    def setEventQuality(self, event_id: str, quality: int) -> bool:
        if self._session_store is None:
            return False
        normalized = quality if 1 <= int(quality) <= 5 else None
        ok = self._session_store.set_quality(event_id, normalized)
        if ok:
            self._reload_from_store(force_changed=True)
            self.refreshPrices()
        return ok

    @Slot(str)
    def setPriceCity(self, value: str) -> None:
        city = str(value or "").strip()
        if not city or city == self._price_city:
            return
        self._price_city = city
        update_app_settings(loot_price_city=city)
        self.changed.emit()

    @Slot(str)
    def setPriceRegion(self, value: str) -> None:
        region = str(value or "europe").strip().lower()
        if region not in {"europe", "west", "east"}:
            region = "europe"
        if region == self._price_region:
            return
        self._price_region = region
        update_app_settings(loot_price_region=region)
        self.changed.emit()

    @Slot(int)
    def setBufferSeconds(self, value: int) -> None:
        seconds = min(600, max(0, int(value)))
        if seconds == self._buffer_seconds:
            return
        self._buffer_seconds = seconds
        update_app_settings(loot_buffer_seconds=seconds)
        self.changed.emit()

    @Slot(str, str)
    def setSelfAffiliation(self, guild_name: str, alliance_name: str) -> None:
        guild = str(guild_name or "").strip()
        alliance = str(alliance_name or "").strip()
        self._self_guild = guild
        self._self_alliance = alliance
        update_app_settings(loot_self_guild=guild, loot_self_alliance=alliance)
        if self._tracker is not None:
            self._tracker.set_self_affiliation(
                guild_name=guild or None,
                alliance_name=alliance or None,
            )
        self.changed.emit()

    @Slot()
    def refreshPrices(self) -> None:
        if self._market_service is None or self._session_store is None or self._pricing_running:
            return
        rows = list(self._stored_rows.values())
        priceable = [row for row in rows if str(row.get("item_id") or "") and not row.get("is_silver")]
        if not priceable:
            self._pricing_status = "no items"
            self.changed.emit()
            return
        item_ids = sorted({str(row["item_id"]) for row in priceable})
        qualities = sorted({int(row.get("quality") or 1) for row in priceable})
        self._pricing_running = True
        self._pricing_status = "refreshing"
        self.changed.emit()

        def worker() -> None:
            try:
                region = MarketRegion(self._price_region)
                records = self._market_service.get_prices(
                    region=region,
                    item_ids=item_ids,
                    locations=[self._price_city],
                    qualities=qualities,
                    allow_stale=True,
                    allow_cache=True,
                    allow_live=True,
                )
                payload = [
                    {
                        "item_id": record.item_id,
                        "city": record.city,
                        "quality": record.quality,
                        "market_unit": record.sell_price_min,
                        "liquidation_unit": record.buy_price_max,
                    }
                    for record in records
                ]
                source = str(getattr(self._market_service.last_prices_meta, "source", "market"))
                self.pricingReady.emit(payload, source)
            except Exception as exc:
                self.pricingReady.emit([], f"error: {exc}")

        threading.Thread(target=worker, daemon=True, name="loot-pricing").start()

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
            suggested_name="acd-loot-view.csv" if self._session_store is not None else "acd-loot-view.txt",
            file_filter="CSV Files (*.csv);;Text Files (*.txt);;All Files (*)",
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
        if self._session_store is not None:
            record = self._session_store.import_session(Path(path).stem, imported)
            self._selected_session_id = record.session_id
            self._imported_events = None
            self._imported_log_path = ""
            self._reload_from_store(force_changed=True)
            return str(Path(path).expanduser().resolve())
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
        if self._session_store is not None:
            self._reload_from_store(force_changed=True)
            return
        self._all_events = list(self._live_events)
        self._refresh_models()

    def update_from_tracker(self, tracker) -> None:
        self._tracker = tracker
        set_affiliation = getattr(tracker, "set_self_affiliation", None)
        if callable(set_affiliation):
            set_affiliation(
                guild_name=self._self_guild or None,
                alliance_name=self._self_alliance or None,
            )
        affiliation = getattr(tracker, "self_affiliation", None)
        if callable(affiliation):
            detected_guild, detected_alliance = affiliation()
            if not self._self_guild and detected_guild:
                self._self_guild = detected_guild
            if not self._self_alliance and detected_alliance:
                self._self_alliance = detected_alliance
        self._live_events = list(tracker.events(limit=self._history_limit))
        if self._session_store is not None:
            observation_source = getattr(tracker, "observations", None)
            observations = list(
                reversed(
                    observation_source(limit=50_000)
                    if callable(observation_source)
                    else tracker.events(limit=50_000)
                )
            )
            changed_observations: list[LootEvent] = []
            for event in observations:
                if not event.event_id:
                    continue
                signature = (
                    event.eligibility_reason,
                    event.looted_by.guild_name,
                    event.looted_by.alliance_name,
                    event.item.quality if event.item is not None else None,
                )
                if self._observation_versions.get(event.event_id) == signature:
                    continue
                self._observation_versions[event.event_id] = signature
                changed_observations.append(event)
            if changed_observations:
                self._session_store.sync_observations(changed_observations)
            now = time.time()
            if now - self._last_prune_at >= 300.0:
                self._session_store.prune_buffer()
                self._last_prune_at = now
            if changed_observations and self._imported_events is None:
                self._reload_from_store()
            return
        if self._imported_events is not None:
            return
        self._all_events = list(self._live_events)
        self._refresh_models()

    def _reload_from_store(self, *, force_changed: bool = False) -> None:
        if self._session_store is None:
            return
        self._refresh_session_list()
        active = self._session_store.active_session()
        if active is not None and not self._selected_session_id:
            self._selected_session_id = active.session_id
        selected = next(
            (
                session
                for session in self._session_store.list_sessions()
                if session.session_id == self._selected_session_id
            ),
            None,
        )
        self._session_active = bool(selected is not None and selected.status == "active")
        self._session_title = selected.title if selected is not None else "Live buffer"
        self._session_started_at = selected.started_at if selected is not None else 0.0
        self._session_ended_at = (
            float(selected.ended_at or 0.0) if selected is not None else 0.0
        )
        rows = self._session_store.loot_rows(
            session_id=selected.session_id if selected is not None else None,
            buffer_limit=max(2000, self._history_limit),
        )
        self._stored_rows = {str(row["event_id"]): row for row in rows}
        self._all_events = [_stored_row_to_event(row) for row in rows]
        self._pending_scope_count = self._session_store.pending_scope_count()
        self._refresh_models(force_changed=force_changed)
        if (
            selected is not None
            and rows
            and not self._pricing_running
            and time.time() - self._last_price_refresh_at >= 60.0
            and any(row.get("market_unit") is None for row in rows)
        ):
            self.refreshPrices()

    def _refresh_session_list(self) -> None:
        if self._session_store is None:
            return
        sessions = self._session_store.list_sessions()
        self._session_ids = [session.session_id for session in sessions]
        self._session_options = [
            f"{session.title} ({session.status})" for session in sessions
        ]

    @Slot(object, str)
    def _apply_price_results(self, records: object, source: str) -> None:
        self._pricing_running = False
        self._last_price_refresh_at = time.time()
        if self._session_store is None:
            return
        if str(source).startswith("error:"):
            self._pricing_status = str(source)
            self.changed.emit()
            return
        rows = records if isinstance(records, list) else []
        index = {
            (
                str(row.get("item_id") or ""),
                str(row.get("city") or ""),
                int(row.get("quality") or 1),
            ): row
            for row in rows
            if isinstance(row, dict)
        }
        priced = 0
        for event_id, row in list(self._stored_rows.items()):
            item_id = str(row.get("item_id") or "")
            if not item_id or bool(row.get("is_silver")):
                continue
            quality = int(row.get("quality") or 1)
            quote = index.get((item_id, self._price_city, quality))
            if quote is None:
                continue
            self._session_store.upsert_valuation(
                event_id,
                region=self._price_region,
                city=self._price_city,
                pricing_quality=quality,
                market_unit=int(quote.get("market_unit") or 0),
                liquidation_unit=int(quote.get("liquidation_unit") or 0),
                source=str(source or "market"),
                estimated=row.get("quality") is None,
            )
            priced += 1
        self._pricing_status = f"priced {priced}/{len(self._stored_rows)} from {source}"
        self._reload_from_store(force_changed=True)

    def _refresh_models(self, *, force_changed: bool = False) -> None:
        visible_events = [event for event in self._all_events if not event.is_silver]
        looter_options = _build_looter_options(visible_events)
        if self._looter_filter not in looter_options:
            self._looter_filter = "all"
        base_events = _filter_events(
            visible_events,
            search_query=self._search_query,
            source_filter=self._source_filter,
            source_name_filter=self._source_name_filter,
            looter_filter=self._looter_filter,
            category_filter=self._category_filter,
        )
        item_events = [event for event in base_events if not event.is_silver]
        filtered_events = list(item_events)
        display_events = _sort_loot_events(filtered_events, self._sort_order)
        rows = [
            _loot_event_to_row(event, stored=self._stored_rows.get(event.event_id))
            for event in display_events
        ]
        item_rows = [
            _loot_event_to_row(event, stored=self._stored_rows.get(event.event_id))
            for event in display_events
        ]
        export_rows = [
            _loot_event_to_row(event, stored=self._stored_rows.get(event.event_id))
            for event in filtered_events
        ]
        export_text = (
            _loot_rows_to_csv(list(reversed(export_rows)))
            if self._session_store is not None and self._imported_events is None
            else loot_events_to_txt(list(reversed(filtered_events)))
        )
        latest_summary = export_rows[0].summary if export_rows else ""
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
        total_market_value = sum(row.market_value for row in rows)
        total_liquidation_value = sum(row.liquidation_value for row in rows)
        outstanding_market_value = sum(
            row.market_unit * row.outstanding_quantity for row in rows
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
            or self._total_market_value != total_market_value
            or self._total_liquidation_value != total_liquidation_value
            or self._outstanding_market_value != outstanding_market_value
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
        self._total_market_value = total_market_value
        self._total_liquidation_value = total_liquidation_value
        self._outstanding_market_value = outstanding_market_value
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
    source_name_filter: str,
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
        source_name = _event_source_name(event)
        if source_name_filter and source_name != source_name_filter:
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
                    source_name,
                )
                if part
            ).lower()
            if query not in haystack:
                continue
        filtered.append(event)
    return filtered


_LOOT_TIER_RE = re.compile(r"^T(\d+)_", re.IGNORECASE)
_LOOT_ENCHANT_RE = re.compile(r"(?:@(\d+)|_LEVEL(\d+))(?:$|_)", re.IGNORECASE)


def _loot_item_tier(unique_name: str | None) -> tuple[int, int]:
    value = str(unique_name or "").strip()
    upper = value.upper()
    # Trash keeps its technical T-prefix in Albion data, but it is not gear and
    # must never outrank a real item in the "Highest tier" view.
    if upper.endswith("_TRASH") or upper.startswith(("QUESTITEM_", "UNIQUE_UNLOCK_")):
        return 0, 0
    tier_match = _LOOT_TIER_RE.match(value)
    if tier_match is None:
        return 0, 0
    tier = int(tier_match.group(1))
    enchant_match = _LOOT_ENCHANT_RE.search(value)
    enchant = 0
    if enchant_match is not None:
        enchant = int(enchant_match.group(1) or enchant_match.group(2) or 0)
    return tier, enchant


def _sort_loot_events(events: list[LootEvent], sort_order: str) -> list[LootEvent]:
    if sort_order == "tier_desc":
        def tier_key(event: LootEvent) -> tuple[int, int, float, str]:
            tier, enchant = _loot_item_tier(
                event.item.unique_name if event.item else None
            )
            return (
                -tier,
                -enchant,
                -(event.timestamp or 0.0),
                (event.item.display_name if event.item else "").lower(),
            )

        return sorted(
            events,
            key=tier_key,
        )
    if sort_order == "item_name":
        return sorted(
            events,
            key=lambda event: (
                (event.item.display_name if event.item else "").lower(),
                -(event.timestamp or 0.0),
            ),
        )
    return list(events)


def _event_source_name(event: LootEvent) -> str:
    if event.looted_from is not None:
        return event.looted_from.player_name
    return event.source_name or ""


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
            {
                "quantity": 0,
                "events": 0,
                "sublabel": row.looted_by_guild or row.looted_by_alliance or "",
                "market": 0,
                "liquidation": 0,
                "outstanding": 0,
            },
        )
        entry["quantity"] = int(entry["quantity"]) + row.quantity
        entry["events"] = int(entry["events"]) + 1
        entry["market"] = int(entry["market"]) + row.market_value
        entry["liquidation"] = int(entry["liquidation"]) + row.liquidation_value
        entry["outstanding"] = int(entry["outstanding"]) + (
            row.market_unit * row.outstanding_quantity
        )
        for key, value in (
            ("returned", row.returned_quantity),
            ("sold", row.sold_quantity),
            ("lost", row.lost_quantity),
            ("allowed", row.allowed_quantity),
            ("unreturned", row.unreturned_quantity),
        ):
            entry[key] = int(entry.get(key, 0)) + value
    ordered = sorted(
        stats.items(),
        key=lambda item: (-int(item[1]["market"]), -int(item[1]["quantity"]), item[0].lower()),
    )
    return [
        LootAggregateRow(
            label=name,
            sublabel=_player_settlement_sublabel(values),
            icon_url="",
            quantity=int(values["quantity"]),
            event_count=int(values["events"]),
            market_value=int(values["market"]),
            liquidation_value=int(values["liquidation"]),
            outstanding_value=int(values["outstanding"]),
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


def _loot_event_to_row(
    event: LootEvent, *, stored: dict[str, object] | None = None
) -> LootRow:
    item_name = ""
    item_id = ""
    if event.item is not None:
        item_name = event.item.display_name
        item_id = event.item.unique_name or ""
    source_name = event.source_name or ""
    if event.looted_from is not None:
        source_name = event.looted_from.player_name
    stored = stored or {}
    quality = int(stored.get("quality") or (event.item.quality if event.item is not None else 0) or 0)
    market_unit = int(stored.get("market_unit") or 0)
    liquidation_unit = int(stored.get("liquidation_unit") or 0)
    quantity = int(event.quantity)
    outstanding = int(stored.get("outstanding_quantity", quantity) or 0)
    settlements = stored.get("settlements")
    settlement_counts = settlements if isinstance(settlements, dict) else {}
    item_tier, item_enchant = _loot_item_tier(item_id)
    item_tier_text = (
        f"T{item_tier}.{item_enchant}" if item_tier and item_enchant
        else (f"T{item_tier}" if item_tier else "")
    )
    return LootRow(
        timestamp_text=_format_timestamp(event.timestamp),
        looted_by_name=event.looted_by.player_name,
        looted_by_guild=event.looted_by.guild_name or "",
        looted_by_alliance=event.looted_by.alliance_name or "",
        item_id=item_id,
        item_name=item_name,
        icon_url=_loot_icon_url(item_id),
        category=_item_category(item_id),
        quantity=quantity,
        source_name=source_name,
        source_kind=event.source_kind,
        is_silver=bool(event.is_silver),
        summary=_format_summary(event, item_name=item_name, source_name=source_name),
        event_id=event.event_id,
        quality=quality,
        quality_text=f"Q{quality}" if quality else "Q?",
        eligibility_reason=event.eligibility_reason,
        market_unit=market_unit,
        liquidation_unit=liquidation_unit,
        market_value=market_unit * quantity,
        liquidation_value=liquidation_unit * quantity,
        value_estimated=bool(stored.get("estimated")) or quality == 0,
        settlement_status=str(stored.get("settlement_status") or "pending"),
        outstanding_quantity=outstanding,
        returned_quantity=int(settlement_counts.get("returned", 0)),
        sold_quantity=int(settlement_counts.get("sold", 0)),
        lost_quantity=int(settlement_counts.get("lost", 0)),
        allowed_quantity=int(settlement_counts.get("allowed", 0)),
        unreturned_quantity=int(settlement_counts.get("unreturned", 0)),
        excluded_quantity=int(settlement_counts.get("excluded", 0)),
        actual_sold_value=int(stored.get("actual_sold_value") or 0),
        item_tier=item_tier,
        item_enchant=item_enchant,
        item_tier_text=item_tier_text,
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


def _stored_row_to_event(row: dict[str, object]) -> LootEvent:
    source_name = str(row.get("source_name") or "")
    source_kind = str(row.get("source_kind") or "unknown")
    item_id = str(row.get("item_id") or "")
    item_name = str(row.get("item_name") or item_id or "Unknown item")
    item = LootItemRef(
        item_num_id=int(row["item_num_id"]) if row.get("item_num_id") is not None else None,
        unique_name=item_id or None,
        display_name=item_name,
        quality=int(row["quality"]) if row.get("quality") is not None else None,
    )
    looted_from = (
        LootPlayer(player_name=source_name)
        if source_kind == "player" and source_name
        else None
    )
    return LootEvent(
        timestamp=float(row.get("timestamp") or 0.0),
        looted_by=LootPlayer(
            player_name=str(row.get("looter_name") or "Unknown"),
            guild_name=str(row.get("looter_guild") or "") or None,
            alliance_name=str(row.get("looter_alliance") or "") or None,
        ),
        looted_from=looted_from,
        source_name=source_name or None,
        source_kind=source_kind,
        item=item,
        quantity=int(row.get("quantity") or 0),
        is_silver=bool(row.get("is_silver")),
        raw_event_code=int(row.get("raw_event_code") or 0),
        raw_subtype=int(row.get("raw_subtype") or 0),
        event_id=str(row.get("event_id") or ""),
        eligibility_reason=str(row.get("eligibility_reason") or "unknown"),
    )


def _loot_rows_to_csv(rows: list[LootRow]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "time",
            "looter",
            "guild",
            "alliance",
            "item_id",
            "item_name",
            "quality",
            "quantity",
            "source",
            "eligibility",
            "market_unit",
            "market_value",
            "liquidation_unit",
            "liquidation_value",
            "settlement_status",
            "outstanding_quantity",
            "returned_quantity",
            "sold_quantity",
            "lost_quantity",
            "allowed_quantity",
            "unreturned_quantity",
            "excluded_quantity",
            "actual_sold_value",
            "estimated",
            "event_id",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.timestamp_text,
                row.looted_by_name,
                row.looted_by_guild,
                row.looted_by_alliance,
                row.item_id,
                row.item_name,
                row.quality_text,
                row.quantity,
                row.source_name,
                row.eligibility_reason,
                row.market_unit,
                row.market_value,
                row.liquidation_unit,
                row.liquidation_value,
                row.settlement_status,
                row.outstanding_quantity,
                row.returned_quantity,
                row.sold_quantity,
                row.lost_quantity,
                row.allowed_quantity,
                row.unreturned_quantity,
                row.excluded_quantity,
                row.actual_sold_value,
                "yes" if row.value_estimated else "no",
                row.event_id,
            ]
        )
    return buffer.getvalue()


def _player_settlement_sublabel(values: dict[str, int | str]) -> str:
    base = str(values.get("sublabel") or "")
    parts = [
        f"returned {int(values.get('returned', 0))}",
        f"sold {int(values.get('sold', 0))}",
        f"lost {int(values.get('lost', 0))}",
        f"unreturned {int(values.get('unreturned', 0))}",
    ]
    if not any(int(values.get(key, 0)) for key in ("returned", "sold", "lost", "unreturned")):
        return base
    detail = " | ".join(parts)
    return f"{base} | {detail}" if base else detail


def _format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, seconds_part = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds_part:02d}"
    return f"{minutes:02d}:{seconds_part:02d}"


def _loot_icon_url(item_id: str) -> str:
    unique = str(item_id or "").strip()
    if not unique or unique == "SILVER":
        return ""
    upper = unique.upper()
    if upper.startswith("UNIQUE_UNLOCK_SKIN_"):
        unique = unique[len("UNIQUE_UNLOCK_") :]
        upper = unique.upper()
    if upper.endswith("_TRASH") or upper.startswith(("QUESTITEM_", "UNIQUE_UNLOCK_")):
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
