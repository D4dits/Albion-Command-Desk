from __future__ import annotations

import csv
import io
import logging
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Property, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFileDialog

from albion_dps.market.flipper import (
    BLACK_MARKET_CITY,
    DEFAULT_BUY_FRESHNESS_MINUTES,
    DEFAULT_SELL_FRESHNESS_MINUTES,
    FLIP_QUALITIES,
    FlipCandidate,
    FlipOpportunity,
    build_flip_opportunities,
    collect_flip_candidates,
)
from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.models import MarketRegion
from albion_dps.market.price_store import DEFAULT_QUOTE_MAX_AGE_SECONDS, LocalMarketPriceStore
from albion_dps.market.service import MarketDataService
from albion_dps.qt.market.recipe_ops import item_id_query_candidates


SOURCE_CITIES = ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
SAFE_SOURCE_CITY = "Caerleon"
DEFAULT_QUERY_ID_LIMIT = 1200
BROAD_QUERY_ID_LIMIT = 1200


@dataclass(frozen=True)
class FlipRow:
    row_key: str
    opportunity: FlipOpportunity
    checked: bool = False
    hidden: bool = False


class FlipperResultsModel(QAbstractListModel):
    RowKeyRole = Qt.UserRole + 1
    ItemIdRole = Qt.UserRole + 2
    ItemNameRole = Qt.UserRole + 3
    TierRole = Qt.UserRole + 4
    EnchantRole = Qt.UserRole + 5
    QualityRole = Qt.UserRole + 6
    SourceCityRole = Qt.UserRole + 7
    TargetCityRole = Qt.UserRole + 8
    SourceSellPriceRole = Qt.UserRole + 9
    SourceAgeRole = Qt.UserRole + 10
    TargetBuyPriceRole = Qt.UserRole + 11
    TargetAgeRole = Qt.UserRole + 12
    TaxValueRole = Qt.UserRole + 13
    BufferValueRole = Qt.UserRole + 14
    NetProfitRole = Qt.UserRole + 15
    RoiPercentRole = Qt.UserRole + 16
    ValidRole = Qt.UserRole + 17
    StaleReasonRole = Qt.UserRole + 18
    CheckedRole = Qt.UserRole + 19

    def __init__(self) -> None:
        super().__init__()
        self._items: list[FlipRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        opp = item.opportunity
        if role == self.RowKeyRole:
            return item.row_key
        if role == self.ItemIdRole:
            return opp.item_id
        if role == self.ItemNameRole:
            return opp.item_name
        if role == self.TierRole:
            return opp.tier
        if role == self.EnchantRole:
            return opp.enchant
        if role == self.QualityRole:
            return opp.quality
        if role == self.SourceCityRole:
            return opp.source_city
        if role == self.TargetCityRole:
            return opp.target_city
        if role == self.SourceSellPriceRole:
            return opp.source_sell_price
        if role == self.SourceAgeRole:
            return opp.source_age_text
        if role == self.TargetBuyPriceRole:
            return opp.target_buy_price
        if role == self.TargetAgeRole:
            return opp.target_age_text
        if role == self.TaxValueRole:
            return opp.tax_value
        if role == self.BufferValueRole:
            return opp.buffer_value
        if role == self.NetProfitRole:
            return opp.net_profit
        if role == self.RoiPercentRole:
            return opp.roi_percent
        if role == self.ValidRole:
            return opp.valid
        if role == self.StaleReasonRole:
            return opp.stale_reason
        if role == self.CheckedRole:
            return item.checked
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.RowKeyRole: b"rowKey",
            self.ItemIdRole: b"itemId",
            self.ItemNameRole: b"itemName",
            self.TierRole: b"tier",
            self.EnchantRole: b"enchant",
            self.QualityRole: b"quality",
            self.SourceCityRole: b"sourceCity",
            self.TargetCityRole: b"targetCity",
            self.SourceSellPriceRole: b"sourceSellPrice",
            self.SourceAgeRole: b"sourceAgeText",
            self.TargetBuyPriceRole: b"blackMarketBuyPrice",
            self.TargetAgeRole: b"blackMarketAgeText",
            self.TaxValueRole: b"taxValue",
            self.BufferValueRole: b"bufferValue",
            self.NetProfitRole: b"netProfit",
            self.RoiPercentRole: b"roiPercent",
            self.ValidRole: b"valid",
            self.StaleReasonRole: b"staleReason",
            self.CheckedRole: b"checked",
        }

    def rows(self) -> list[FlipRow]:
        return list(self._items)

    def set_items(self, rows: list[FlipRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()

    def set_checked(self, row_key: str, checked: bool) -> bool:
        for idx, row in enumerate(self._items):
            if row.row_key != row_key:
                continue
            if row.checked == bool(checked):
                return False
            self._items[idx] = FlipRow(row_key=row.row_key, opportunity=row.opportunity, checked=bool(checked), hidden=row.hidden)
            model_index = self.index(idx, 0)
            self.dataChanged.emit(model_index, model_index, [self.CheckedRole])
            return True
        return False


class MarketFlipperState(QObject):
    filtersChanged = Signal()
    resultsChanged = Signal()
    refreshChanged = Signal()
    summaryChanged = Signal()

    def __init__(
        self,
        *,
        service: MarketDataService | None = None,
        price_store: LocalMarketPriceStore | None = None,
        catalog: RecipeCatalog | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._price_store = price_store or getattr(service, "price_store", None)
        self._catalog = catalog or RecipeCatalog.from_default()
        self._log = logger or logging.getLogger(__name__)
        self._all_candidates = collect_flip_candidates(self._catalog)
        self._results_model = FlipperResultsModel()
        self._region = MarketRegion.EUROPE
        self._source_city = SAFE_SOURCE_CITY
        self._query_id_limit = DEFAULT_QUERY_ID_LIMIT
        self._broad_query_id_limit = BROAD_QUERY_ID_LIMIT
        self._last_candidate_total = 0
        self._quality = 1
        self._search_query = ""
        self._min_profit = 10000.0
        self._min_roi_percent = 5.0
        self._risk_buffer_percent = 0.0
        self._sale_tax_percent = 4.0
        self._sell_freshness_minutes = DEFAULT_SELL_FRESHNESS_MINUTES
        self._buy_freshness_minutes = DEFAULT_BUY_FRESHNESS_MINUTES
        self._refresh_in_progress = False
        self._refresh_status_text = "Refresh all opportunities or enter an item family to narrow the scan."
        self._prices_source = "none"
        self._checked_row_keys: set[str] = set()
        self._hidden_row_keys: set[str] = set()
        self._last_all_count = 0
        self._last_valid_count = 0
        self._last_missing_count = 0
        self._last_selected_total_profit = 0.0
        self._result_queue: queue.Queue[tuple[list[FlipOpportunity], str, str] | Exception] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(50)
        self._poll_timer.timeout.connect(self._poll_refresh_result)

    @Property(str, notify=filtersChanged)
    def region(self) -> str:
        return self._region.value

    @Property(str, notify=filtersChanged)
    def sourceCity(self) -> str:
        return self._effective_source_city()

    @Property(int, notify=filtersChanged)
    def quality(self) -> int:
        return self._quality

    @Property(float, notify=filtersChanged)
    def minProfit(self) -> float:
        return self._min_profit

    @Property(float, notify=filtersChanged)
    def minRoiPercent(self) -> float:
        return self._min_roi_percent

    @Property(float, notify=filtersChanged)
    def riskBufferPercent(self) -> float:
        return self._risk_buffer_percent

    @Property(float, notify=filtersChanged)
    def saleTaxPercent(self) -> float:
        return self._sale_tax_percent

    @Property(str, notify=filtersChanged)
    def searchQuery(self) -> str:
        return self._search_query

    @Property(int, constant=True)
    def sellFreshnessMinutes(self) -> int:
        return self._sell_freshness_minutes

    @Property(int, constant=True)
    def buyFreshnessMinutes(self) -> int:
        return self._buy_freshness_minutes

    @Property(bool, notify=refreshChanged)
    def refreshInProgress(self) -> bool:
        return self._refresh_in_progress

    @Property(str, notify=refreshChanged)
    def refreshStatusText(self) -> str:
        return self._refresh_status_text

    @Property(str, notify=refreshChanged)
    def pricesSource(self) -> str:
        return self._prices_source

    @Property(QObject, notify=resultsChanged)
    def resultsModel(self) -> QObject:
        return self._results_model

    @Property(int, notify=summaryChanged)
    def resultsCount(self) -> int:
        return self._last_all_count

    @Property(int, notify=summaryChanged)
    def validCount(self) -> int:
        return self._last_valid_count

    @Property(int, notify=summaryChanged)
    def missingCount(self) -> int:
        return self._last_missing_count

    @Property(float, notify=summaryChanged)
    def selectedTotalProfit(self) -> float:
        return self._last_selected_total_profit

    @Slot(str)
    def setRegion(self, value: str) -> None:
        try:
            region = MarketRegion(str(value).strip().lower())
        except ValueError:
            return
        if region == self._region:
            return
        self._region = region
        self.filtersChanged.emit()

    @Slot(str)
    def setSourceCity(self, value: str) -> None:
        city = str(value or "").strip()
        if city not in SOURCE_CITIES:
            return
        if city == self._source_city:
            return
        self._source_city = city
        self.filtersChanged.emit()

    @Slot(int)
    def setQuality(self, value: int) -> None:
        quality = max(1, min(5, int(value)))
        if quality == self._quality:
            return
        self._quality = quality
        self.filtersChanged.emit()

    @Slot(str)
    def setSearchQuery(self, value: str) -> None:
        query = str(value or "").strip()
        if query == self._search_query:
            return
        self._search_query = query
        self.filtersChanged.emit()

    @Slot(float)
    @Slot(str)
    def setMinProfit(self, value: Any) -> None:
        parsed = _to_float(value, default=self._min_profit)
        parsed = max(0.0, parsed)
        if parsed == self._min_profit:
            return
        self._min_profit = parsed
        self.filtersChanged.emit()

    @Slot(float)
    @Slot(str)
    def setMinRoiPercent(self, value: Any) -> None:
        parsed = max(0.0, _to_float(value, default=self._min_roi_percent))
        if parsed == self._min_roi_percent:
            return
        self._min_roi_percent = parsed
        self.filtersChanged.emit()

    @Slot(float)
    @Slot(str)
    def setRiskBufferPercent(self, value: Any) -> None:
        parsed = max(0.0, _to_float(value, default=self._risk_buffer_percent))
        if parsed == self._risk_buffer_percent:
            return
        self._risk_buffer_percent = parsed
        self.filtersChanged.emit()

    @Slot(float)
    @Slot(str)
    def setSaleTaxPercent(self, value: Any) -> None:
        parsed = max(0.0, _to_float(value, default=self._sale_tax_percent))
        if parsed == self._sale_tax_percent:
            return
        self._sale_tax_percent = parsed
        self.filtersChanged.emit()

    @Slot()
    def refreshFlips(self) -> None:
        if self._refresh_in_progress:
            return
        if self._service is None and self._price_store is None:
            self._refresh_status_text = "Market data is not available."
            self._prices_source = "error"
            self.refreshChanged.emit()
            return
        candidates = self._filtered_candidates()
        if not candidates:
            self._apply_opportunities([], source="none", status="No matching item candidates.")
            return
        self._refresh_in_progress = True
        self._prices_source = "loading"
        suffix = ""
        if self._last_candidate_total > len(candidates):
            suffix = f" of {self._last_candidate_total}; use search for a focused full-family scan"
        scan_label = "broad market scan" if not self._search_query.strip() else "focused scan"
        self._refresh_status_text = f"Refreshing {scan_label}: {len(candidates)}{suffix} item candidates..."
        self.refreshChanged.emit()
        self._worker = threading.Thread(
            target=self._run_refresh_worker,
            args=(candidates, self._region, self._effective_source_city(), self._quality, scan_label),
            daemon=True,
        )
        self._worker.start()
        self._poll_timer.start()

    @Slot(str, bool)
    def setRowChecked(self, row_key: str, checked: bool) -> None:
        key = str(row_key or "")
        if not key:
            return
        if checked:
            self._checked_row_keys.add(key)
        else:
            self._checked_row_keys.discard(key)
        if self._results_model.set_checked(key, checked):
            self._recompute_summary()

    @Slot(result=bool)
    def copySelectedCsv(self) -> bool:
        payload = self._selected_csv()
        if not payload:
            return False
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return False
        clipboard.setText(payload)
        return True

    @Slot(result=str)
    def exportSelectedCsvInteractive(self) -> str:
        payload = self._selected_csv(include_all_if_none=True)
        if not payload:
            return ""
        path, _ = QFileDialog.getSaveFileName(
            None,
            "Export Market Flipper CSV",
            str(Path("market_flips.csv")),
            "CSV files (*.csv);;All files (*)",
        )
        if not path:
            return ""
        Path(path).write_text(payload, encoding="utf-8")
        return path

    def _run_refresh_worker(
        self,
        candidates: list[FlipCandidate],
        region: MarketRegion,
        source_city: str,
        quality: int,
        scan_label: str,
    ) -> None:
        try:
            query_ids = _expanded_query_ids(candidates)
            price_index = {}
            source = "none"
            if self._price_store is not None:
                price_index = self._price_store.get_price_index(
                    region=region,
                    item_ids=query_ids,
                    locations=[source_city, BLACK_MARKET_CITY],
                    qualities=list(FLIP_QUALITIES),
                    max_age_seconds=DEFAULT_QUOTE_MAX_AGE_SECONDS,
                )
                source = "local_db"
            if not price_index and self._price_store is None and self._service is not None:
                price_index = self._service.get_price_index(
                    region=region,
                    item_ids=query_ids,
                    locations=[source_city, BLACK_MARKET_CITY],
                    qualities=list(FLIP_QUALITIES),
                    ttl_seconds=30.0,
                    allow_stale=False,
                    allow_cache=True,
                    allow_live=True,
                )
                source = self._service.last_prices_meta.source
            rows = build_flip_opportunities(
                candidates=candidates,
                price_index=price_index,
                source_city=source_city,
                quality=quality,
                sale_tax_percent=self._sale_tax_percent,
                risk_buffer_percent=self._risk_buffer_percent,
                min_profit=self._min_profit,
                min_roi_percent=self._min_roi_percent,
                sell_freshness_minutes=self._sell_freshness_minutes,
                buy_freshness_minutes=self._buy_freshness_minutes,
                item_id_candidates=item_id_query_candidates,
            )
            if source == "local_db":
                rows = [row for row in rows if row.source_sell_price > 0 or row.target_buy_price > 0]
            status = f"{len(rows)} flips checked ({scan_label}) from {source_city} to Black Market. Source: {source}."
            self._result_queue.put((rows, source, status))
        except Exception as exc:  # pragma: no cover - surfaced through UI
            self._log.exception("Market flipper refresh failed")
            self._result_queue.put(exc)

    def _poll_refresh_result(self) -> None:
        try:
            result = self._result_queue.get_nowait()
        except queue.Empty:
            return
        self._poll_timer.stop()
        self._refresh_in_progress = False
        if isinstance(result, Exception):
            self._prices_source = "error"
            self._refresh_status_text = f"Refresh failed: {result}"
            self.refreshChanged.emit()
            return
        rows, source, status = result
        self._apply_opportunities(rows, source=source, status=status)

    def _apply_opportunities(self, rows: list[FlipOpportunity], *, source: str, status: str) -> None:
        model_rows = [
            FlipRow(
                row_key=_row_key(row),
                opportunity=row,
                checked=_row_key(row) in self._checked_row_keys,
            )
            for row in rows
        ]
        self._results_model.set_items(model_rows)
        self._prices_source = source
        self._refresh_status_text = status
        self.resultsChanged.emit()
        self.refreshChanged.emit()
        self._recompute_summary()

    def _recompute_summary(self) -> None:
        rows = self._results_model.rows()
        self._last_all_count = len(rows)
        self._last_valid_count = sum(1 for row in rows if row.opportunity.valid)
        self._last_missing_count = sum(1 for row in rows if not row.opportunity.valid)
        self._last_selected_total_profit = sum(
            row.opportunity.net_profit for row in rows if row.checked and row.opportunity.valid
        )
        self.summaryChanged.emit()

    def _filtered_candidates(self) -> list[FlipCandidate]:
        query = self._search_query.lower()
        out: list[FlipCandidate] = []
        for candidate in self._all_candidates:
            item = candidate.item
            haystack = f"{item.display_name} {item.unique_name}".lower()
            if query and query not in haystack:
                continue
            tier = int(item.tier or 0)
            if tier and tier < 4:
                continue
            out.append(candidate)
        self._last_candidate_total = len(out)
        if query:
            if self._price_store is not None:
                return out
            return self._limit_candidates_by_query_ids(out, limit=self._query_id_limit)
        if self._price_store is not None:
            return self._balanced_broad_candidates(out, limit=None)
        return self._balanced_broad_candidates(out)

    def _effective_source_city(self) -> str:
        return self._source_city if self._source_city in SOURCE_CITIES else SAFE_SOURCE_CITY

    def _balanced_broad_candidates(
        self,
        candidates: list[FlipCandidate],
        *,
        limit: int | None = BROAD_QUERY_ID_LIMIT,
    ) -> list[FlipCandidate]:
        groups: dict[tuple[int, int], list[FlipCandidate]] = {}
        for candidate in candidates:
            item = candidate.item
            key = (int(item.tier or 0), int(item.enchantment or 0))
            groups.setdefault(key, []).append(candidate)

        ordered: list[FlipCandidate] = []
        keys = sorted(groups)
        index = 0
        while keys:
            next_keys: list[tuple[int, int]] = []
            for key in keys:
                bucket = groups[key]
                if index < len(bucket):
                    ordered.append(bucket[index])
                if index + 1 < len(bucket):
                    next_keys.append(key)
            keys = next_keys
            index += 1
        if limit is None:
            return ordered
        return self._limit_candidates_by_query_ids(ordered, limit=limit)

    def _limit_candidates_by_query_ids(self, candidates: list[FlipCandidate], *, limit: int) -> list[FlipCandidate]:
        limited: list[FlipCandidate] = []
        query_ids: set[str] = set()
        for candidate in candidates:
            expanded = [item_id for item_id in item_id_query_candidates(candidate.item.unique_name) if item_id]
            new_ids = [item_id for item_id in expanded if item_id not in query_ids]
            if limited and len(query_ids) + len(new_ids) > int(limit):
                break
            limited.append(candidate)
            query_ids.update(new_ids)
        return limited

    def _selected_csv(self, *, include_all_if_none: bool = False) -> str:
        rows = [row for row in self._results_model.rows() if row.checked and row.opportunity.valid]
        if include_all_if_none and not rows:
            rows = [row for row in self._results_model.rows() if row.opportunity.valid]
        if not rows:
            return ""
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            [
                "item_id",
                "item_name",
                "source_city",
                "source_sell_price",
                "source_age",
                "black_market_buy_price",
                "black_market_age",
                "tax",
                "buffer",
                "net_profit",
                "roi_percent",
            ]
        )
        for row in rows:
            opp = row.opportunity
            writer.writerow(
                [
                    opp.item_id,
                    opp.item_name,
                    opp.source_city,
                    round(opp.source_sell_price),
                    opp.source_age_text,
                    round(opp.target_buy_price),
                    opp.target_age_text,
                    round(opp.tax_value),
                    round(opp.buffer_value),
                    round(opp.net_profit),
                    round(opp.roi_percent, 2),
                ]
            )
        return output.getvalue()


def _expanded_query_ids(candidates: list[FlipCandidate]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for candidate in candidates:
        for item_id in item_id_query_candidates(candidate.item.unique_name):
            if item_id in seen:
                continue
            seen.add(item_id)
            out.append(item_id)
    return out


def _row_key(row: FlipOpportunity) -> str:
    return f"{row.item_id}|{row.quality}|{row.source_city}|{row.target_city}"


def _to_float(value: Any, *, default: float) -> float:
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return float(default)
