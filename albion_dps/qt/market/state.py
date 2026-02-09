from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Property, Qt, Signal, Slot

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.engine import build_craft_run, compute_run_profit
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
    manual_price: int
    unit_price: float
    total_cost: float


class MarketInputsModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    ManualPriceRole = Qt.UserRole + 6
    UnitPriceRole = Qt.UserRole + 7
    TotalCostRole = Qt.UserRole + 8

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


class MarketOutputsModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    ManualPriceRole = Qt.UserRole + 6
    UnitPriceRole = Qt.UserRole + 7
    TotalValueRole = Qt.UserRole + 8

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


class RecipeOptionsModel(QAbstractListModel):
    RecipeIdRole = Qt.UserRole + 1
    DisplayNameRole = Qt.UserRole + 2

    def __init__(self) -> None:
        super().__init__()
        self._items: list[RecipeOptionRow] = []

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
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.RecipeIdRole: b"recipeId",
            self.DisplayNameRole: b"displayName",
        }

    def set_items(self, rows: list[RecipeOptionRow]) -> None:
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
            station_fee_percent=6.0,
            market_tax_percent=4.0,
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
        self._catalog = self._load_catalog()
        self._recipe = self._resolve_recipe(recipe_id)
        self._recipe_options_model.set_items(self._build_recipe_options())
        self._breakdown = ProfitBreakdown()
        self._input_price_types: dict[str, PriceType] = {
            component.item.unique_name: PriceType.SELL_ORDER
            for component in self._recipe.components
        }
        self._output_price_types: dict[str, PriceType] = {
            output.item.unique_name: PriceType.BUY_ORDER
            for output in self._recipe.outputs
        }
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

    @Property(float, notify=setupChanged)
    def stationFeePercent(self) -> float:
        return self._setup.station_fee_percent

    @Property(float, notify=setupChanged)
    def marketTaxPercent(self) -> float:
        return self._setup.market_tax_percent

    @Property(float, notify=setupChanged)
    def dailyBonusPercent(self) -> float:
        return self._setup.daily_bonus_percent

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
        return self._recipe.item.display_name or self._recipe.item.unique_name

    @Property(int, notify=setupChanged)
    def recipeTier(self) -> int:
        return int(self._recipe.item.tier or 0)

    @Property(int, notify=setupChanged)
    def recipeEnchant(self) -> int:
        return int(self._recipe.item.enchantment or 0)

    @Property(int, notify=setupChanged)
    def recipeIndex(self) -> int:
        return self._recipe_options_model.index_of_recipe(self.recipeId)

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

    @Property(str, notify=validationChanged)
    def validationText(self) -> str:
        errors = validate_setup(self._setup)
        if self._craft_runs <= 0:
            errors.append("craftRuns must be > 0")
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
        self._input_price_types = {
            component.item.unique_name: PriceType.SELL_ORDER
            for component in self._recipe.components
        }
        self._output_price_types = {
            output.item.unique_name: PriceType.BUY_ORDER
            for output in self._recipe.outputs
        }
        self._manual_input_prices = {}
        self._manual_output_prices = {}
        self._output_cities = {}
        self._price_index = {}
        self._price_context_key = None
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

    @Slot(float)
    def setStationFeePercent(self, value: float) -> None:
        self._replace(station_fee_percent=float(value))

    @Slot(float)
    def setMarketTaxPercent(self, value: float) -> None:
        self._replace(market_tax_percent=float(value))

    @Slot(float)
    def setDailyBonusPercent(self, value: float) -> None:
        self._replace(daily_bonus_percent=float(value))

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
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def refreshPrices(self) -> None:
        self._rebuild_preview(force_price_refresh=True)

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
        setup = CraftSetup(
            region=kwargs.get("region", self._setup.region),
            craft_city=kwargs.get("craft_city", self._setup.craft_city),
            default_buy_city=kwargs.get("default_buy_city", self._setup.default_buy_city),
            default_sell_city=kwargs.get("default_sell_city", self._setup.default_sell_city),
            premium=kwargs.get("premium", self._setup.premium),
            station_fee_percent=kwargs.get("station_fee_percent", self._setup.station_fee_percent),
            market_tax_percent=kwargs.get("market_tax_percent", self._setup.market_tax_percent),
            daily_bonus_percent=kwargs.get("daily_bonus_percent", self._setup.daily_bonus_percent),
            return_rate_percent=kwargs.get("return_rate_percent", self._setup.return_rate_percent),
            hideout_power_percent=kwargs.get("hideout_power_percent", self._setup.hideout_power_percent),
            quality=kwargs.get("quality", self._setup.quality),
        )
        self._setup = sanitized_setup(setup)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    def _rebuild_preview(self, *, force_price_refresh: bool) -> None:
        setup = self.to_setup()
        price_index = self._current_price_index(setup, force_refresh=force_price_refresh)
        try:
            run = build_craft_run(
                recipe=self._recipe,
                quantity=self._craft_runs,
                setup=setup,
                price_index=price_index,
                input_price_types=dict(self._input_price_types),
                output_cities=dict(self._output_cities),
                output_price_types=dict(self._output_price_types),
                manual_input_prices=dict(self._manual_input_prices),
                manual_output_prices=dict(self._manual_output_prices),
            )
        except Exception:
            self._inputs_model.set_items([])
            self._outputs_model.set_items([])
            self._shopping_model.set_items([])
            self._selling_model.set_items([])
            self._results_items_model.set_items([])
            self._breakdown_model.set_items([])
            self._shopping_csv = ""
            self._selling_csv = ""
            self._breakdown = ProfitBreakdown(notes=["preview build failed"])
            self.inputsChanged.emit()
            self.outputsChanged.emit()
            self.resultsChanged.emit()
            self.listsChanged.emit()
            self.resultsDetailsChanged.emit()
            return

        input_rows = [
            InputPreviewRow(
                item_id=line.item.unique_name,
                item=line.item.display_name or line.item.unique_name,
                quantity=float(line.quantity),
                city=line.city,
                price_type=line.price_type.value,
                manual_price=self._manual_input_prices.get(line.item.unique_name, 0),
                unit_price=float(line.unit_price),
                total_cost=float(line.total_cost),
            )
            for line in run.inputs
        ]
        output_rows = [
            OutputPreviewRow(
                item_id=line.item.unique_name,
                item=line.item.display_name or line.item.unique_name,
                quantity=float(line.quantity),
                city=line.city,
                price_type=line.price_type.value,
                manual_price=self._manual_output_prices.get(line.item.unique_name, 0),
                unit_price=float(line.unit_price),
                total_value=float(line.total_value),
            )
            for line in run.outputs
        ]
        self._inputs_model.set_items(input_rows)
        self._outputs_model.set_items(output_rows)
        self._breakdown = compute_run_profit(run)

        shopping_rows = [
            ShoppingPreviewRow(
                item_id=entry.item_id,
                item=entry.item_name,
                quantity=float(entry.quantity),
                city=entry.city,
                price_type=entry.price_type,
                unit_price=float(entry.unit_price),
                total_cost=float(entry.total_cost),
            )
            for entry in build_shopping_entries(list(run.inputs))
        ]
        selling_rows = [
            SellingPreviewRow(
                item_id=entry.item_id,
                item=entry.item_name,
                quantity=float(entry.quantity),
                city=entry.city,
                price_type=entry.price_type,
                unit_price=float(entry.unit_price),
                total_value=float(entry.total_value),
            )
            for entry in build_selling_entries(list(run.outputs))
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
            fee_value = float(self._breakdown.station_fee) * share
            tax_value = float(self._breakdown.market_tax) * share
            profit = output.total_value - allocated_cost - fee_value - tax_value
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
        focus_impact = 0.0
        if self._breakdown.focus_used > 0:
            focus_impact = float(self._breakdown.net_profit / self._breakdown.focus_used)
        return [
            BreakdownRow(label="Raw materials", value=float(self._breakdown.input_cost)),
            BreakdownRow(label="Station fee", value=float(self._breakdown.station_fee)),
            BreakdownRow(label="Market tax", value=float(self._breakdown.market_tax)),
            BreakdownRow(label="Net profit", value=float(self._breakdown.net_profit)),
            BreakdownRow(label="Focus impact (silver/focus)", value=float(focus_impact)),
        ]

    def _demand_proxy_percent(self, *, item_id: str, city: str, quality: int) -> float:
        quote = self._price_index.get((item_id, city, quality)) or self._price_index.get((item_id, city, 1))
        if quote is None:
            return 0.0
        if quote.sell_price_min <= 0 or quote.buy_price_max <= 0:
            return 0.0
        return (float(quote.buy_price_max) / float(quote.sell_price_min)) * 100.0

    def _set_list_action_text(self, text: str) -> None:
        self._list_action_text = text
        self.listsChanged.emit()

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
        item_ids = sorted(
            {
                *(x.item.unique_name for x in self._recipe.components),
                *(x.item.unique_name for x in self._recipe.outputs),
            }
        )
        locations = sorted(
            {
                setup.craft_city.strip(),
                setup.default_buy_city.strip(),
                setup.default_sell_city.strip(),
            }
            - {""}
        )
        if not locations:
            locations = ["Bridgewatch"]
        context_key = self._price_key(setup)
        if not force and self._price_index and context_key == self._price_context_key:
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
                allow_stale=True,
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

    def _price_key(self, setup: CraftSetup) -> tuple[str, int, tuple[str, ...], tuple[str, ...]]:
        item_ids = tuple(
            sorted(
                {
                    *(x.item.unique_name for x in self._recipe.components),
                    *(x.item.unique_name for x in self._recipe.outputs),
                }
            )
        )
        locations = tuple(
            sorted(
                {
                    setup.craft_city.strip(),
                    setup.default_buy_city.strip(),
                    setup.default_sell_city.strip(),
                }
                - {""}
            )
        )
        return (setup.region.value, int(setup.quality), item_ids, locations)

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
                    display_name=recipe.item.display_name or recipe.item.unique_name,
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
        locations = {
            setup.craft_city.strip(),
            setup.default_buy_city.strip(),
            setup.default_sell_city.strip(),
            "Bridgewatch",
        }
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
        for component in self._recipe.components:
            item_id = component.item.unique_name
            prices[item_id] = known_prices.get(item_id, self._price_by_tier(component.item.tier))

        component_sell_total = 0.0
        for component in self._recipe.components:
            buy_price, sell_price = prices.get(
                component.item.unique_name,
                self._price_by_tier(component.item.tier),
            )
            _ = buy_price
            component_sell_total += sell_price * component.quantity

        outputs = self._recipe.outputs or ()
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
