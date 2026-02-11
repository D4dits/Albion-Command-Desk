from __future__ import annotations

import csv
import io
import json
import logging
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Property, Qt, Signal, Slot

from albion_dps.market.aod_client import MarketPriceRecord, REGION_HOSTS
from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.engine import (
    build_craft_run,
    compute_batch_profit,
    compute_output_valuations,
    compute_run_profit,
    effective_return_fraction,
)
from albion_dps.market.models import (
    CraftSetup,
    MarketRegion,
    PriceType,
    ProfitBreakdown,
    Recipe,
)
from albion_dps.market.planner import build_selling_entries, build_shopping_entries
from albion_dps.market.service import MarketDataService
from albion_dps.market.setup import sanitized_setup, validate_setup


@dataclass(frozen=True)
class InputPreviewRow:
    item_id: str
    item: str
    quantity: float
    city: str
    price_type: str
    price_age_text: str
    manual_price: int
    unit_price: float
    total_cost: float


class MarketInputsModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    PriceAgeRole = Qt.UserRole + 6
    ManualPriceRole = Qt.UserRole + 7
    UnitPriceRole = Qt.UserRole + 8
    TotalCostRole = Qt.UserRole + 9

    def __init__(self) -> None:
        super().__init__()
        self._items: list[InputPreviewRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemRole:
            return item.item
        if role == self.QuantityRole:
            return item.quantity
        if role == self.CityRole:
            return item.city
        if role == self.PriceTypeRole:
            return item.price_type
        if role == self.PriceAgeRole:
            return item.price_age_text
        if role == self.ManualPriceRole:
            return item.manual_price
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.TotalCostRole:
            return item.total_cost
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.PriceAgeRole: b"priceAgeText",
            self.ManualPriceRole: b"manualPrice",
            self.UnitPriceRole: b"unitPrice",
            self.TotalCostRole: b"totalCost",
        }

    def set_items(self, rows: list[InputPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class OutputPreviewRow:
    item_id: str
    item: str
    quantity: float
    city: str
    price_type: str
    manual_price: int
    unit_price: float
    total_value: float
    fee_value: float
    tax_value: float
    net_value: float


class MarketOutputsModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    ManualPriceRole = Qt.UserRole + 6
    UnitPriceRole = Qt.UserRole + 7
    TotalValueRole = Qt.UserRole + 8
    FeeValueRole = Qt.UserRole + 9
    TaxValueRole = Qt.UserRole + 10
    NetValueRole = Qt.UserRole + 11

    def __init__(self) -> None:
        super().__init__()
        self._items: list[OutputPreviewRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemRole:
            return item.item
        if role == self.QuantityRole:
            return item.quantity
        if role == self.CityRole:
            return item.city
        if role == self.PriceTypeRole:
            return item.price_type
        if role == self.ManualPriceRole:
            return item.manual_price
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.TotalValueRole:
            return item.total_value
        if role == self.FeeValueRole:
            return item.fee_value
        if role == self.TaxValueRole:
            return item.tax_value
        if role == self.NetValueRole:
            return item.net_value
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.ManualPriceRole: b"manualPrice",
            self.UnitPriceRole: b"unitPrice",
            self.TotalValueRole: b"totalValue",
            self.FeeValueRole: b"feeValue",
            self.TaxValueRole: b"taxValue",
            self.NetValueRole: b"netValue",
        }

    def set_items(self, rows: list[OutputPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class ShoppingPreviewRow:
    item_id: str
    item: str
    quantity: float
    city: str
    price_type: str
    unit_price: float
    total_cost: float


class MarketShoppingModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    UnitPriceRole = Qt.UserRole + 6
    TotalCostRole = Qt.UserRole + 7

    def __init__(self) -> None:
        super().__init__()
        self._items: list[ShoppingPreviewRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemRole:
            return item.item
        if role == self.QuantityRole:
            return item.quantity
        if role == self.CityRole:
            return item.city
        if role == self.PriceTypeRole:
            return item.price_type
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.TotalCostRole:
            return item.total_cost
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.UnitPriceRole: b"unitPrice",
            self.TotalCostRole: b"totalCost",
        }

    def set_items(self, rows: list[ShoppingPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class SellingPreviewRow:
    item_id: str
    item: str
    quantity: float
    city: str
    price_type: str
    unit_price: float
    total_value: float


class MarketSellingModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    UnitPriceRole = Qt.UserRole + 6
    TotalValueRole = Qt.UserRole + 7

    def __init__(self) -> None:
        super().__init__()
        self._items: list[SellingPreviewRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemRole:
            return item.item
        if role == self.QuantityRole:
            return item.quantity
        if role == self.CityRole:
            return item.city
        if role == self.PriceTypeRole:
            return item.price_type
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.TotalValueRole:
            return item.total_value
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.UnitPriceRole: b"unitPrice",
            self.TotalValueRole: b"totalValue",
        }

    def set_items(self, rows: list[SellingPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class ResultItemRow:
    item_id: str
    item: str
    city: str
    quantity: float
    unit_price: float
    revenue: float
    allocated_cost: float
    fee_value: float
    tax_value: float
    profit: float
    margin_percent: float
    demand_proxy: float


class MarketResultsItemsModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    CityRole = Qt.UserRole + 3
    QuantityRole = Qt.UserRole + 4
    UnitPriceRole = Qt.UserRole + 5
    RevenueRole = Qt.UserRole + 6
    CostRole = Qt.UserRole + 7
    FeeRole = Qt.UserRole + 8
    TaxRole = Qt.UserRole + 9
    ProfitRole = Qt.UserRole + 10
    MarginRole = Qt.UserRole + 11
    DemandRole = Qt.UserRole + 12

    def __init__(self) -> None:
        super().__init__()
        self._items: list[ResultItemRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemRole:
            return item.item
        if role == self.CityRole:
            return item.city
        if role == self.QuantityRole:
            return item.quantity
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.RevenueRole:
            return item.revenue
        if role == self.CostRole:
            return item.allocated_cost
        if role == self.FeeRole:
            return item.fee_value
        if role == self.TaxRole:
            return item.tax_value
        if role == self.ProfitRole:
            return item.profit
        if role == self.MarginRole:
            return item.margin_percent
        if role == self.DemandRole:
            return item.demand_proxy
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.ItemRole: b"item",
            self.CityRole: b"city",
            self.QuantityRole: b"quantity",
            self.UnitPriceRole: b"unitPrice",
            self.RevenueRole: b"revenue",
            self.CostRole: b"cost",
            self.FeeRole: b"feeValue",
            self.TaxRole: b"taxValue",
            self.ProfitRole: b"profit",
            self.MarginRole: b"marginPercent",
            self.DemandRole: b"demandProxy",
        }

    def set_items(self, rows: list[ResultItemRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class BreakdownRow:
    label: str
    value: float


class MarketBreakdownModel(QAbstractListModel):
    LabelRole = Qt.UserRole + 1
    ValueRole = Qt.UserRole + 2

    def __init__(self) -> None:
        super().__init__()
        self._items: list[BreakdownRow] = []

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
        if role == self.ValueRole:
            return item.value
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.LabelRole: b"label",
            self.ValueRole: b"value",
        }

    def set_items(self, rows: list[BreakdownRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class RecipeOptionRow:
    recipe_id: str
    display_name: str
    tier: int
    enchant: int


@dataclass(frozen=True)
class RecipeFilter:
    terms: tuple[str, ...]
    tier: int | None
    enchant: int | None


_RECIPE_TIER_ENCHANT_RE = re.compile(r"\b(?:t)?(?P<tier>[1-8])(?:[.\-\/](?P<ench>[0-4]))?\b", re.IGNORECASE)
_TIER_PREFIX_RE = re.compile(r"^T(?P<tier>\d+)_(?P<rest>.+)$", re.IGNORECASE)
_LEVEL_SUFFIX_RE = re.compile(r"_LEVEL\d+$", re.IGNORECASE)

_ITEM_ID_WORD_ALIASES: dict[str, str] = {
    "ARTEFACT": "Artifact",
    "METALBAR": "Metal Bar",
    "OFFHAND": "Off Hand",
    "QUARTERSTAFF": "Quarterstaff",
    "SHAPESHIFTERSTAFF": "Shapeshifter Staff",
    "ARCANESTAFF": "Arcane Staff",
    "CURSEDSTAFF": "Cursed Staff",
    "FIRESTAFF": "Fire Staff",
    "FROSTSTAFF": "Frost Staff",
    "HOLYSTAFF": "Holy Staff",
    "NATURESTAFF": "Nature Staff",
}


class RecipeOptionsModel(QAbstractListModel):
    RecipeIdRole = Qt.UserRole + 1
    DisplayNameRole = Qt.UserRole + 2
    TierRole = Qt.UserRole + 3
    EnchantRole = Qt.UserRole + 4

    def __init__(self) -> None:
        super().__init__()
        self._all_items: list[RecipeOptionRow] = []
        self._items: list[RecipeOptionRow] = []
        self._filter = RecipeFilter(terms=(), tier=None, enchant=None)

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.RecipeIdRole:
            return item.recipe_id
        if role == self.DisplayNameRole:
            return item.display_name
        if role == self.TierRole:
            return item.tier
        if role == self.EnchantRole:
            return item.enchant
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.RecipeIdRole: b"recipeId",
            self.DisplayNameRole: b"displayName",
            self.TierRole: b"tier",
            self.EnchantRole: b"enchant",
        }

    def set_items(self, rows: list[RecipeOptionRow]) -> None:
        self._all_items = list(rows)
        self._apply_filter()

    def set_query(self, query: str) -> None:
        self._filter = _parse_recipe_filter(query)
        self._apply_filter()

    def _apply_filter(self) -> None:
        rows = self._all_items
        if self._filter.terms or self._filter.tier is not None or self._filter.enchant is not None:
            rows = [row for row in rows if _matches_recipe_filter(row, self._filter)]
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()

    def recipe_id_at(self, index: int) -> str | None:
        if index < 0 or index >= len(self._items):
            return None
        return self._items[index].recipe_id

    def index_of_recipe(self, recipe_id: str) -> int:
        for idx, item in enumerate(self._items):
            if item.recipe_id == recipe_id:
                return idx
        return -1


@dataclass(frozen=True)
class CraftPlanRow:
    row_id: int
    recipe_id: str
    display_name: str
    tier: int
    enchant: int
    craft_city: str
    daily_bonus_percent: float
    return_rate_percent: float | None
    runs: int
    enabled: bool
    profit_percent: float | None = None


class CraftPlanModel(QAbstractListModel):
    RowIdRole = Qt.UserRole + 1
    RecipeIdRole = Qt.UserRole + 2
    DisplayNameRole = Qt.UserRole + 3
    TierRole = Qt.UserRole + 4
    EnchantRole = Qt.UserRole + 5
    CraftCityRole = Qt.UserRole + 6
    DailyBonusRole = Qt.UserRole + 7
    ReturnRateRole = Qt.UserRole + 8
    RunsRole = Qt.UserRole + 9
    EnabledRole = Qt.UserRole + 10
    ProfitPercentRole = Qt.UserRole + 11

    def __init__(self) -> None:
        super().__init__()
        self._items: list[CraftPlanRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.RowIdRole:
            return item.row_id
        if role == self.RecipeIdRole:
            return item.recipe_id
        if role == self.DisplayNameRole:
            return item.display_name
        if role == self.TierRole:
            return item.tier
        if role == self.EnchantRole:
            return item.enchant
        if role == self.CraftCityRole:
            return item.craft_city
        if role == self.DailyBonusRole:
            return item.daily_bonus_percent
        if role == self.ReturnRateRole:
            return item.return_rate_percent
        if role == self.RunsRole:
            return item.runs
        if role == self.EnabledRole:
            return item.enabled
        if role == self.ProfitPercentRole:
            return item.profit_percent
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.RowIdRole: b"rowId",
            self.RecipeIdRole: b"recipeId",
            self.DisplayNameRole: b"displayName",
            self.TierRole: b"tier",
            self.EnchantRole: b"enchant",
            self.CraftCityRole: b"craftCity",
            self.DailyBonusRole: b"dailyBonusPercent",
            self.ReturnRateRole: b"returnRatePercent",
            self.RunsRole: b"runs",
            self.EnabledRole: b"isEnabled",
            self.ProfitPercentRole: b"profitPercent",
        }

    def set_items(self, rows: list[CraftPlanRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


class MarketSetupState(QObject):
    setupChanged = Signal()
    validationChanged = Signal()
    pricesChanged = Signal()
    inputsChanged = Signal()
    outputsChanged = Signal()
    resultsChanged = Signal()
    listsChanged = Signal()
    resultsDetailsChanged = Signal()

    def __init__(
        self,
        *,
        service: MarketDataService | None = None,
        logger: logging.Logger | None = None,
        auto_refresh_prices: bool = True,
        recipe_id: str = "T4_MAIN_SWORD",
    ) -> None:
        super().__init__()
        self._service = service
        self._log = logger or logging.getLogger(__name__)
        self._setup = CraftSetup(
            region=MarketRegion.EUROPE,
            craft_city="Bridgewatch",
            default_buy_city="Bridgewatch",
            default_sell_city="Bridgewatch",
            premium=True,
            focus_enabled=False,
            station_fee_percent=300.0,
            market_tax_percent=self._default_market_tax_percent(True),
            daily_bonus_percent=0.0,
            return_rate_percent=0.0,
            hideout_power_percent=0.0,
            quality=1,
        )
        self._craft_runs = 10
        self._inputs_model = MarketInputsModel()
        self._outputs_model = MarketOutputsModel()
        self._shopping_model = MarketShoppingModel()
        self._selling_model = MarketSellingModel()
        self._results_items_model = MarketResultsItemsModel()
        self._breakdown_model = MarketBreakdownModel()
        self._recipe_options_model = RecipeOptionsModel()
        self._craft_plan_model = CraftPlanModel()
        self._catalog = self._load_catalog()
        self._recipe = self._resolve_recipe(recipe_id)
        self._recipe_options_model.set_items(self._build_recipe_options())
        self._craft_plan_rows: list[CraftPlanRow] = []
        self._next_plan_row_id = 1
        self._breakdown = ProfitBreakdown()
        self._input_price_types: dict[str, PriceType] = {}
        self._output_price_types: dict[str, PriceType] = {}
        self._manual_input_prices: dict[str, int] = {}
        self._manual_output_prices: dict[str, int] = {}
        self._output_cities: dict[str, str] = {}
        self._price_index: dict[tuple[str, str, int], MarketPriceRecord] = {}
        self._price_context_key: tuple[str, int, tuple[str, ...], tuple[str, ...]] | None = None
        self._prices_source = "fallback"
        self._prices_status_text = "Using bundled fallback prices."
        self._results_sort_key = "profit"
        self._shopping_csv = ""
        self._selling_csv = ""
        self._list_action_text = ""
        self._recipe_search_query = ""
        self._preset_path = _default_preset_path()
        self._presets: dict[str, dict[str, object]] = self._load_presets()
        self._selected_preset_name = ""
        self._ensure_price_preferences_for_recipe(self._recipe)
        if auto_refresh_prices and self._service is not None:
            self._refresh_price_index(self.to_setup(), force=True)
        self._rebuild_preview(force_price_refresh=False)

    @Property(str, notify=setupChanged)
    def region(self) -> str:
        return self._setup.region.value

    @Property(str, notify=setupChanged)
    def craftCity(self) -> str:
        return self._setup.craft_city

    @Property(str, notify=setupChanged)
    def defaultBuyCity(self) -> str:
        return self._setup.default_buy_city

    @Property(str, notify=setupChanged)
    def defaultSellCity(self) -> str:
        return self._setup.default_sell_city

    @Property(bool, notify=setupChanged)
    def premium(self) -> bool:
        return self._setup.premium

    @Property(bool, notify=setupChanged)
    def focusEnabled(self) -> bool:
        return self._setup.focus_enabled

    @Property(float, notify=setupChanged)
    def stationFeePercent(self) -> float:
        return self._setup.station_fee_percent

    @Property(float, notify=setupChanged)
    def marketTaxPercent(self) -> float:
        return self._setup.market_tax_percent

    @Property(float, notify=setupChanged)
    def dailyBonusPercent(self) -> float:
        return self._setup.daily_bonus_percent

    @Property(int, notify=setupChanged)
    def dailyBonusPreset(self) -> int:
        return self._normalize_daily_bonus_percent(self._setup.daily_bonus_percent)

    @Property(float, notify=setupChanged)
    def returnRatePercent(self) -> float:
        return self._setup.return_rate_percent

    @Property(float, notify=setupChanged)
    def hideoutPowerPercent(self) -> float:
        return self._setup.hideout_power_percent

    @Property(int, notify=setupChanged)
    def quality(self) -> int:
        return self._setup.quality

    @Property(int, notify=setupChanged)
    def craftRuns(self) -> int:
        return self._craft_runs

    @Property(str, notify=setupChanged)
    def recipeId(self) -> str:
        return self._recipe.item.unique_name

    @Property(str, notify=setupChanged)
    def recipeDisplayName(self) -> str:
        return _friendly_item_label(self._recipe.item.display_name, self._recipe.item.unique_name)

    @Property(int, notify=setupChanged)
    def recipeTier(self) -> int:
        return int(self._recipe.item.tier or 0)

    @Property(int, notify=setupChanged)
    def recipeEnchant(self) -> int:
        return int(self._recipe.item.enchantment or 0)

    @Property(int, notify=setupChanged)
    def recipeIndex(self) -> int:
        return self._recipe_options_model.index_of_recipe(self.recipeId)

    @Property(str, notify=setupChanged)
    def recipeSearchQuery(self) -> str:
        return self._recipe_search_query

    @Property("QVariantList", notify=setupChanged)
    def presetNames(self) -> list[str]:
        return sorted(self._presets.keys(), key=lambda x: x.lower())

    @Property(str, notify=setupChanged)
    def selectedPresetName(self) -> str:
        return self._selected_preset_name

    @Property(str, notify=pricesChanged)
    def pricesSource(self) -> str:
        return self._prices_source

    @Property(str, notify=pricesChanged)
    def pricesStatusText(self) -> str:
        return self._prices_status_text

    @Property(QObject, constant=True)
    def inputsModel(self) -> QObject:
        return self._inputs_model

    @Property(QObject, constant=True)
    def outputsModel(self) -> QObject:
        return self._outputs_model

    @Property(QObject, constant=True)
    def recipeOptionsModel(self) -> QObject:
        return self._recipe_options_model

    @Property(QObject, constant=True)
    def craftPlanModel(self) -> QObject:
        return self._craft_plan_model

    @Property(int, notify=setupChanged)
    def craftPlanCount(self) -> int:
        return len(self._craft_plan_rows)

    @Property(int, notify=setupChanged)
    def craftPlanEnabledCount(self) -> int:
        return len([row for row in self._craft_plan_rows if row.enabled])

    @Property(QObject, constant=True)
    def shoppingModel(self) -> QObject:
        return self._shopping_model

    @Property(QObject, constant=True)
    def sellingModel(self) -> QObject:
        return self._selling_model

    @Property(QObject, constant=True)
    def resultsItemsModel(self) -> QObject:
        return self._results_items_model

    @Property(QObject, constant=True)
    def breakdownModel(self) -> QObject:
        return self._breakdown_model

    @Property(str, notify=listsChanged)
    def shoppingCsv(self) -> str:
        return self._shopping_csv

    @Property(str, notify=listsChanged)
    def sellingCsv(self) -> str:
        return self._selling_csv

    @Property(str, notify=listsChanged)
    def listActionText(self) -> str:
        return self._list_action_text

    @Property(str, notify=resultsDetailsChanged)
    def resultsSortKey(self) -> str:
        return self._results_sort_key

    @Property(float, notify=inputsChanged)
    def inputsTotalCost(self) -> float:
        total = 0.0
        for idx in range(self._inputs_model.rowCount()):
            model_index = self._inputs_model.index(idx, 0)
            value = self._inputs_model.data(model_index, MarketInputsModel.TotalCostRole)
            if value is not None:
                total += float(value)
        return total

    @Property(float, notify=outputsChanged)
    def outputsTotalValue(self) -> float:
        total = 0.0
        for idx in range(self._outputs_model.rowCount()):
            model_index = self._outputs_model.index(idx, 0)
            value = self._outputs_model.data(model_index, MarketOutputsModel.TotalValueRole)
            if value is not None:
                total += float(value)
        return total

    @Property(float, notify=outputsChanged)
    def outputsNetValue(self) -> float:
        total = 0.0
        for idx in range(self._outputs_model.rowCount()):
            model_index = self._outputs_model.index(idx, 0)
            value = self._outputs_model.data(model_index, MarketOutputsModel.NetValueRole)
            if value is not None:
                total += float(value)
        return total

    @Property(float, notify=resultsChanged)
    def stationFeeValue(self) -> float:
        return float(self._breakdown.station_fee)

    @Property(float, notify=resultsChanged)
    def marketTaxValue(self) -> float:
        return float(self._breakdown.market_tax)

    @Property(float, notify=resultsChanged)
    def netProfitValue(self) -> float:
        return float(self._breakdown.net_profit)

    @Property(float, notify=resultsChanged)
    def marginPercent(self) -> float:
        return float(self._breakdown.margin_percent)

    @Property(float, notify=resultsChanged)
    def focusUsed(self) -> float:
        return float(self._breakdown.focus_used)

    @Property(float, notify=resultsChanged)
    def silverPerFocus(self) -> float:
        if self._breakdown.focus_used <= 0:
            return 0.0
        return float(self._breakdown.net_profit / self._breakdown.focus_used)

    @Property(float, notify=setupChanged)
    def resourceReturnRatePercent(self) -> float:
        setup = self.to_setup()
        row = self._find_plan_row_by_recipe(self._recipe.item.unique_name)
        if row is not None:
            setup = self._setup_for_plan_row(setup, row)
        return float(effective_return_fraction(setup=setup, recipe=self._recipe) * 100.0)

    @Property(str, notify=validationChanged)
    def validationText(self) -> str:
        errors = validate_setup(self._setup)
        if self._craft_runs <= 0:
            errors.append("craftRuns must be > 0")
        if not any(row.enabled for row in self._craft_plan_rows):
            errors.append("craftPlan must contain at least one enabled recipe")
        if not errors:
            return ""
        return "; ".join(errors)

    @Slot(str)
    def setRegion(self, value: str) -> None:
        value_norm = value.strip().lower()
        mapping = {
            "europe": MarketRegion.EUROPE,
            "west": MarketRegion.WEST,
            "east": MarketRegion.EAST,
        }
        if value_norm not in mapping:
            return
        self._replace(region=mapping[value_norm])

    @Slot(int)
    def setRecipeIndex(self, index: int) -> None:
        recipe_id = self._recipe_options_model.recipe_id_at(int(index))
        if recipe_id is None:
            return
        self.setRecipeId(recipe_id)

    @Slot(str)
    def setRecipeId(self, recipe_id: str) -> None:
        recipe = self._catalog.get(recipe_id)
        if recipe is None:
            return
        if recipe.item.unique_name == self._recipe.item.unique_name:
            return
        self._recipe = recipe
        self._ensure_price_preferences_for_recipe(self._recipe)
        plan_row = self._find_plan_row_by_recipe(self._recipe.item.unique_name)
        if plan_row is not None:
            self._craft_runs = max(1, int(plan_row.runs))
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(str)
    def setRecipeSearchQuery(self, query: str) -> None:
        normalized = query.strip()
        if normalized == self._recipe_search_query:
            return
        self._recipe_search_query = normalized
        self._recipe_options_model.set_query(normalized)
        self.setupChanged.emit()

    @Slot(str)
    def setSelectedPresetName(self, value: str) -> None:
        name = value.strip()
        if name == self._selected_preset_name:
            return
        self._selected_preset_name = name
        self.setupChanged.emit()

    @Slot(str)
    def savePreset(self, raw_name: str) -> None:
        name = _sanitize_preset_name(raw_name)
        if not name:
            self._set_list_action_text("Preset name is empty.")
            return
        self._presets[name] = {
            "setup": _setup_to_dict(self._setup),
            "craft_runs": int(self._craft_runs),
        }
        if self._save_presets():
            self._selected_preset_name = name
            self._set_list_action_text(f"Preset saved: {name}")
            self.setupChanged.emit()

    @Slot(str)
    def loadPreset(self, raw_name: str) -> None:
        name = _sanitize_preset_name(raw_name)
        if not name:
            self._set_list_action_text("Preset name is empty.")
            return
        payload = self._presets.get(name)
        if payload is None:
            self._set_list_action_text(f"Preset not found: {name}")
            return
        setup_data = payload.get("setup")
        if not isinstance(setup_data, dict):
            self._set_list_action_text(f"Preset is invalid: {name}")
            return
        self._setup = sanitized_setup(_setup_from_dict(setup_data, fallback=self._setup))
        self._craft_runs = max(1, int(payload.get("craft_runs") or self._craft_runs))
        row = self._find_plan_row_by_recipe(self._recipe.item.unique_name)
        if row is not None and row.runs != self._craft_runs:
            self._update_plan_row(row.row_id, runs=self._craft_runs)
        self._selected_preset_name = name
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()
        self._set_list_action_text(f"Preset loaded: {name}")

    @Slot(str)
    def deletePreset(self, raw_name: str) -> None:
        name = _sanitize_preset_name(raw_name)
        if not name:
            self._set_list_action_text("Preset name is empty.")
            return
        if name not in self._presets:
            self._set_list_action_text(f"Preset not found: {name}")
            return
        del self._presets[name]
        if self._selected_preset_name == name:
            self._selected_preset_name = ""
        if self._save_presets():
            self._set_list_action_text(f"Preset deleted: {name}")
            self.setupChanged.emit()

    @Slot()
    def selectFirstRecipeOption(self) -> None:
        if self._recipe_options_model.rowCount() <= 0:
            return
        recipe_id = self._recipe_options_model.recipe_id_at(0)
        if recipe_id is None:
            return
        self.setRecipeId(recipe_id)

    @Slot()
    def addFirstRecipeOption(self) -> None:
        if self._recipe_options_model.rowCount() <= 0:
            return
        recipe_id = self._recipe_options_model.recipe_id_at(0)
        if recipe_id is None:
            return
        self.addRecipeToPlan(recipe_id)
        self.setRecipeId(recipe_id)

    @Slot(int)
    def addRecipeAtIndex(self, index: int) -> None:
        recipe_id = self._recipe_options_model.recipe_id_at(int(index))
        if recipe_id is None:
            return
        self.addRecipeToPlan(recipe_id)
        self.setRecipeId(recipe_id)

    @Slot()
    def addCurrentRecipeToPlan(self) -> None:
        added = self._add_recipe_to_plan_internal(self._recipe.item.unique_name, runs=self._craft_runs, enabled=True)
        if not added:
            row = self._find_plan_row_by_recipe(self._recipe.item.unique_name)
            if row is not None and (not row.enabled or row.runs != self._craft_runs):
                self._update_plan_row(row.row_id, runs=self._craft_runs, enabled=True)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(str)
    def addRecipeToPlan(self, recipe_id: str) -> None:
        added = self._add_recipe_to_plan_internal(recipe_id, runs=self._craft_runs, enabled=True)
        if not added:
            row = self._find_plan_row_by_recipe(recipe_id)
            if row is not None and not row.enabled:
                self._update_plan_row(row.row_id, enabled=True)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int)
    def selectPlanRow(self, row_id: int) -> None:
        row = self._find_plan_row(row_id)
        if row is None:
            return
        self.setRecipeId(row.recipe_id)

    @Slot(int)
    def removePlanRow(self, row_id: int) -> None:
        before = len(self._craft_plan_rows)
        self._craft_plan_rows = [row for row in self._craft_plan_rows if int(row.row_id) != int(row_id)]
        if len(self._craft_plan_rows) == before:
            return
        self._sync_craft_plan_model()
        if not any(row.recipe_id == self._recipe.item.unique_name for row in self._craft_plan_rows):
            if self._craft_plan_rows:
                self._recipe = self._resolve_recipe(self._craft_plan_rows[0].recipe_id)
                self._craft_runs = max(1, int(self._craft_plan_rows[0].runs))
                self._ensure_price_preferences_for_recipe(self._recipe)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, bool)
    def setPlanRowEnabled(self, row_id: int, enabled: bool) -> None:
        if not self._update_plan_row(row_id, enabled=bool(enabled)):
            return
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, int)
    def setPlanRowRuns(self, row_id: int, runs: int) -> None:
        normalized = max(1, int(runs))
        if not self._update_plan_row(row_id, runs=normalized):
            return
        row = self._find_plan_row(row_id)
        if row is not None and row.recipe_id == self._recipe.item.unique_name:
            self._craft_runs = normalized
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, str)
    def setPlanRowCraftCity(self, row_id: int, craft_city: str) -> None:
        city_value = craft_city.strip()
        if not city_value:
            city_value = self._setup.craft_city
        if not self._update_plan_row(row_id, craft_city=city_value):
            return
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, str)
    def setPlanRowDailyBonus(self, row_id: int, daily_bonus: str) -> None:
        text = daily_bonus.strip().replace("%", "")
        try:
            parsed = float(text)
        except ValueError:
            return
        normalized = float(self._normalize_daily_bonus_percent(parsed))
        if not self._update_plan_row(row_id, daily_bonus_percent=normalized):
            return
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def clearCraftPlan(self) -> None:
        self._craft_plan_rows = []
        self._next_plan_row_id = 1
        self._sync_craft_plan_model()
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(str)
    def setCraftCity(self, value: str) -> None:
        self._replace(craft_city=value)

    @Slot(str)
    def setDefaultBuyCity(self, value: str) -> None:
        self._replace(default_buy_city=value)

    @Slot(str)
    def setDefaultSellCity(self, value: str) -> None:
        self._replace(default_sell_city=value)

    @Slot(bool)
    def setPremium(self, value: bool) -> None:
        self._replace(premium=bool(value))

    @Slot(bool)
    def setFocusEnabled(self, value: bool) -> None:
        self._replace(focus_enabled=bool(value))

    @Slot(float)
    def setStationFeePercent(self, value: float) -> None:
        self._replace(station_fee_percent=float(value))

    @Slot(float)
    def setMarketTaxPercent(self, value: float) -> None:
        self._replace(market_tax_percent=float(value))

    @Slot(float)
    def setDailyBonusPercent(self, value: float) -> None:
        self._replace(daily_bonus_percent=float(self._normalize_daily_bonus_percent(value)))

    @Slot(str)
    def setDailyBonusPreset(self, value: str) -> None:
        text = value.strip().replace("%", "")
        try:
            parsed = float(text)
        except ValueError:
            return
        self.setDailyBonusPercent(parsed)

    @Slot(float)
    def setReturnRatePercent(self, value: float) -> None:
        self._replace(return_rate_percent=float(value))

    @Slot(float)
    def setHideoutPowerPercent(self, value: float) -> None:
        self._replace(hideout_power_percent=float(value))

    @Slot(int)
    def setQuality(self, value: int) -> None:
        self._replace(quality=int(value))

    @Slot(int)
    def setCraftRuns(self, value: int) -> None:
        runs = max(1, int(value))
        if runs == self._craft_runs:
            return
        self._craft_runs = runs
        row = self._find_plan_row_by_recipe(self._recipe.item.unique_name)
        if row is not None and row.runs != runs:
            self._update_plan_row(row.row_id, runs=runs)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def refreshPrices(self) -> None:
        self._rebuild_preview(force_price_refresh=True)

    @Slot()
    def showAoDataRaw(self) -> None:
        url = self._build_aodata_url()
        if not url:
            return
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
        except Exception as exc:  # pragma: no cover - optional
            self._set_list_action_text(f"Failed to open AOData URL: {exc}")
            return
        opened = QDesktopServices.openUrl(QUrl(url))
        if opened:
            self._set_list_action_text("Opened AOData prices in browser.")
        else:
            self._set_list_action_text(f"AOData URL: {url}")

    @Slot(str, str)
    def setInputPriceType(self, item_id: str, price_type: str) -> None:
        normalized = self._to_price_type(price_type)
        if normalized is None:
            return
        if self._input_price_types.get(item_id) == normalized:
            return
        self._input_price_types[item_id] = normalized
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, str)
    def setOutputPriceType(self, item_id: str, price_type: str) -> None:
        normalized = self._to_price_type(price_type)
        if normalized is None:
            return
        if self._output_price_types.get(item_id) == normalized:
            return
        self._output_price_types[item_id] = normalized
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, str)
    def setOutputCity(self, item_id: str, city: str) -> None:
        city_value = city.strip()
        if not city_value:
            city_value = self._setup.default_sell_city or self._setup.craft_city
        if self._output_cities.get(item_id, "") == city_value:
            return
        self._output_cities[item_id] = city_value
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, str)
    def setInputManualPrice(self, item_id: str, raw_value: str) -> None:
        price = _parse_price(raw_value)
        if price <= 0:
            self._manual_input_prices.pop(item_id, None)
        else:
            self._manual_input_prices[item_id] = price
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, str)
    def setOutputManualPrice(self, item_id: str, raw_value: str) -> None:
        price = _parse_price(raw_value)
        if price <= 0:
            self._manual_output_prices.pop(item_id, None)
        else:
            self._manual_output_prices[item_id] = price
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str)
    def setResultsSortKey(self, key: str) -> None:
        normalized = key.strip().lower()
        if normalized not in {"profit", "margin", "revenue"}:
            return
        if normalized == self._results_sort_key:
            return
        self._results_sort_key = normalized
        self._rebuild_preview(force_price_refresh=False)
        self.resultsDetailsChanged.emit()

    @Slot()
    def copyShoppingCsv(self) -> None:
        if not self._shopping_csv:
            self._set_list_action_text("Shopping CSV is empty.")
            return
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            self._set_list_action_text("Clipboard is not available.")
            return
        clipboard.setText(self._shopping_csv)
        self._set_list_action_text("Shopping CSV copied to clipboard.")

    @Slot(str)
    def copyText(self, raw_value: str) -> None:
        value = str(raw_value or "").strip()
        if not value:
            return
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            self._set_list_action_text("Clipboard is not available.")
            return
        clipboard.setText(value)
        self._set_list_action_text("Copied value to clipboard.")

    @Slot()
    def copySellingCsv(self) -> None:
        if not self._selling_csv:
            self._set_list_action_text("Selling CSV is empty.")
            return
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            self._set_list_action_text("Clipboard is not available.")
            return
        clipboard.setText(self._selling_csv)
        self._set_list_action_text("Selling CSV copied to clipboard.")

    @Slot(str)
    def exportShoppingCsv(self, raw_path: str) -> None:
        self._export_csv(raw_path=raw_path, payload=self._shopping_csv, label="Shopping")

    @Slot(str)
    def exportSellingCsv(self, raw_path: str) -> None:
        self._export_csv(raw_path=raw_path, payload=self._selling_csv, label="Selling")

    def to_setup(self) -> CraftSetup:
        return sanitized_setup(self._setup)

    def close(self) -> None:
        if self._service is not None:
            self._service.close()

    def _replace(self, **kwargs) -> None:
        premium_value = bool(kwargs.get("premium", self._setup.premium))
        market_tax_value = kwargs.get("market_tax_percent", self._default_market_tax_percent(premium_value))
        setup = CraftSetup(
            region=kwargs.get("region", self._setup.region),
            craft_city=kwargs.get("craft_city", self._setup.craft_city),
            default_buy_city=kwargs.get("default_buy_city", self._setup.default_buy_city),
            default_sell_city=kwargs.get("default_sell_city", self._setup.default_sell_city),
            premium=premium_value,
            focus_enabled=bool(kwargs.get("focus_enabled", self._setup.focus_enabled)),
            station_fee_percent=kwargs.get("station_fee_percent", self._setup.station_fee_percent),
            market_tax_percent=market_tax_value,
            daily_bonus_percent=kwargs.get("daily_bonus_percent", self._setup.daily_bonus_percent),
            return_rate_percent=kwargs.get("return_rate_percent", self._setup.return_rate_percent),
            hideout_power_percent=kwargs.get("hideout_power_percent", self._setup.hideout_power_percent),
            quality=kwargs.get("quality", self._setup.quality),
        )
        self._setup = sanitized_setup(setup)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    def _sync_craft_plan_model(self) -> None:
        self._craft_plan_model.set_items(self._craft_plan_rows)

    def _add_recipe_to_plan_internal(self, recipe_id: str, *, runs: int, enabled: bool) -> bool:
        recipe = self._catalog.get(recipe_id)
        if recipe is None:
            return False
        if self._find_plan_row_by_recipe(recipe_id) is not None:
            return False
        self._ensure_price_preferences_for_recipe(recipe)
        row = CraftPlanRow(
            row_id=self._next_plan_row_id,
            recipe_id=recipe.item.unique_name,
            display_name=_friendly_item_label(recipe.item.display_name, recipe.item.unique_name),
            tier=int(recipe.item.tier or 0),
            enchant=int(recipe.item.enchantment or 0),
            craft_city=self._setup.craft_city or "Bridgewatch",
            daily_bonus_percent=float(self._normalize_daily_bonus_percent(self._setup.daily_bonus_percent)),
            return_rate_percent=None,
            runs=max(1, int(runs)),
            enabled=bool(enabled),
            profit_percent=None,
        )
        self._next_plan_row_id += 1
        self._craft_plan_rows.append(row)
        self._sync_craft_plan_model()
        return True

    def _find_plan_row(self, row_id: int) -> CraftPlanRow | None:
        for row in self._craft_plan_rows:
            if int(row.row_id) == int(row_id):
                return row
        return None

    def _find_plan_row_by_recipe(self, recipe_id: str) -> CraftPlanRow | None:
        for row in self._craft_plan_rows:
            if row.recipe_id == recipe_id:
                return row
        return None

    def _update_plan_row(
        self,
        row_id: int,
        *,
        runs: int | None = None,
        enabled: bool | None = None,
        craft_city: str | None = None,
        daily_bonus_percent: float | None = None,
    ) -> bool:
        changed = False
        next_rows: list[CraftPlanRow] = []
        for row in self._craft_plan_rows:
            if int(row.row_id) != int(row_id):
                next_rows.append(row)
                continue
            next_runs = max(1, int(runs)) if runs is not None else row.runs
            next_enabled = bool(enabled) if enabled is not None else row.enabled
            next_craft_city = craft_city.strip() if craft_city is not None else row.craft_city
            if not next_craft_city:
                next_craft_city = row.craft_city or self._setup.craft_city or "Bridgewatch"
            next_daily_bonus = (
                float(self._normalize_daily_bonus_percent(daily_bonus_percent))
                if daily_bonus_percent is not None
                else float(row.daily_bonus_percent)
            )
            next_row = CraftPlanRow(
                row_id=row.row_id,
                recipe_id=row.recipe_id,
                display_name=row.display_name,
                tier=row.tier,
                enchant=row.enchant,
                craft_city=next_craft_city,
                daily_bonus_percent=next_daily_bonus,
                return_rate_percent=row.return_rate_percent,
                runs=next_runs,
                enabled=next_enabled,
                profit_percent=row.profit_percent,
            )
            changed = next_row != row
            next_rows.append(next_row)
        if changed:
            self._craft_plan_rows = next_rows
            self._sync_craft_plan_model()
        return changed

    def _ensure_price_preferences_for_recipe(self, recipe: Recipe) -> None:
        for component in recipe.components:
            self._input_price_types.setdefault(component.item.unique_name, PriceType.BUY_ORDER)
        for output in recipe.outputs:
            self._output_price_types.setdefault(output.item.unique_name, PriceType.SELL_ORDER)

    def _recipes_for_preview(self) -> list[tuple[CraftPlanRow, Recipe]]:
        rows: list[tuple[CraftPlanRow, Recipe]] = []
        for row in self._craft_plan_rows:
            if not row.enabled:
                continue
            recipe = self._catalog.get(row.recipe_id)
            if recipe is None:
                continue
            rows.append((row, recipe))
        return rows

    @staticmethod
    def _setup_for_plan_row(setup: CraftSetup, row: CraftPlanRow) -> CraftSetup:
        return CraftSetup(
            region=setup.region,
            craft_city=row.craft_city,
            default_buy_city=setup.default_buy_city,
            default_sell_city=setup.default_sell_city,
            premium=setup.premium,
            focus_enabled=setup.focus_enabled,
            station_fee_percent=setup.station_fee_percent,
            market_tax_percent=setup.market_tax_percent,
            daily_bonus_percent=float(row.daily_bonus_percent),
            return_rate_percent=setup.return_rate_percent,
            hideout_power_percent=setup.hideout_power_percent,
            quality=setup.quality,
        )

    def _recipes_for_pricing(self) -> list[Recipe]:
        recipes: list[Recipe] = []
        seen: set[str] = set()
        for row in self._craft_plan_rows:
            if not row.enabled:
                continue
            recipe = self._catalog.get(row.recipe_id)
            if recipe is None:
                continue
            if recipe.item.unique_name in seen:
                continue
            seen.add(recipe.item.unique_name)
            recipes.append(recipe)
        return recipes

    def _collect_pricing_item_ids(self) -> list[str]:
        item_ids: set[str] = set()
        for recipe in self._recipes_for_pricing():
            for component in recipe.components:
                item_ids.update(_item_id_candidates(component.item.unique_name))
            for output in recipe.outputs:
                item_ids.update(_item_id_candidates(output.item.unique_name))
        return sorted(item_ids)

    def _collect_locations(self, setup: CraftSetup) -> list[str]:
        location_set = {
            setup.craft_city.strip(),
            setup.default_buy_city.strip(),
            setup.default_sell_city.strip(),
        }
        for row in self._craft_plan_rows:
            city_value = row.craft_city.strip()
            if city_value:
                location_set.add(city_value)
        locations = sorted(
            location
            for location in (location_set - {""})
            if self._is_market_location(location)
        )
        if not locations:
            locations = ["Bridgewatch"]
        return locations

    def _clear_preview_state(self, note: str) -> None:
        self._inputs_model.set_items([])
        self._outputs_model.set_items([])
        self._shopping_model.set_items([])
        self._selling_model.set_items([])
        self._results_items_model.set_items([])
        self._breakdown_model.set_items([])
        self._set_plan_profit_map({})
        self._shopping_csv = ""
        self._selling_csv = ""
        self._breakdown = ProfitBreakdown(notes=[note] if note else [])
        self.inputsChanged.emit()
        self.outputsChanged.emit()
        self.resultsChanged.emit()
        self.listsChanged.emit()
        self.resultsDetailsChanged.emit()

    def _rebuild_preview(self, *, force_price_refresh: bool) -> None:
        setup = self.to_setup()
        price_index = self._current_price_index(setup, force_refresh=force_price_refresh)
        planned_recipes = self._recipes_for_preview()
        if not planned_recipes:
            self._clear_preview_state("no enabled recipes in craft plan")
            return
        try:
            runs = []
            for row, recipe in planned_recipes:
                self._ensure_price_preferences_for_recipe(recipe)
                row_setup = self._setup_for_plan_row(setup, row)
                runs.append(
                    build_craft_run(
                        recipe=recipe,
                        quantity=max(1, int(row.runs)),
                        setup=row_setup,
                        price_index=price_index,
                        input_price_types=dict(self._input_price_types),
                        output_cities=dict(self._output_cities),
                        output_price_types=dict(self._output_price_types),
                        manual_input_prices=dict(self._manual_input_prices),
                        manual_output_prices=dict(self._manual_output_prices),
                    )
                )
        except Exception:
            self._clear_preview_state("preview build failed")
            return

        run_profit_by_row: dict[int, float] = {}
        run_rrr_by_row: dict[int, float] = {}
        for (plan_row, recipe), run in zip(planned_recipes, runs):
            breakdown = compute_run_profit(run)
            run_profit_by_row[int(plan_row.row_id)] = float(breakdown.margin_percent)
            row_setup = self._setup_for_plan_row(setup, plan_row)
            run_rrr_by_row[int(plan_row.row_id)] = float(
                effective_return_fraction(setup=row_setup, recipe=recipe) * 100.0
            )
        self._set_plan_profit_map(run_profit_by_row, run_rrr_by_row)

        all_inputs = [line for run in runs for line in run.inputs]
        all_outputs = [line for run in runs for line in run.outputs]

        input_acc: dict[tuple[str, str, str, float], dict[str, float | str]] = {}
        for line in all_inputs:
            key = (line.item.unique_name, line.city, line.price_type.value, float(line.unit_price))
            row = input_acc.get(key)
            if row is None:
                input_acc[key] = {
                    "item_id": line.item.unique_name,
                    "item": _friendly_item_label(line.item.display_name, line.item.unique_name),
                    "city": line.city,
                    "price_type": line.price_type.value,
                    "price_age_text": self._price_age_text(
                        item_id=line.item.unique_name,
                        city=line.city,
                        quality=self._setup.quality,
                        price_type=line.price_type.value,
                    ),
                    "unit_price": float(line.unit_price),
                    "quantity": float(line.quantity),
                    "total_cost": float(line.total_cost),
                }
            else:
                row["quantity"] = float(row["quantity"]) + float(line.quantity)
                row["total_cost"] = float(row["total_cost"]) + float(line.total_cost)

        input_rows = [
            InputPreviewRow(
                item_id=str(row["item_id"]),
                item=str(row["item"]),
                quantity=float(max(0, math.ceil(float(row["quantity"])))),
                city=str(row["city"]),
                price_type=str(row["price_type"]),
                price_age_text=str(row["price_age_text"]),
                manual_price=self._manual_input_prices.get(str(row["item_id"]), 0),
                unit_price=float(row["unit_price"]),
                total_cost=float(max(0, math.ceil(float(row["quantity"]))) * float(row["unit_price"])),
            )
            for row in input_acc.values()
        ]
        input_rows.sort(key=lambda x: (x.item.lower(), x.city.lower()))

        self._breakdown = compute_batch_profit(tuple(runs))
        valuations = compute_output_valuations(
            output_lines=all_outputs,
            station_fee_percent=setup.station_fee_percent,
            market_tax_percent=setup.market_tax_percent,
        )

        output_acc: dict[tuple[str, str, str, float], dict[str, float | str]] = {}
        for valuation in valuations:
            line = valuation.line
            key = (line.item.unique_name, line.city, line.price_type.value, float(line.unit_price))
            row = output_acc.get(key)
            if row is None:
                output_acc[key] = {
                    "item_id": line.item.unique_name,
                    "item": _friendly_item_label(line.item.display_name, line.item.unique_name),
                    "city": line.city,
                    "price_type": line.price_type.value,
                    "unit_price": float(line.unit_price),
                    "quantity": float(line.quantity),
                    "total_value": float(valuation.gross_value),
                    "fee_value": float(valuation.fee_value),
                    "tax_value": float(valuation.tax_value),
                    "net_value": float(valuation.net_value),
                }
            else:
                row["quantity"] = float(row["quantity"]) + float(line.quantity)
                row["total_value"] = float(row["total_value"]) + float(valuation.gross_value)
                row["fee_value"] = float(row["fee_value"]) + float(valuation.fee_value)
                row["tax_value"] = float(row["tax_value"]) + float(valuation.tax_value)
                row["net_value"] = float(row["net_value"]) + float(valuation.net_value)

        output_rows = [
            OutputPreviewRow(
                item_id=str(row["item_id"]),
                item=str(row["item"]),
                quantity=float(row["quantity"]),
                city=str(row["city"]),
                price_type=str(row["price_type"]),
                manual_price=self._manual_output_prices.get(str(row["item_id"]), 0),
                unit_price=float(row["unit_price"]),
                total_value=float(row["total_value"]),
                fee_value=float(row["fee_value"]),
                tax_value=float(row["tax_value"]),
                net_value=float(row["net_value"]),
            )
            for row in output_acc.values()
        ]
        output_rows.sort(key=lambda x: (x.item.lower(), x.city.lower()))

        self._inputs_model.set_items(input_rows)
        self._outputs_model.set_items(output_rows)

        shopping_rows = [
            ShoppingPreviewRow(
                item_id=entry.item_id,
                item=_friendly_item_label(entry.item_name, entry.item_id),
                quantity=float(max(0, math.ceil(float(entry.quantity)))),
                city=entry.city,
                price_type=entry.price_type,
                unit_price=float(entry.unit_price),
                total_cost=float(max(0, math.ceil(float(entry.quantity))) * float(entry.unit_price)),
            )
            for entry in build_shopping_entries(all_inputs)
        ]
        selling_rows = [
            SellingPreviewRow(
                item_id=entry.item_id,
                item=_friendly_item_label(entry.item_name, entry.item_id),
                quantity=float(entry.quantity),
                city=entry.city,
                price_type=entry.price_type,
                unit_price=float(entry.unit_price),
                total_value=float(entry.total_value),
            )
            for entry in build_selling_entries(all_outputs)
        ]

        self._shopping_model.set_items(shopping_rows)
        self._selling_model.set_items(selling_rows)
        self._shopping_csv = self._rows_to_csv(
            header=["item_id", "item_name", "quantity", "city", "price_type", "unit_price", "total_cost"],
            rows=[
                [
                    row.item_id,
                    row.item,
                    f"{row.quantity:.4f}",
                    row.city,
                    row.price_type,
                    f"{row.unit_price:.2f}",
                    f"{row.total_cost:.2f}",
                ]
                for row in shopping_rows
            ],
        )
        self._selling_csv = self._rows_to_csv(
            header=["item_id", "item_name", "quantity", "city", "price_type", "unit_price", "total_value"],
            rows=[
                [
                    row.item_id,
                    row.item,
                    f"{row.quantity:.4f}",
                    row.city,
                    row.price_type,
                    f"{row.unit_price:.2f}",
                    f"{row.total_value:.2f}",
                ]
                for row in selling_rows
            ],
        )

        results_rows = self._build_results_rows(output_rows)
        self._results_items_model.set_items(results_rows)
        breakdown_rows = self._build_breakdown_rows()
        self._breakdown_model.set_items(breakdown_rows)

        self.inputsChanged.emit()
        self.outputsChanged.emit()
        self.resultsChanged.emit()
        self.listsChanged.emit()
        self.resultsDetailsChanged.emit()

    def _build_results_rows(self, output_rows: list[OutputPreviewRow]) -> list[ResultItemRow]:
        total_revenue = max(0.0, sum(row.total_value for row in output_rows))
        input_total = float(self.inputsTotalCost)
        rows: list[ResultItemRow] = []
        for output in output_rows:
            share = (output.total_value / total_revenue) if total_revenue > 0 else 0.0
            allocated_cost = input_total * share
            fee_value = float(output.fee_value)
            tax_value = float(output.tax_value)
            profit = float(output.net_value) - allocated_cost
            margin = (profit / allocated_cost * 100.0) if allocated_cost > 0 else 0.0
            rows.append(
                ResultItemRow(
                    item_id=output.item_id,
                    item=output.item,
                    city=output.city,
                    quantity=float(output.quantity),
                    unit_price=float(output.unit_price),
                    revenue=float(output.total_value),
                    allocated_cost=float(allocated_cost),
                    fee_value=float(fee_value),
                    tax_value=float(tax_value),
                    profit=float(profit),
                    margin_percent=float(margin),
                    demand_proxy=float(
                        self._demand_proxy_percent(
                            item_id=output.item_id,
                            city=output.city,
                            quality=self._setup.quality,
                        )
                    ),
                )
            )

        if self._results_sort_key == "margin":
            rows.sort(key=lambda x: x.margin_percent, reverse=True)
        elif self._results_sort_key == "revenue":
            rows.sort(key=lambda x: x.revenue, reverse=True)
        else:
            rows.sort(key=lambda x: x.profit, reverse=True)
        return rows

    def _build_breakdown_rows(self) -> list[BreakdownRow]:
        return [
            BreakdownRow(label="Raw materials", value=float(self._breakdown.input_cost)),
            BreakdownRow(label="Station fee", value=float(self._breakdown.station_fee)),
            BreakdownRow(label="Market tax", value=float(self._breakdown.market_tax)),
            BreakdownRow(label="Net profit", value=float(self._breakdown.net_profit)),
        ]

    def _demand_proxy_percent(self, *, item_id: str, city: str, quality: int) -> float:
        quote = _find_price_quote(
            self._price_index,
            item_id=item_id,
            city=city,
            quality=quality,
            preferred_mode=None,
        )
        if quote is None:
            return 0.0
        if quote.sell_price_min <= 0 or quote.buy_price_max <= 0:
            return 0.0
        return (float(quote.buy_price_max) / float(quote.sell_price_min)) * 100.0

    def _set_plan_profit_map(
        self,
        values: dict[int, float],
        return_rates: dict[int, float] | None = None,
    ) -> None:
        rates = return_rates or {}
        next_rows: list[CraftPlanRow] = []
        changed = False
        for row in self._craft_plan_rows:
            next_profit = values.get(int(row.row_id))
            next_rrr = rates.get(int(row.row_id), row.return_rate_percent)
            next_row = CraftPlanRow(
                row_id=row.row_id,
                recipe_id=row.recipe_id,
                display_name=row.display_name,
                tier=row.tier,
                enchant=row.enchant,
                craft_city=row.craft_city,
                daily_bonus_percent=row.daily_bonus_percent,
                return_rate_percent=next_rrr,
                runs=row.runs,
                enabled=row.enabled,
                profit_percent=next_profit,
            )
            if next_row != row:
                changed = True
            next_rows.append(next_row)
        if changed:
            self._craft_plan_rows = next_rows
            self._sync_craft_plan_model()

    def _price_age_text(self, *, item_id: str, city: str, quality: int, price_type: str) -> str:
        normalized = str(price_type).strip().lower()
        if normalized == PriceType.MANUAL.value:
            return "manual"
        quote = _find_price_quote(
            self._price_index,
            item_id=item_id,
            city=city,
            quality=quality,
            preferred_mode=normalized,
        )
        if quote is None:
            return "n/a"

        if normalized == PriceType.BUY_ORDER.value:
            if int(quote.buy_price_max or 0) <= 0:
                return "n/a"
            dt = _parse_iso_datetime(quote.buy_price_max_date)
        elif normalized == PriceType.SELL_ORDER.value:
            if int(quote.sell_price_min or 0) <= 0:
                return "n/a"
            dt = _parse_iso_datetime(quote.sell_price_min_date)
        else:
            dt_buy = _parse_iso_datetime(quote.buy_price_max_date) if int(quote.buy_price_max or 0) > 0 else None
            dt_sell = _parse_iso_datetime(quote.sell_price_min_date) if int(quote.sell_price_min or 0) > 0 else None
            dt = max([x for x in [dt_buy, dt_sell] if x is not None], default=None)

        if dt is None:
            return "n/a"
        return _format_age(dt)

    def _set_list_action_text(self, text: str) -> None:
        self._list_action_text = text
        self.listsChanged.emit()

    def _build_aodata_url(self) -> str | None:
        setup = self.to_setup()
        item_ids = self._collect_pricing_item_ids()
        if not item_ids:
            self._set_list_action_text("Select a recipe in Craft Plan to build AOData URL.")
            return None
        locations = self._collect_locations(setup)
        if not locations:
            self._set_list_action_text("No market locations selected.")
            return None
        qualities = [setup.quality, 1] if setup.quality != 1 else [1]
        params = urlencode(
            {
                "locations": ",".join(locations),
                "qualities": ",".join(str(x) for x in qualities),
            }
        )
        host = REGION_HOSTS.get(setup.region)
        if not host:
            self._set_list_action_text("Unknown AOData region.")
            return None
        joined_ids = ",".join(item_ids)
        return f"https://{host}/api/v2/stats/prices/{joined_ids}.json?{params}"

    def _export_csv(self, *, raw_path: str, payload: str, label: str) -> None:
        path_text = raw_path.strip()
        if not path_text:
            self._set_list_action_text(f"{label} export path is empty.")
            return
        if not payload:
            self._set_list_action_text(f"{label} CSV is empty.")
            return
        try:
            path = Path(path_text)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
        except Exception as exc:
            self._set_list_action_text(f"{label} export failed: {exc}")
            return
        self._set_list_action_text(f"{label} CSV exported to {path}.")

    @staticmethod
    def _rows_to_csv(*, header: list[str], rows: list[list[str]]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
        return buf.getvalue()

    def _current_price_index(
        self,
        setup: CraftSetup,
        *,
        force_refresh: bool,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        if force_refresh:
            return self._refresh_price_index(setup, force=True)
        context_key = self._price_key(setup)
        if self._price_index and context_key == self._price_context_key:
            return self._price_index
        return self._refresh_price_index(setup, force=False)

    def _refresh_price_index(
        self,
        setup: CraftSetup,
        *,
        force: bool,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        item_ids = self._collect_pricing_item_ids()
        locations = self._collect_locations(setup)
        context_key = self._price_key(setup)
        if not force and self._price_index and context_key == self._price_context_key:
            return self._price_index
        if not item_ids:
            self._set_fallback_status("No recipe items selected. Prices unavailable.")
            self._price_index = {}
            self._price_context_key = context_key
            return self._price_index

        if self._service is None:
            self._set_fallback_status("AO Data client not configured. Using bundled fallback prices.")
            self._price_index = self._build_fallback_price_index(setup)
            self._price_context_key = context_key
            return self._price_index

        try:
            index = self._service.get_price_index(
                region=setup.region,
                item_ids=item_ids,
                locations=locations,
                qualities=[setup.quality, 1] if setup.quality != 1 else [1],
                ttl_seconds=120.0,
                allow_stale=not force,
                allow_cache=not force,
            )
            if index:
                meta = self._service.last_prices_meta
                self._price_index = index
                self._price_context_key = context_key
                self._prices_source = meta.source
                self._prices_status_text = (
                    f"{meta.source}: {meta.record_count} rows in {meta.elapsed_ms:.0f} ms"
                )
                self.pricesChanged.emit()
                return self._price_index
            self._set_fallback_status("AO Data returned no price rows. Using bundled fallback prices.")
        except Exception as exc:
            self._log.warning("AO Data fetch failed, using fallback prices: %s", exc)
            self._set_fallback_status(f"AO Data fetch failed ({exc}). Using bundled fallback prices.")

        self._price_index = self._build_fallback_price_index(setup)
        self._price_context_key = context_key
        return self._price_index

    def _set_fallback_status(self, message: str) -> None:
        self._prices_source = "fallback"
        self._prices_status_text = message
        self.pricesChanged.emit()

    def _load_presets(self) -> dict[str, dict[str, object]]:
        path = self._preset_path
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._log.warning("Market preset load failed: %s", exc)
            return {}
        if not isinstance(payload, dict):
            return {}
        out: dict[str, dict[str, object]] = {}
        for key, value in payload.items():
            name = _sanitize_preset_name(str(key))
            if not name or not isinstance(value, dict):
                continue
            out[name] = value
        return out

    def _save_presets(self) -> bool:
        path = self._preset_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            serialized = json.dumps(self._presets, ensure_ascii=True, indent=2, sort_keys=True)
            path.write_text(serialized, encoding="utf-8")
        except Exception as exc:
            self._log.warning("Market preset save failed: %s", exc)
            self._set_list_action_text(f"Preset save failed: {exc}")
            return False
        return True

    def _price_key(self, setup: CraftSetup) -> tuple[str, int, tuple[str, ...], tuple[str, ...]]:
        item_ids = tuple(self._collect_pricing_item_ids())
        locations = tuple(self._collect_locations(setup))
        return (setup.region.value, int(setup.quality), item_ids, locations)

    @staticmethod
    def _default_market_tax_percent(premium: bool) -> float:
        # Margin-based default: setup fee + sales tax.
        # premium=True -> 2.5% + 4.0%; premium=False -> 2.5% + 8.0%
        return 6.5 if premium else 10.5

    @staticmethod
    def _normalize_daily_bonus_percent(value: float) -> float:
        raw = int(round(float(value)))
        if raw >= 15:
            return 20.0
        if raw >= 5:
            return 10.0
        return 0.0

    @staticmethod
    def _to_price_type(value: str) -> PriceType | None:
        normalized = value.strip().lower()
        if normalized == PriceType.BUY_ORDER.value:
            return PriceType.BUY_ORDER
        if normalized == PriceType.SELL_ORDER.value:
            return PriceType.SELL_ORDER
        if normalized == PriceType.AVERAGE.value:
            return PriceType.AVERAGE
        if normalized == PriceType.MANUAL.value:
            return PriceType.MANUAL
        return None

    @staticmethod
    def _is_market_location(location: str) -> bool:
        normalized = location.strip().lower()
        normalized = " ".join(normalized.split())
        market_locations = {
            "bridgewatch",
            "martlock",
            "lymhurst",
            "fort sterling",
            "fortsterling",
            "thetford",
            "caerleon",
            "brecilien",
            "black market",
            "blackmarket",
        }
        return normalized in market_locations

    def _load_catalog(self) -> RecipeCatalog:
        try:
            catalog = RecipeCatalog.from_default()
        except Exception as exc:
            self._log.warning("Market recipe catalog load failed: %s", exc)
            return RecipeCatalog(recipes={})
        issues = catalog.validate_integrity()
        if issues:
            self._log.warning("Market recipe catalog integrity issues: %d", len(issues))
            for issue in issues[:5]:
                self._log.warning("Recipe issue [%s]: %s", issue.recipe_id, issue.message)
        return catalog

    def _build_recipe_options(self) -> list[RecipeOptionRow]:
        rows: list[RecipeOptionRow] = []
        for recipe_id in self._catalog.items():
            recipe = self._catalog.get(recipe_id)
            if recipe is None:
                continue
            rows.append(
                RecipeOptionRow(
                    recipe_id=recipe.item.unique_name,
                    display_name=_friendly_item_label(recipe.item.display_name, recipe.item.unique_name),
                    tier=int(recipe.item.tier or 0),
                    enchant=int(recipe.item.enchantment or 0),
                )
            )
        rows.sort(key=lambda row: row.display_name.lower())
        return rows

    def _resolve_recipe(self, recipe_id: str) -> Recipe:
        recipe = self._catalog.get(recipe_id)
        if recipe is not None:
            return recipe
        recipe = self._catalog.first()
        if recipe is not None:
            return recipe
        self._log.warning("Market catalog empty, using builtin fallback recipe.")
        return self._build_builtin_recipe()

    @staticmethod
    def _build_builtin_recipe() -> Recipe:
        from albion_dps.market.models import ItemRef, RecipeComponent, RecipeOutput

        sword = ItemRef(unique_name="T4_MAIN_SWORD", display_name="Broadsword", tier=4, enchantment=0)
        bars = ItemRef(unique_name="T4_METALBAR", display_name="Metal Bar", tier=4, enchantment=0)
        planks = ItemRef(unique_name="T4_PLANKS", display_name="Planks", tier=4, enchantment=0)
        return Recipe(
            item=sword,
            station="Warrior Forge",
            city_bonus="Bridgewatch",
            components=(
                RecipeComponent(item=bars, quantity=16.0),
                RecipeComponent(item=planks, quantity=8.0),
            ),
            outputs=(RecipeOutput(item=sword, quantity=1.0),),
            focus_per_craft=200,
        )

    def _build_fallback_price_index(
        self,
        setup: CraftSetup,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        locations = set(self._collect_locations(setup))
        locations.add("Bridgewatch")
        prices = self._estimate_fallback_prices()
        index: dict[tuple[str, str, int], MarketPriceRecord] = {}
        for location in locations:
            if not location:
                continue
            for item_id, (buy_price, sell_price) in prices.items():
                index[(item_id, location, int(setup.quality))] = MarketPriceRecord(
                    item_id=item_id,
                    city=location,
                    quality=int(setup.quality),
                    sell_price_min=int(sell_price),
                    buy_price_max=int(buy_price),
                    sell_price_min_date="",
                    buy_price_max_date="",
                )
                if int(setup.quality) != 1:
                    index[(item_id, location, 1)] = MarketPriceRecord(
                        item_id=item_id,
                        city=location,
                        quality=1,
                        sell_price_min=int(sell_price),
                        buy_price_max=int(buy_price),
                        sell_price_min_date="",
                        buy_price_max_date="",
                    )
        return index

    def _estimate_fallback_prices(self) -> dict[str, tuple[int, int]]:
        known_prices: dict[str, tuple[int, int]] = {
            "T4_METALBAR": (900, 1000),
            "T4_PLANKS": (500, 600),
            "T4_CLOTH": (540, 620),
            "T4_LEATHER": (560, 640),
        }
        prices: dict[str, tuple[int, int]] = {}
        for recipe in self._recipes_for_pricing():
            for component in recipe.components:
                item_id = component.item.unique_name
                prices[item_id] = known_prices.get(item_id, self._price_by_tier(component.item.tier))

            component_sell_total = 0.0
            for component in recipe.components:
                buy_price, sell_price = prices.get(
                    component.item.unique_name,
                    self._price_by_tier(component.item.tier),
                )
                _ = buy_price
                component_sell_total += sell_price * component.quantity

            outputs = recipe.outputs or ()
            total_output_qty = sum(max(0.01, x.quantity) for x in outputs)
            if outputs and component_sell_total > 0:
                estimated_sell = int((component_sell_total / total_output_qty) * 1.30)
            else:
                estimated_sell = 1200
            estimated_buy = int(max(1, estimated_sell * 0.95))
            for output in outputs:
                prices[output.item.unique_name] = (estimated_buy, estimated_sell)
        return prices

    @staticmethod
    def _price_by_tier(tier: int | None) -> tuple[int, int]:
        value_by_tier = {
            2: 80,
            3: 220,
            4: 600,
            5: 1800,
            6: 5200,
            7: 14500,
            8: 42000,
        }
        tier_value = value_by_tier.get(int(tier or 4), value_by_tier[4])
        buy_price = int(max(1, tier_value * 0.92))
        sell_price = int(max(1, tier_value))
        return buy_price, sell_price


def _parse_price(raw_value: str) -> int:
    text = raw_value.strip().replace(",", ".")
    if not text:
        return 0
    try:
        parsed = int(float(text))
    except ValueError:
        return 0
    return max(0, parsed)


def _default_preset_path() -> Path:
    return Path.home() / ".albion_dps" / "market_presets.json"


def _sanitize_preset_name(raw_value: str) -> str:
    value = str(raw_value or "").strip()
    value = re.sub(r"\s+", " ", value)
    return value[:64]


def _setup_to_dict(setup: CraftSetup) -> dict[str, object]:
    return {
        "region": setup.region.value,
        "craft_city": setup.craft_city,
        "default_buy_city": setup.default_buy_city,
        "default_sell_city": setup.default_sell_city,
        "premium": bool(setup.premium),
        "focus_enabled": bool(setup.focus_enabled),
        "station_fee_percent": float(setup.station_fee_percent),
        "market_tax_percent": float(setup.market_tax_percent),
        "daily_bonus_percent": float(setup.daily_bonus_percent),
        "return_rate_percent": float(setup.return_rate_percent),
        "hideout_power_percent": float(setup.hideout_power_percent),
        "quality": int(setup.quality),
    }


def _setup_from_dict(payload: dict[str, object], *, fallback: CraftSetup) -> CraftSetup:
    region_raw = str(payload.get("region") or fallback.region.value).strip().lower()
    region_map = {
        "europe": MarketRegion.EUROPE,
        "west": MarketRegion.WEST,
        "east": MarketRegion.EAST,
    }
    region = region_map.get(region_raw, fallback.region)
    return CraftSetup(
        region=region,
        craft_city=str(payload.get("craft_city") or fallback.craft_city),
        default_buy_city=str(payload.get("default_buy_city") or fallback.default_buy_city),
        default_sell_city=str(payload.get("default_sell_city") or fallback.default_sell_city),
        premium=bool(payload.get("premium", fallback.premium)),
        focus_enabled=bool(payload.get("focus_enabled", fallback.focus_enabled)),
        station_fee_percent=float(payload.get("station_fee_percent") or fallback.station_fee_percent),
        market_tax_percent=float(payload.get("market_tax_percent") or fallback.market_tax_percent),
        daily_bonus_percent=float(payload.get("daily_bonus_percent") or fallback.daily_bonus_percent),
        return_rate_percent=float(payload.get("return_rate_percent") or fallback.return_rate_percent),
        hideout_power_percent=float(payload.get("hideout_power_percent") or fallback.hideout_power_percent),
        quality=int(payload.get("quality") or fallback.quality),
    )


def _friendly_item_label(display_name: str, item_id: str) -> str:
    name = str(display_name or "").strip()
    if name and name.upper() != str(item_id or "").strip().upper():
        return name
    fallback = _humanize_item_id(item_id)
    return fallback or str(item_id or "").strip()


def _humanize_item_id(item_id: str) -> str:
    raw = str(item_id or "").strip()
    if not raw:
        return ""

    enchant: int | None = None
    base = raw
    if "@" in base:
        stem, enchant_raw = base.rsplit("@", 1)
        base = stem
        try:
            enchant = int(enchant_raw)
        except ValueError:
            enchant = None

    base = _LEVEL_SUFFIX_RE.sub("", base)
    tier: int | None = None
    tier_match = _TIER_PREFIX_RE.match(base)
    if tier_match is not None:
        tier = int(tier_match.group("tier"))
        base = tier_match.group("rest")

    words: list[str] = []
    for token in base.split("_"):
        cleaned = token.strip()
        if not cleaned:
            continue
        upper = cleaned.upper()
        if upper in {"MAIN", "2H"}:
            continue
        mapped = _ITEM_ID_WORD_ALIASES.get(upper)
        if mapped is not None:
            words.append(mapped)
            continue
        if len(upper) <= 3 and upper.isalpha():
            words.append(upper)
            continue
        words.append(cleaned.replace("-", " ").title())

    item_name = " ".join(words).strip() or raw
    if tier is None:
        return item_name
    if enchant is not None and enchant > 0:
        return f"{item_name} {tier}.{enchant}"
    return f"{item_name} T{tier}"


def _item_id_candidates(item_id: str) -> tuple[str, ...]:
    base = str(item_id or "").strip()
    if not base:
        return ()
    out: list[str] = [base]
    if "@" in base:
        stem, raw = base.rsplit("@", 1)
        out.append(stem)
        try:
            level = int(raw)
        except ValueError:
            level = -1
        if level >= 0:
            out.append(f"{stem}_LEVEL{level}")
    level_match = _LEVEL_SUFFIX_RE.search(base)
    if level_match is not None:
        stem = base[: level_match.start()]
        out.append(stem)
    seen: set[str] = set()
    ordered: list[str] = []
    for value in out:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


def _mode_has_price(quote: MarketPriceRecord, preferred_mode: str | None) -> bool:
    mode = str(preferred_mode or "").strip().lower()
    if mode == PriceType.BUY_ORDER.value:
        return int(quote.buy_price_max or 0) > 0
    if mode == PriceType.SELL_ORDER.value:
        return int(quote.sell_price_min or 0) > 0
    if mode == PriceType.MANUAL.value:
        return True
    return int(quote.buy_price_max or 0) > 0 or int(quote.sell_price_min or 0) > 0


def _find_price_quote(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
    preferred_mode: str | None,
) -> MarketPriceRecord | None:
    candidates = _item_id_candidates(item_id)
    if not candidates:
        return None
    fallback: MarketPriceRecord | None = None
    quality_candidates = [int(quality)]
    if int(quality) != 1:
        quality_candidates.append(1)
    for candidate_id in candidates:
        for candidate_quality in quality_candidates:
            quote = price_index.get((candidate_id, city, candidate_quality))
            if quote is None:
                continue
            if _mode_has_price(quote, preferred_mode):
                return quote
            if fallback is None:
                fallback = quote
    for (candidate_id, candidate_city, _candidate_quality), quote in price_index.items():
        if candidate_city != city or candidate_id not in candidates:
            continue
        if _mode_has_price(quote, preferred_mode):
            return quote
        if fallback is None:
            fallback = quote
    return fallback


def _parse_iso_datetime(raw_value: str) -> datetime | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.year <= 2001:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_age(updated_at: datetime) -> str:
    now = datetime.now(timezone.utc)
    seconds = max(0, int((now - updated_at).total_seconds()))
    if seconds < 60:
        return "<1m"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        rem_minutes = minutes % 60
        if rem_minutes == 0:
            return f"{hours}h"
        return f"{hours}h {rem_minutes}m"
    days = hours // 24
    rem_hours = hours % 24
    if rem_hours == 0:
        return f"{days}d"
    return f"{days}d {rem_hours}h"


def _parse_recipe_filter(query: str) -> RecipeFilter:
    text = query.strip().lower()
    if not text:
        return RecipeFilter(terms=(), tier=None, enchant=None)

    tier: int | None = None
    enchant: int | None = None
    remainder = text
    match = _RECIPE_TIER_ENCHANT_RE.search(text)
    if match is not None:
        tier = int(match.group("tier"))
        enchant_raw = match.group("ench")
        enchant = int(enchant_raw) if enchant_raw is not None else None
        start, end = match.span()
        remainder = (text[:start] + " " + text[end:]).strip()

    clean = "".join(ch if ch.isalnum() else " " for ch in remainder)
    terms = tuple(part for part in clean.split() if part)
    return RecipeFilter(terms=terms, tier=tier, enchant=enchant)


def _matches_recipe_filter(row: RecipeOptionRow, recipe_filter: RecipeFilter) -> bool:
    if recipe_filter.tier is not None and int(row.tier or 0) != int(recipe_filter.tier):
        return False
    if recipe_filter.enchant is not None and int(row.enchant or 0) != int(recipe_filter.enchant):
        return False
    if not recipe_filter.terms:
        return True
    haystack = f"{row.display_name} {row.recipe_id}".lower()
    return all(term in haystack for term in recipe_filter.terms)
