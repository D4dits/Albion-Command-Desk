from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Property, Qt, Signal, Slot

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.engine import build_craft_run, compute_run_profit
from albion_dps.market.models import (
    CraftSetup,
    ItemRef,
    MarketRegion,
    PriceType,
    ProfitBreakdown,
    Recipe,
    RecipeComponent,
    RecipeOutput,
)
from albion_dps.market.setup import sanitized_setup, validate_setup


@dataclass(frozen=True)
class InputPreviewRow:
    item: str
    quantity: float
    city: str
    price_type: str
    unit_price: float
    total_cost: float


class MarketInputsModel(QAbstractListModel):
    ItemRole = Qt.UserRole + 1
    QuantityRole = Qt.UserRole + 2
    CityRole = Qt.UserRole + 3
    PriceTypeRole = Qt.UserRole + 4
    UnitPriceRole = Qt.UserRole + 5
    TotalCostRole = Qt.UserRole + 6

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
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.UnitPriceRole: b"unitPrice",
            self.TotalCostRole: b"totalCost",
        }

    def set_items(self, rows: list[InputPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class OutputPreviewRow:
    item: str
    quantity: float
    city: str
    price_type: str
    unit_price: float
    total_value: float


class MarketOutputsModel(QAbstractListModel):
    ItemRole = Qt.UserRole + 1
    QuantityRole = Qt.UserRole + 2
    CityRole = Qt.UserRole + 3
    PriceTypeRole = Qt.UserRole + 4
    UnitPriceRole = Qt.UserRole + 5
    TotalValueRole = Qt.UserRole + 6

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
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.UnitPriceRole: b"unitPrice",
            self.TotalValueRole: b"totalValue",
        }

    def set_items(self, rows: list[OutputPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


class MarketSetupState(QObject):
    setupChanged = Signal()
    validationChanged = Signal()
    inputsChanged = Signal()
    outputsChanged = Signal()
    resultsChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
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
        self._recipe = self._build_recipe()
        self._breakdown = ProfitBreakdown()
        self._rebuild_preview()

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

    @Property(QObject, constant=True)
    def inputsModel(self) -> QObject:
        return self._inputs_model

    @Property(QObject, constant=True)
    def outputsModel(self) -> QObject:
        return self._outputs_model

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
        self._rebuild_preview()
        self.setupChanged.emit()
        self.validationChanged.emit()

    def to_setup(self) -> CraftSetup:
        return sanitized_setup(self._setup)

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
        self._rebuild_preview()
        self.setupChanged.emit()
        self.validationChanged.emit()

    def _rebuild_preview(self) -> None:
        setup = self.to_setup()
        price_index = self._build_price_index(setup)
        try:
            run = build_craft_run(
                recipe=self._recipe,
                quantity=self._craft_runs,
                setup=setup,
                price_index=price_index,
                input_price_types={
                    "T4_METALBAR": PriceType.SELL_ORDER,
                    "T4_PLANKS": PriceType.SELL_ORDER,
                },
                output_price_types={
                    self._recipe.item.unique_name: PriceType.BUY_ORDER,
                },
            )
        except Exception:
            self._inputs_model.set_items([])
            self._outputs_model.set_items([])
            self._breakdown = ProfitBreakdown(notes=["preview build failed"])
            self.inputsChanged.emit()
            self.outputsChanged.emit()
            self.resultsChanged.emit()
            return

        input_rows = [
            InputPreviewRow(
                item=line.item.unique_name,
                quantity=float(line.quantity),
                city=line.city,
                price_type=line.price_type.value,
                unit_price=float(line.unit_price),
                total_cost=float(line.total_cost),
            )
            for line in run.inputs
        ]
        output_rows = [
            OutputPreviewRow(
                item=line.item.unique_name,
                quantity=float(line.quantity),
                city=line.city,
                price_type=line.price_type.value,
                unit_price=float(line.unit_price),
                total_value=float(line.total_value),
            )
            for line in run.outputs
        ]
        self._inputs_model.set_items(input_rows)
        self._outputs_model.set_items(output_rows)
        self._breakdown = compute_run_profit(run)
        self.inputsChanged.emit()
        self.outputsChanged.emit()
        self.resultsChanged.emit()

    @staticmethod
    def _build_recipe() -> Recipe:
        sword = ItemRef(
            unique_name="T4_MAIN_SWORD",
            display_name="Broadsword",
            tier=4,
            enchantment=0,
        )
        bars = ItemRef(
            unique_name="T4_METALBAR",
            display_name="Metal Bar",
            tier=4,
            enchantment=0,
        )
        planks = ItemRef(
            unique_name="T4_PLANKS",
            display_name="Planks",
            tier=4,
            enchantment=0,
        )
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

    def _build_price_index(
        self,
        setup: CraftSetup,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        locations = {
            setup.craft_city.strip(),
            setup.default_buy_city.strip(),
            setup.default_sell_city.strip(),
            "Bridgewatch",
        }
        prices = {
            "T4_METALBAR": (900, 1000),
            "T4_PLANKS": (500, 600),
            "T4_MAIN_SWORD": (15000, 15500),
        }
        index: dict[tuple[str, str, int], MarketPriceRecord] = {}
        for location in locations:
            if not location:
                continue
            for item_id, (buy_price, sell_price) in prices.items():
                record = MarketPriceRecord(
                    item_id=item_id,
                    city=location,
                    quality=int(setup.quality),
                    sell_price_min=int(sell_price),
                    buy_price_max=int(buy_price),
                    sell_price_min_date="",
                    buy_price_max_date="",
                )
                index[(item_id, location, int(setup.quality))] = record
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
