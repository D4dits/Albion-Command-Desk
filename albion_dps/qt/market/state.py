from __future__ import annotations

import json
import logging
import math
import os
import time
from math import ceil
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from PySide6.QtCore import QCoreApplication, QObject, Property, Qt, QTimer, Signal, Slot

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.engine import (
    compute_batch_profit,
    compute_output_valuations,
    effective_return_fraction,
)
from albion_dps.market.models import (
    CraftRun,
    CraftSetup,
    InputLine,
    ItemRef,
    MarketRegion,
    PriceType,
    ProfitBreakdown,
    Recipe,
)
from albion_dps.market.planner import build_selling_entries, build_shopping_entries
from albion_dps.market.service import MarketDataService
from albion_dps.market.setup import sanitized_setup, validate_setup
from albion_dps.qt.market.list_models import (
    BreakdownRow,
    CraftPlanModel,
    CraftPlanRow,
    InputPreviewRow,
    MarketBreakdownModel,
    MarketInputsModel,
    MarketOutputsModel,
    MarketResultsItemsModel,
    MarketSellingModel,
    MarketShoppingModel,
    RecipeOptionRow,
    RecipeOptionsModel,
    ResultItemRow,
    SellingPreviewRow,
    ShoppingPreviewRow,
)
from albion_dps.qt.market import common_ops
from albion_dps.qt.market import catalog_ops
from albion_dps.qt.market import journal_ops
from albion_dps.qt.market import preset_ops
from albion_dps.qt.market import pricing_ops
from albion_dps.qt.market import price_refresh_ops
from albion_dps.qt.market import preview_flow_ops
from albion_dps.qt.market import preview_metric_ops
from albion_dps.qt.market import preview_render_ops
from albion_dps.qt.market import preview_state_ops
from albion_dps.qt.market import quote_ops
from albion_dps.qt.market import recipe_ops
from albion_dps.qt.market import selection_ops
from albion_dps.qt.market import ui_ops
from albion_dps.qt.market.state_types import _JournalLine, _JournalRule, _JournalTotals
from albion_dps.settings import load_app_settings, update_app_settings


class MarketSetupState(QObject):
    setupChanged = Signal()
    validationChanged = Signal()
    pricesChanged = Signal()
    inputsChanged = Signal()
    outputsChanged = Signal()
    resultsChanged = Signal()
    listsChanged = Signal()
    resultsDetailsChanged = Signal()
    diagnosticsChanged = Signal()

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
        self._inputs_on_model = MarketInputsModel()
        self._outputs_model = MarketOutputsModel()
        self._outputs_on_model = MarketOutputsModel()
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
        self._craft_plan_recipe_ids: set[str] = set()
        self._next_plan_row_id = 1
        self._breakdown = ProfitBreakdown()
        self._base_input_total_cost = 0.0
        self._journal_totals = _JournalTotals()
        self._results_journal_totals = _JournalTotals()
        self._selected_material_input_total_cost = 0.0
        self._selected_input_total_cost = 0.0
        self._selected_output_total_value = 0.0
        self._selected_output_net_value = 0.0
        self._selected_net_profit_value = 0.0
        self._selected_margin_percent = 0.0
        self._selected_input_item_ids: list[str] = []
        self._selected_output_item_ids: list[str] = []
        self._input_price_types: dict[str, PriceType] = {}
        self._output_price_types: dict[str, PriceType] = {}
        self._manual_input_prices: dict[str, int] = {}
        self._input_stock_quantities: dict[str, float] = {}
        self._completed_input_item_ids: set[str] = set()
        self._manual_output_prices: dict[str, int] = {}
        self._completed_output_item_ids: set[str] = set()
        self._output_cities: dict[str, str] = {}
        self._price_index: dict[tuple[str, str, int], MarketPriceRecord] = {}
        self._price_context_key: tuple[str, int, tuple[str, ...], tuple[str, ...]] | None = None
        self._prices_source = "fallback"
        self._prices_status_text = "Using bundled fallback prices."
        self._price_fetch_in_progress = False
        self._price_fetch_thread: Any | None = None
        self._price_fetch_result_queue: Any | None = None
        self._pending_price_context_key: Any | None = None
        self._pending_price_force = False
        self._results_sort_key = "profit"
        self._shopping_csv = ""
        self._selling_csv = ""
        self._results_csv = ""
        self._list_action_text = ""
        self._diagnostics_lines: list[str] = []
        self._recipe_search_query = ""
        self._recipe_tier_filters: list[int] = []
        self._recipe_enchant_filters: list[int] = []
        self._hide_rows_without_fresh_prices = False
        self._app_settings = load_app_settings()
        self._default_export_dir = str(self._app_settings.market_export_dir or "").strip()
        self._preset_path = _default_preset_path()
        self._presets: dict[str, dict[str, object]] = self._load_presets()
        self._selected_preset_name = str(self._app_settings.market_selected_preset or "").strip()
        self._craft_plan_sort_key = "added"
        self._craft_plan_sort_desc = False
        self._active_market_tab_index = 0
        self._market_data_tabs_live_bootstrap_done = False
        self._manual_refresh_cooldown_seconds = 30.0
        self._min_live_refresh_interval_seconds = 2.0
        self._rate_limit_cooldown_seconds = 90.0
        self._next_live_fetch_not_before = 0.0
        self._deferred_price_refresh_timer = QTimer(self)
        self._deferred_price_refresh_timer.setSingleShot(True)
        self._deferred_price_refresh_timer.timeout.connect(self._on_deferred_price_refresh_timeout)
        self._price_fetch_result_timer = QTimer(self)
        self._price_fetch_result_timer.setInterval(50)
        self._price_fetch_result_timer.timeout.connect(self._on_async_price_fetch_poll)
        self._deferred_preview_rebuild_timer = QTimer(self)
        self._deferred_preview_rebuild_timer.setSingleShot(True)
        self._deferred_preview_rebuild_timer.timeout.connect(self._on_deferred_preview_rebuild_timeout)
        self._deferred_force_preview_rebuild = False
        self._refresh_cooldown_tick_timer = QTimer(self)
        self._refresh_cooldown_tick_timer.setInterval(1000)
        self._refresh_cooldown_tick_timer.timeout.connect(self._on_refresh_cooldown_tick)
        self._deferred_force_price_refresh = False
        if self._selected_preset_name and self._selected_preset_name in self._presets:
            self._apply_preset_payload(self._selected_preset_name, self._presets[self._selected_preset_name])
        self._ensure_price_preferences_for_recipe(self._recipe)
        if auto_refresh_prices and self._service is not None:
            self._refresh_price_index(self.to_setup(), force=True)
        self._rebuild_preview(force_price_refresh=False)
        self._append_diag("Market state initialized.", level="INFO")

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
        return _recipe_identity(self._recipe)

    @Property(str, notify=setupChanged)
    def recipeDisplayName(self) -> str:
        return _recipe_display_label(self._recipe)

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

    @Property(int, notify=setupChanged)
    def recipeEnchantFilter(self) -> int:
        if not self._recipe_enchant_filters:
            return -1
        return int(self._recipe_enchant_filters[0])

    @Property("QVariantList", notify=setupChanged)
    def recipeTierFilters(self) -> list[int]:
        return list(self._recipe_tier_filters)

    @Property("QVariantList", notify=setupChanged)
    def recipeEnchantFilters(self) -> list[int]:
        return list(self._recipe_enchant_filters)

    @Property(bool, notify=setupChanged)
    def hideRowsWithoutFreshPrices(self) -> bool:
        return bool(self._hide_rows_without_fresh_prices)

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

    @Property(bool, notify=pricesChanged)
    def priceFetchInProgress(self) -> bool:
        return self._price_fetch_in_progress

    @Property(bool, notify=pricesChanged)
    def priceFetchPending(self) -> bool:
        return self._price_fetch_in_progress or self._deferred_price_refresh_timer.isActive()

    @Property(int, notify=pricesChanged)
    def refreshCooldownSeconds(self) -> int:
        remaining = self._next_live_fetch_not_before - time.monotonic()
        if remaining <= 0:
            return 0
        return int(ceil(remaining))

    @Property(bool, notify=pricesChanged)
    def canRefreshPrices(self) -> bool:
        return (not self._price_fetch_in_progress) and self.refreshCooldownSeconds <= 0

    @Property(str, notify=pricesChanged)
    def refreshPricesButtonText(self) -> str:
        if self.refreshCooldownSeconds > 0:
            return f"Refresh in {self.refreshCooldownSeconds}s"
        return "Refresh prices"

    @Property(QObject, constant=True)
    def inputsModel(self) -> QObject:
        return self._inputs_model

    @Property(QObject, constant=True)
    def inputsOnModel(self) -> QObject:
        return self._inputs_on_model

    @Property(QObject, constant=True)
    def outputsModel(self) -> QObject:
        return self._outputs_model

    @Property(QObject, constant=True)
    def outputsOnModel(self) -> QObject:
        return self._outputs_on_model

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

    @Property(str, notify=setupChanged)
    def craftPlanSortKey(self) -> str:
        return self._craft_plan_sort_key

    @Property(bool, notify=setupChanged)
    def craftPlanSortDescending(self) -> bool:
        return self._craft_plan_sort_desc

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

    @Property(str, notify=resultsChanged)
    def resultsCsv(self) -> str:
        return self._results_csv

    @Property(str, notify=listsChanged)
    def listActionText(self) -> str:
        return self._list_action_text

    @Property(str, notify=diagnosticsChanged)
    def diagnosticsText(self) -> str:
        return "\n".join(self._diagnostics_lines)

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
        return float(total)

    @Property(float, notify=outputsChanged)
    def outputsTotalValue(self) -> float:
        total = 0.0
        for idx in range(self._outputs_model.rowCount()):
            model_index = self._outputs_model.index(idx, 0)
            value = self._outputs_model.data(model_index, MarketOutputsModel.TotalValueRole)
            if value is not None:
                total += float(value)
        return float(total)

    @Property(float, notify=outputsChanged)
    def outputsNetValue(self) -> float:
        total = 0.0
        for idx in range(self._outputs_model.rowCount()):
            model_index = self._outputs_model.index(idx, 0)
            value = self._outputs_model.data(model_index, MarketOutputsModel.NetValueRole)
            if value is not None:
                total += float(value)
        return float(total)

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
    def selectedInputsTotalCost(self) -> float:
        return float(self._selected_input_total_cost)

    @Property(float, notify=resultsChanged)
    def selectedOutputsTotalValue(self) -> float:
        return float(self._selected_output_total_value)

    @Property(float, notify=resultsChanged)
    def selectedOutputsNetValue(self) -> float:
        return float(self._selected_output_net_value)

    @Property(float, notify=resultsChanged)
    def selectedNetProfitValue(self) -> float:
        return float(self._selected_net_profit_value)

    @Property(float, notify=resultsChanged)
    def selectedMarginPercent(self) -> float:
        return float(self._selected_margin_percent)

    @Property("QVariantList", notify=inputsChanged)
    def selectedInputItemIds(self) -> list[str]:
        return list(self._selected_input_item_ids)

    @Property("QVariantList", notify=outputsChanged)
    def selectedOutputItemIds(self) -> list[str]:
        return list(self._selected_output_item_ids)

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
        row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
        if row is not None:
            setup = self._setup_for_plan_row(setup, row)
        return float(effective_return_fraction(setup=setup, recipe=self._recipe) * 100.0)

    @Property(str, notify=validationChanged)
    def validationText(self) -> str:
        errors = validate_setup(self._setup)
        if self._craft_runs <= 0:
            errors.append("craftRuns must be > 0")
        if not self._craft_plan_rows:
            errors.append("craftPlan must contain at least one recipe")
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
    def setActiveMarketTab(self, index: int) -> None:
        normalized = max(0, int(index))
        if normalized == self._active_market_tab_index:
            return
        self._active_market_tab_index = normalized
        if self._active_market_tab_index >= 1:
            if not self._should_defer_price_refresh():
                self._rebuild_preview(force_price_refresh=False)
            elif not self._market_data_tabs_live_bootstrap_done:
                # First data-tab visit: schedule async refresh so UI can paint loading state.
                self._schedule_deferred_price_refresh(0.05, force=False)
            else:
                # Subsequent tab switches: rebuild synchronously using current data (no loading flash).
                self._rebuild_preview(force_price_refresh=False)

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
        if _recipe_identity(recipe) == _recipe_identity(self._recipe):
            return
        self._recipe = recipe
        self._ensure_price_preferences_for_recipe(self._recipe)
        plan_row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
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

    @Slot(int)
    def setRecipeEnchantFilter(self, value: int) -> None:
        raw = int(value)
        if raw < 0:
            self.setRecipeEnchantFilters([])
            return
        if raw > 4:
            return
        self.setRecipeEnchantFilters([raw])

    @Slot("QVariantList")
    def setRecipeTierFilters(self, values: list[object]) -> None:
        normalized = self._normalize_int_filter_list(values, minimum=1, maximum=8)
        if normalized == self._recipe_tier_filters:
            return
        self._recipe_tier_filters = normalized
        self._recipe_options_model.set_tier_filters(normalized)
        self.setupChanged.emit()

    @Slot("QVariantList")
    def setRecipeEnchantFilters(self, values: list[object]) -> None:
        normalized = self._normalize_int_filter_list(values, minimum=0, maximum=4)
        if normalized == self._recipe_enchant_filters:
            return
        self._recipe_enchant_filters = normalized
        self._recipe_options_model.set_enchant_filters(normalized)
        self.setupChanged.emit()

    @Slot(bool)
    def setHideRowsWithoutFreshPrices(self, enabled: bool) -> None:
        normalized = bool(enabled)
        if normalized == self._hide_rows_without_fresh_prices:
            return
        self._hide_rows_without_fresh_prices = normalized
        self.setupChanged.emit()
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str)
    def setSelectedPresetName(self, value: str) -> None:
        name = value.strip()
        if name == self._selected_preset_name:
            return
        self._selected_preset_name = name
        self._persist_app_settings()
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
            "recipe_id": _recipe_identity(self._recipe),
            "recipe_search_query": self._recipe_search_query,
            "recipe_tier_filters": list(self._recipe_tier_filters),
            "recipe_enchant_filters": list(self._recipe_enchant_filters),
            "hide_rows_without_fresh_prices": bool(self._hide_rows_without_fresh_prices),
            "craft_plan": [_craft_plan_row_to_dict(row) for row in self._craft_plan_rows],
        }
        if self._save_presets():
            self._selected_preset_name = name
            self._persist_app_settings()
            self._set_list_action_text(f"Preset saved: {name}")
            self._append_diag(f"Preset saved: {name}", level="INFO")
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
        if not self._apply_preset_payload(name, payload):
            self._set_list_action_text(f"Preset is invalid: {name}")
            return
        self._persist_app_settings()
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()
        self._set_list_action_text(f"Preset loaded: {name}")
        self._append_diag(f"Preset loaded: {name}", level="INFO")

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
            self._persist_app_settings()
            self._set_list_action_text(f"Preset deleted: {name}")
            self._append_diag(f"Preset deleted: {name}", level="INFO")
            self.setupChanged.emit()

    def _apply_preset_payload(self, name: str, payload: object) -> bool:
        if not isinstance(payload, dict):
            return False
        setup_data = payload.get("setup")
        if not isinstance(setup_data, dict):
            return False

        self._setup = sanitized_setup(_setup_from_dict(setup_data, fallback=self._setup))
        loaded_rows = _craft_plan_rows_from_payload(
            payload.get("craft_plan"),
            catalog=self._catalog,
            fallback_city=self._setup.craft_city,
            fallback_daily_bonus_percent=float(self._setup.daily_bonus_percent),
        )
        if loaded_rows is not None:
            self._craft_plan_rows = loaded_rows
            self._rebuild_craft_plan_recipe_index()
            self._next_plan_row_id = max((row.row_id for row in loaded_rows), default=0) + 1
            self._sync_craft_plan_model()
            for plan_row in self._craft_plan_rows:
                plan_recipe = self._catalog.get(plan_row.recipe_id)
                if plan_recipe is not None:
                    self._ensure_price_preferences_for_recipe(plan_recipe)

        recipe_id = str(payload.get("recipe_id") or "").strip()
        if recipe_id and self._catalog.get(recipe_id) is not None:
            self._recipe = self._resolve_recipe(recipe_id)
        elif self._craft_plan_rows:
            self._recipe = self._resolve_recipe(self._craft_plan_rows[0].recipe_id)
        self._ensure_price_preferences_for_recipe(self._recipe)

        search_query = str(payload.get("recipe_search_query") or "").strip()
        self._recipe_search_query = search_query
        self._recipe_options_model.set_query(search_query)
        tier_filters = payload.get("recipe_tier_filters")
        enchant_filters = payload.get("recipe_enchant_filters")
        self._recipe_tier_filters = self._normalize_int_filter_list(
            tier_filters if isinstance(tier_filters, list) else [],
            minimum=1,
            maximum=8,
        )
        self._recipe_enchant_filters = self._normalize_int_filter_list(
            enchant_filters if isinstance(enchant_filters, list) else [],
            minimum=0,
            maximum=4,
        )
        self._recipe_options_model.set_tier_filters(self._recipe_tier_filters)
        self._recipe_options_model.set_enchant_filters(self._recipe_enchant_filters)
        self._hide_rows_without_fresh_prices = bool(payload.get("hide_rows_without_fresh_prices", False))

        self._craft_runs = max(1, int(payload.get("craft_runs") or self._craft_runs))
        active_row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
        if active_row is not None:
            self._craft_runs = max(1, int(active_row.runs))
        self._selected_preset_name = name
        return True

    def _persist_app_settings(self) -> None:
        try:
            self._app_settings = update_app_settings(
                market_selected_preset=str(self._selected_preset_name or ""),
                market_export_dir=str(self._default_export_dir or ""),
            )
        except Exception as exc:
            self._log.warning("Market app settings save failed: %s", exc)

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
    def addFilteredRecipeOptions(self) -> None:
        recipe_ids = self._recipe_options_model.recipe_ids()
        if not recipe_ids:
            self._set_list_action_text("No recipes match current filters.")
            return
        added = 0
        for recipe_id in recipe_ids:
            if self._add_recipe_to_plan_internal(recipe_id, runs=self._craft_runs, enabled=False, sync_model=False):
                added += 1
        if added <= 0:
            self._set_list_action_text("No new recipes were added.")
            return
        self._sync_craft_plan_model()
        self._set_list_action_text(f"Added {added} recipes to craft plan (On = off).")
        self._request_preview_rebuild(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def addRecipeFamily(self) -> None:
        family_ids: list[str] = []
        if self._recipe_search_query.strip():
            filtered_ids = self._recipe_options_model.recipe_ids()
            family_ids = self._station_recipe_ids_for_filtered(filtered_ids)
            if not family_ids:
                family_ids = self._family_recipe_ids_for_filtered(filtered_ids)
        else:
            family_ids = self._station_recipe_ids(_recipe_identity(self._recipe))
            if not family_ids:
                family_ids = self._family_recipe_ids(_recipe_identity(self._recipe))
        if not family_ids:
            self._set_list_action_text("No recipes found for selected family.")
            return
        added = 0
        for recipe_id in family_ids:
            if self._add_recipe_to_plan_internal(recipe_id, runs=self._craft_runs, enabled=False, sync_model=False):
                added += 1
        if added <= 0:
            self._set_list_action_text("No new family recipes were added.")
            return
        self._sync_craft_plan_model()
        self._set_list_action_text(f"Added {added} family recipes (On = off).")
        if self._craft_plan_rows:
            self._request_preview_rebuild(force_price_refresh=False)
        else:
            self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def addCurrentRecipeToPlan(self) -> None:
        added = self._add_recipe_to_plan_internal(_recipe_identity(self._recipe), runs=self._craft_runs, enabled=False)
        if not added:
            row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
            if row is not None and row.runs != self._craft_runs:
                self._update_plan_row(row.row_id, runs=self._craft_runs)
        self._request_preview_rebuild(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(str)
    def addRecipeToPlan(self, recipe_id: str) -> None:
        added = self._add_recipe_to_plan_internal(recipe_id, runs=self._craft_runs, enabled=False)
        if not added:
            row = self._find_plan_row_by_recipe(recipe_id)
            if row is not None and row.runs != self._craft_runs:
                self._update_plan_row(row.row_id, runs=self._craft_runs)
        self._request_preview_rebuild(force_price_refresh=False)
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
        self._rebuild_craft_plan_recipe_index()
        self._sync_craft_plan_model()
        if not any(row.recipe_id == _recipe_identity(self._recipe) for row in self._craft_plan_rows):
            if self._craft_plan_rows:
                self._recipe = self._resolve_recipe(self._craft_plan_rows[0].recipe_id)
                self._craft_runs = max(1, int(self._craft_plan_rows[0].runs))
                self._ensure_price_preferences_for_recipe(self._recipe)
        self._request_preview_rebuild(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, bool)
    def setPlanRowEnabled(self, row_id: int, enabled: bool) -> None:
        if not self._update_plan_row(row_id, enabled=bool(enabled)):
            return
        self._request_preview_rebuild(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, int)
    def setPlanRowRuns(self, row_id: int, runs: int) -> None:
        normalized = max(1, int(runs))
        if not self._update_plan_row(row_id, runs=normalized):
            return
        row = self._find_plan_row(row_id)
        if row is not None and row.recipe_id == _recipe_identity(self._recipe):
            self._craft_runs = normalized
        self._request_preview_rebuild(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, str)
    def setPlanRowCraftCity(self, row_id: int, craft_city: str) -> None:
        city_value = craft_city.strip()
        if not city_value:
            city_value = self._setup.craft_city
        if not self._update_plan_row(row_id, craft_city=city_value):
            return
        self._request_preview_rebuild(force_price_refresh=False)
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
        self._request_preview_rebuild(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def clearCraftPlan(self) -> None:
        self._craft_plan_rows = []
        self._craft_plan_recipe_ids.clear()
        self._next_plan_row_id = 1
        self._completed_input_item_ids.clear()
        self._completed_output_item_ids.clear()
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
        row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
        if row is not None and row.runs != runs:
            self._update_plan_row(row.row_id, runs=runs)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def refreshPrices(self) -> None:
        price_refresh_ops.refresh_prices(self)

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
            self._append_diag("Opened AOData raw URL in browser.", level="INFO")
        else:
            self._set_list_action_text(f"AOData URL: {url}")
            self._append_diag("Failed to open browser; AOData URL copied to status.", level="WARN")

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
    def setInputStockQuantity(self, item_id: str, raw_value: str) -> None:
        quantity = _parse_float(raw_value)
        if quantity <= 0:
            self._input_stock_quantities.pop(item_id, None)
        else:
            self._input_stock_quantities[item_id] = quantity
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, bool)
    def setInputRowCompleted(self, item_id: str, completed: bool) -> None:
        normalized_item_id = str(item_id or "").strip()
        if not normalized_item_id:
            return
        if completed:
            if normalized_item_id in self._completed_input_item_ids:
                return
            self._completed_input_item_ids.add(normalized_item_id)
        else:
            if normalized_item_id not in self._completed_input_item_ids:
                return
            self._completed_input_item_ids.discard(normalized_item_id)
        self._inputs_model.set_completed_by_item_id(normalized_item_id, completed)
        self._inputs_on_model.set_completed_by_item_id(normalized_item_id, completed)
        self.inputsChanged.emit()

    @Slot(str, bool)
    def setOutputRowCompleted(self, item_id: str, completed: bool) -> None:
        normalized_item_id = str(item_id or "").strip()
        if not normalized_item_id:
            return
        if completed:
            if normalized_item_id in self._completed_output_item_ids:
                return
            self._completed_output_item_ids.add(normalized_item_id)
        else:
            if normalized_item_id not in self._completed_output_item_ids:
                return
            self._completed_output_item_ids.discard(normalized_item_id)
        self._outputs_model.set_completed_by_item_id(normalized_item_id, completed)
        self._outputs_on_model.set_completed_by_item_id(normalized_item_id, completed)
        self.outputsChanged.emit()

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

    @Slot(str)
    def setCraftPlanSortKey(self, key: str) -> None:
        normalized = key.strip().lower()
        if normalized not in {"added", "craft", "tier", "city", "pl"}:
            return
        changed = normalized != self._craft_plan_sort_key
        self._craft_plan_sort_key = normalized
        if normalized == "pl" and not self._craft_plan_sort_desc:
            self._craft_plan_sort_desc = True
            changed = True
        if not changed:
            return
        self._sync_craft_plan_model()
        self.setupChanged.emit()

    @Slot(bool)
    def setCraftPlanSortDescending(self, value: bool) -> None:
        normalized = bool(value)
        if normalized == self._craft_plan_sort_desc:
            return
        self._craft_plan_sort_desc = normalized
        self._sync_craft_plan_model()
        self.setupChanged.emit()

    @Slot()
    def toggleCraftPlanSortDescending(self) -> None:
        self.setCraftPlanSortDescending(not self._craft_plan_sort_desc)

    @Slot()
    def copyShoppingCsv(self) -> None:
        if not self._shopping_csv:
            self._set_list_action_text("Shopping CSV is empty.")
            return
        self._copy_to_clipboard(self._shopping_csv, success_message="Shopping CSV copied to clipboard.")

    @Slot(str)
    def copyText(self, raw_value: str) -> None:
        value = str(raw_value or "").strip()
        if not value:
            return
        self._copy_to_clipboard(value, success_message="Copied value to clipboard.")

    @Slot()
    def clearDiagnostics(self) -> None:
        self._diagnostics_lines = []
        self.diagnosticsChanged.emit()

    @Slot()
    def copySellingCsv(self) -> None:
        if not self._selling_csv:
            self._set_list_action_text("Selling CSV is empty.")
            return
        self._copy_to_clipboard(self._selling_csv, success_message="Selling CSV copied to clipboard.")

    @Slot()
    def copyResultsCsv(self) -> None:
        if not self._results_csv:
            self._set_list_action_text("Results CSV is empty.")
            return
        self._copy_to_clipboard(self._results_csv, success_message="Results CSV copied to clipboard.")

    @Slot(str)
    def exportShoppingCsv(self, raw_path: str) -> None:
        self._export_csv(raw_path=raw_path, payload=self._shopping_csv, label="Shopping")

    @Slot(str)
    def exportSellingCsv(self, raw_path: str) -> None:
        self._export_csv(raw_path=raw_path, payload=self._selling_csv, label="Selling")

    @Slot(str)
    def exportResultsCsv(self, raw_path: str) -> None:
        self._export_csv(raw_path=raw_path, payload=self._results_csv, label="Results")

    @Slot()
    def exportShoppingCsvInteractive(self) -> None:
        self._export_csv_interactive(payload=self._shopping_csv, label="Shopping", suggested_name="acd-shopping.csv")

    @Slot()
    def exportSellingCsvInteractive(self) -> None:
        self._export_csv_interactive(payload=self._selling_csv, label="Selling", suggested_name="acd-selling.csv")

    @Slot()
    def exportResultsCsvInteractive(self) -> None:
        self._export_csv_interactive(payload=self._results_csv, label="Results", suggested_name="acd-results.csv")

    def to_setup(self) -> CraftSetup:
        return sanitized_setup(self._setup)

    def close(self) -> None:
        if not price_refresh_ops.shutdown_async_price_fetch(self):
            return
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
        self._craft_plan_model.set_items(self._sorted_craft_plan_rows(self._craft_plan_rows))

    def _rebuild_craft_plan_recipe_index(self) -> None:
        self._craft_plan_recipe_ids = {str(row.recipe_id) for row in self._craft_plan_rows if str(row.recipe_id)}

    def _request_preview_rebuild(self, *, force_price_refresh: bool) -> None:
        if self._should_defer_preview_rebuild():
            self._deferred_force_preview_rebuild = bool(
                self._deferred_force_preview_rebuild or force_price_refresh
            )
            self._deferred_preview_rebuild_timer.start(250)
            return
        self._rebuild_preview(force_price_refresh=force_price_refresh)

    def _should_defer_preview_rebuild(self) -> bool:
        if len(self._craft_plan_rows) < 8:
            return False
        if QCoreApplication.instance() is None:
            return False
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return False
        return True

    def _family_recipe_ids(self, recipe_id: str) -> list[str]:
        return selection_ops.family_recipe_ids(
            self._catalog,
            recipe_id,
            recipe_tier_filters=self._recipe_tier_filters,
            recipe_enchant_filters=self._recipe_enchant_filters,
            is_recipe_plan_candidate=_is_recipe_plan_candidate,
            item_family_key=_item_family_key,
            recipe_display_label=_recipe_display_label,
            recipe_identity=_recipe_identity,
        )

    def _family_recipe_ids_for_filtered(self, recipe_ids: list[str]) -> list[str]:
        return selection_ops.family_recipe_ids_for_filtered(
            self._catalog,
            recipe_ids,
            family_recipe_ids_for_recipe=self._family_recipe_ids,
            item_family_key=_item_family_key,
            recipe_identity=_recipe_identity,
        )

    def _station_recipe_ids(self, recipe_id: str) -> list[str]:
        return selection_ops.station_recipe_ids(
            self._catalog,
            recipe_id,
            recipe_tier_filters=self._recipe_tier_filters,
            recipe_enchant_filters=self._recipe_enchant_filters,
            is_recipe_plan_candidate=_is_recipe_plan_candidate,
            recipe_display_label=_recipe_display_label,
            recipe_identity=_recipe_identity,
        )

    def _station_recipe_ids_for_filtered(self, recipe_ids: list[str]) -> list[str]:
        return selection_ops.station_recipe_ids_for_filtered(
            self._catalog,
            recipe_ids,
            station_recipe_ids_for_recipe=self._station_recipe_ids,
            recipe_identity=_recipe_identity,
        )

    def _sorted_craft_plan_rows(self, rows: list[CraftPlanRow]) -> list[CraftPlanRow]:
        return selection_ops.sorted_craft_plan_rows(
            rows,
            sort_key=self._craft_plan_sort_key,
            reverse=bool(self._craft_plan_sort_desc),
        )

    def _add_recipe_to_plan_internal(
        self,
        recipe_id: str,
        *,
        runs: int,
        enabled: bool,
        sync_model: bool = True,
    ) -> bool:
        recipe = self._catalog.get(recipe_id)
        if recipe is None:
            return False
        if not _is_recipe_plan_candidate(recipe):
            return False
        resolved_recipe_id = _recipe_identity(recipe)
        if resolved_recipe_id in self._craft_plan_recipe_ids:
            return False
        self._ensure_price_preferences_for_recipe(recipe)
        row = CraftPlanRow(
            row_id=self._next_plan_row_id,
            recipe_id=resolved_recipe_id,
            display_name=_recipe_display_label(recipe),
            tier=int(recipe.item.tier or 0),
            enchant=int(recipe.item.enchantment or 0),
            variant_label=str(recipe.variant_label or ""),
            uses_crystallized=bool(recipe.uses_crystallized),
            craft_city=self._setup.craft_city or "Bridgewatch",
            daily_bonus_percent=float(self._normalize_daily_bonus_percent(self._setup.daily_bonus_percent)),
            return_rate_percent=None,
            runs=max(1, int(runs)),
            enabled=bool(enabled),
            profit_percent=None,
            has_fresh_component_prices=True,
        )
        self._next_plan_row_id += 1
        self._craft_plan_rows.append(row)
        self._craft_plan_recipe_ids.add(resolved_recipe_id)
        if sync_model:
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
        changed_city = False
        changed_profit_drivers = False
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
                variant_label=row.variant_label,
                uses_crystallized=bool(row.uses_crystallized),
                craft_city=next_craft_city,
                daily_bonus_percent=next_daily_bonus,
                return_rate_percent=row.return_rate_percent,
                runs=next_runs,
                enabled=next_enabled,
                profit_percent=row.profit_percent,
                has_fresh_component_prices=row.has_fresh_component_prices,
            )
            changed = next_row != row
            changed_city = changed_city or (next_row.craft_city != row.craft_city)
            changed_profit_drivers = changed_profit_drivers or (
                next_row.enabled != row.enabled
                or next_row.runs != row.runs
                or float(next_row.daily_bonus_percent) != float(row.daily_bonus_percent)
            )
            next_rows.append(next_row)
        if changed:
            self._craft_plan_rows = next_rows
            sort_key = str(self._craft_plan_sort_key or "")
            needs_resort = (sort_key == "city" and changed_city) or (sort_key == "pl" and changed_profit_drivers)
            if needs_resort:
                self._sync_craft_plan_model()
            else:
                self._craft_plan_model.set_items_in_place(self._sorted_craft_plan_rows(self._craft_plan_rows))
        return changed

    def _ensure_price_preferences_for_recipe(self, recipe: Recipe) -> None:
        for component in recipe.components:
            self._input_price_types.setdefault(component.item.unique_name, PriceType.SELL_ORDER)
        for output in recipe.outputs:
            self._output_price_types.setdefault(output.item.unique_name, PriceType.SELL_ORDER)

    def _recipes_for_preview(self) -> list[tuple[CraftPlanRow, Recipe]]:
        return preview_state_ops.recipes_for_preview(self)

    @staticmethod
    def _setup_for_plan_row(setup: CraftSetup, row: CraftPlanRow) -> CraftSetup:
        return preview_state_ops.setup_for_plan_row(setup, row)

    def _recipes_for_pricing(self) -> list[Recipe]:
        return preview_state_ops.recipes_for_pricing(
            self,
            recipe_identity=_recipe_identity,
        )

    def _collect_pricing_item_ids(self) -> list[str]:
        return preview_state_ops.collect_pricing_item_ids(
            self,
            recipes_for_pricing=self._recipes_for_pricing,
            item_id_query_candidates=_item_id_query_candidates,
            journal_rule_for_item=_journal_rule_for_item,
        )

    def _collect_locations(self, setup: CraftSetup) -> list[str]:
        return preview_state_ops.collect_locations(
            self,
            setup,
            is_market_location=self._is_market_location,
        )

    def _clear_preview_state(self, note: str) -> None:
        preview_state_ops.clear_preview_state(self, note)

    def _rebuild_preview(self, *, force_price_refresh: bool) -> None:
        setup = self.to_setup()
        planned_recipes = self._recipes_for_preview()
        if not planned_recipes:
            self._clear_preview_state("no enabled recipes in craft plan")
            return
        allow_live_fetch = force_price_refresh or (
            self._active_market_tab_index >= 1 and not self._market_data_tabs_live_bootstrap_done
        )
        if allow_live_fetch and not force_price_refresh:
            # One automatic live fetch when first entering data tabs; next refreshes are manual.
            self._market_data_tabs_live_bootstrap_done = True
        price_index = self._current_price_index(
            setup,
            force_refresh=force_price_refresh,
            allow_live=allow_live_fetch,
        )
        runs, prepared_recipes, skipped_rows = preview_flow_ops.prepare_preview_runs(
            self,
            setup=setup,
            planned_recipes=planned_recipes,
            price_index=price_index,
            recipe_identity=_recipe_identity,
        )

        if not runs:
            self._clear_preview_state("preview build failed")
            return

        run_profit_by_row, run_rrr_by_row, run_fresh_by_row = preview_flow_ops.compute_run_maps(
            self,
            setup=setup,
            prepared_recipes=prepared_recipes,
            runs=runs,
        )
        self._set_plan_profit_map(run_profit_by_row, run_rrr_by_row, run_fresh_by_row)

        visible_runs, visible_prepared_recipes = preview_flow_ops.filter_visible_runs(
            self,
            prepared_recipes=prepared_recipes,
            runs=runs,
            run_fresh_by_row=run_fresh_by_row,
        )

        selected_visible_runs, selected_visible_prepared_recipes = preview_flow_ops.split_selected_visible_runs(
            visible_prepared_recipes=visible_prepared_recipes,
            visible_runs=visible_runs,
        )
        selected_journal_totals = self._estimate_journal_totals(
            runs=selected_visible_runs,
            setup=setup,
            price_index=price_index,
        )
        self._results_journal_totals = selected_journal_totals
        selected_inputs = [line for run in selected_visible_runs for line in run.inputs]
        self._selected_input_item_ids = preview_flow_ops.selected_input_item_ids(
            selected_visible_runs=selected_visible_runs,
            selected_journal_totals=selected_journal_totals,
        )
        selected_material_input_total = self._compute_input_total_from_lines(
            input_lines=selected_inputs,
            prepared_recipes=selected_visible_prepared_recipes,
        )
        selected_input_total = float(selected_material_input_total + float(selected_journal_totals.input_cost))

        all_inputs = [line for run in visible_runs for line in run.inputs]
        all_outputs = [line for run in visible_runs for line in run.outputs]
        self._journal_totals = self._estimate_journal_totals(runs=visible_runs, setup=setup, price_index=price_index)
        input_acc = self._accumulate_input_preview_rows(
            prepared_recipes=visible_prepared_recipes,
            runs=visible_runs,
        )

        journal_buy_city = (setup.default_buy_city or setup.craft_city or "").strip()
        journal_sell_city = (setup.default_sell_city or setup.craft_city or "").strip()
        preview_render_ops.merge_journal_input_rows(
            input_acc=input_acc,
            journal_totals=self._journal_totals,
            buy_city=journal_buy_city,
            quality=self._setup.quality,
            price_age_text_for_item_ids=self._price_age_text_for_item_ids,
            journal_display_name=_journal_display_name,
            input_price_types=self._input_price_types,
            to_price_type=self._to_price_type,
            include_item_ref=True,
        )

        input_rows, adjusted_inputs = preview_render_ops.build_input_rows(
            input_acc=input_acc,
            input_stock_quantities=self._input_stock_quantities,
            manual_input_prices=self._manual_input_prices,
            completed_input_item_ids=self._completed_input_item_ids,
            need_quantity_with_safety_buffer=_need_quantity_with_safety_buffer,
            input_preview_row_key=_input_preview_row_key,
            sort_key=_input_preview_sort_key,
        )

        selected_input_acc = self._accumulate_input_preview_rows(
            prepared_recipes=selected_visible_prepared_recipes,
            runs=selected_visible_runs,
        )

        preview_render_ops.merge_journal_input_rows(
            input_acc=selected_input_acc,
            journal_totals=selected_journal_totals,
            buy_city=journal_buy_city,
            quality=self._setup.quality,
            price_age_text_for_item_ids=self._price_age_text_for_item_ids,
            journal_display_name=_journal_display_name,
            input_price_types=None,
            to_price_type=self._to_price_type,
            include_item_ref=False,
        )

        selected_input_rows, _ = preview_render_ops.build_input_rows(
            input_acc=selected_input_acc,
            input_stock_quantities=self._input_stock_quantities,
            manual_input_prices=self._manual_input_prices,
            completed_input_item_ids=self._completed_input_item_ids,
            need_quantity_with_safety_buffer=_need_quantity_with_safety_buffer,
            input_preview_row_key=_input_preview_row_key,
            sort_key=_input_preview_sort_key,
        )

        self._base_input_total_cost = float(sum(row.total_cost for row in input_rows))
        valuations = compute_output_valuations(
            output_lines=all_outputs,
            station_fee_percent=setup.station_fee_percent,
            market_tax_percent=setup.market_tax_percent,
        )

        output_acc = preview_render_ops.accumulate_output_rows(
            valuations=valuations,
            quality=self._setup.quality,
            price_age_text=self._price_age_text,
            item_label=_friendly_item_label,
        )

        preview_render_ops.merge_journal_output_rows(
            output_acc=output_acc,
            journal_totals=self._journal_totals,
            sell_city=journal_sell_city,
            quality=self._setup.quality,
            price_age_text_for_item_ids=self._price_age_text_for_item_ids,
            journal_display_name=_journal_display_name,
            output_price_types=self._output_price_types,
            output_cities=self._output_cities,
            to_price_type=self._to_price_type,
        )

        output_rows = preview_render_ops.build_output_rows(
            output_acc=output_acc,
            manual_output_prices=self._manual_output_prices,
            completed_output_item_ids=self._completed_output_item_ids,
        )

        self._inputs_model.set_items(input_rows)
        self._inputs_on_model.set_items(selected_input_rows)
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
            for entry in build_shopping_entries(adjusted_inputs)
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

        selected_outputs = [line for run in selected_visible_runs for line in run.outputs]
        selected_valuations = compute_output_valuations(
            output_lines=selected_outputs,
            station_fee_percent=setup.station_fee_percent,
            market_tax_percent=setup.market_tax_percent,
        )
        selected_output_acc = preview_render_ops.accumulate_output_rows(
            valuations=selected_valuations,
            quality=self._setup.quality,
            price_age_text=self._price_age_text,
            item_label=_friendly_item_label,
        )

        preview_render_ops.merge_journal_output_rows(
            output_acc=selected_output_acc,
            journal_totals=selected_journal_totals,
            sell_city=journal_sell_city,
            quality=self._setup.quality,
            price_age_text_for_item_ids=self._price_age_text_for_item_ids,
            journal_display_name=_journal_display_name,
            output_price_types=None,
            output_cities=None,
            to_price_type=self._to_price_type,
        )

        selected_output_rows = preview_render_ops.build_output_rows(
            output_acc=selected_output_acc,
            manual_output_prices=self._manual_output_prices,
            completed_output_item_ids=self._completed_output_item_ids,
        )
        self._selected_output_item_ids = sorted({str(row.item_id) for row in selected_output_rows})

        selected_output_total_value = float(sum(row.total_value for row in selected_output_rows))
        selected_output_net_value = float(sum(row.net_value for row in selected_output_rows))
        selected_station_fee = float(sum(row.fee_value for row in selected_output_rows))
        selected_market_tax = float(sum(row.tax_value for row in selected_output_rows))
        selected_run_breakdown = compute_batch_profit(tuple(selected_visible_runs))
        self._breakdown = ProfitBreakdown(
            input_cost=float(selected_input_total),
            output_value=selected_output_total_value,
            station_fee=selected_station_fee,
            market_tax=selected_market_tax,
            focus_used=float(selected_run_breakdown.focus_used),
            notes=list(selected_run_breakdown.notes),
        )
        self._selected_input_total_cost = float(selected_input_total)
        self._selected_material_input_total_cost = float(selected_material_input_total)
        self._selected_output_total_value = selected_output_total_value
        self._selected_output_net_value = selected_output_net_value
        self._selected_net_profit_value = float(self._breakdown.net_profit)
        self._selected_margin_percent = float(self._breakdown.margin_percent)

        results_rows = self._build_results_rows_from_runs(
            runs=selected_visible_runs,
            input_total=selected_input_total,
        )
        self._results_items_model.set_items(results_rows)
        self._results_csv = self._rows_to_csv(
            header=["item_id", "item_name", "city", "quantity", "revenue", "cost", "fee", "tax", "profit", "margin_percent", "demand_proxy"],
            rows=[
                [
                    row.item_id,
                    row.item,
                    row.city,
                    f"{row.quantity:.4f}",
                    f"{row.revenue:.2f}",
                    f"{row.allocated_cost:.2f}",
                    f"{row.fee_value:.2f}",
                    f"{row.tax_value:.2f}",
                    f"{row.profit:.2f}",
                    f"{row.margin_percent:.2f}",
                    f"{row.demand_proxy:.2f}",
                ]
                for row in results_rows
            ],
        )
        self._outputs_on_model.set_items(selected_output_rows)
        breakdown_rows = self._build_breakdown_rows()
        self._breakdown_model.set_items(breakdown_rows)

        self.inputsChanged.emit()
        self.outputsChanged.emit()
        self.resultsChanged.emit()
        self.listsChanged.emit()
        self.resultsDetailsChanged.emit()
        if skipped_rows:
            self._set_fallback_status(
                f"Skipped {len(skipped_rows)} recipe(s) that could not be previewed."
            )

    def _build_results_rows_from_runs(
        self,
        *,
        runs: list[CraftRun],
        input_total: float,
    ) -> list[ResultItemRow]:
        return preview_metric_ops.build_results_rows(
            self,
            runs=runs,
            input_total=input_total,
            item_label=_friendly_item_label,
            result_row_profit_and_margin=lambda allocated_cost, net_value: _result_row_profit_and_margin(
                allocated_cost=allocated_cost,
                net_value=net_value,
            ),
        )

    def _accumulate_input_preview_rows(
        self,
        *,
        prepared_recipes: list[tuple[CraftPlanRow, Recipe]],
        runs: list[CraftRun],
    ) -> dict[tuple[str, str, str, float], dict[str, object]]:
        return preview_metric_ops.accumulate_inputs(
            self,
            prepared_recipes=prepared_recipes,
            runs=runs,
            item_label=_friendly_item_label,
            minimal_upfront_quantity_for_batches=_minimal_upfront_quantity_for_batches,
            upfront_return_safety_units=_upfront_return_safety_units,
        )

    def _build_breakdown_rows(self) -> list[BreakdownRow]:
        return preview_metric_ops.build_breakdown(self)

    def _compute_input_total_from_lines(
        self,
        *,
        input_lines: list[InputLine] | tuple[InputLine, ...],
        prepared_recipes: list[tuple[CraftPlanRow, Recipe]],
    ) -> float:
        return preview_metric_ops.compute_input_total(
            self,
            input_lines=input_lines,
            prepared_recipes=prepared_recipes,
        )

    def _demand_proxy_percent(self, *, item_id: str, city: str, quality: int) -> float:
        return quote_ops.demand_proxy_percent(
            self._price_index,
            item_id=item_id,
            city=city,
            quality=quality,
            find_price_quote=_find_price_quote,
        )

    def _set_plan_profit_map(
        self,
        values: dict[int, float | None],
        return_rates: dict[int, float] | None = None,
        fresh_component_prices: dict[int, bool] | None = None,
    ) -> None:
        quote_ops.set_plan_profit_map(
            self,
            values,
            return_rates=return_rates,
            fresh_component_prices=fresh_component_prices,
        )

    def _price_age_text(self, *, item_id: str, city: str, quality: int, price_type: str) -> str:
        return quote_ops.price_age_text(
            self._price_index,
            item_id=item_id,
            city=city,
            quality=quality,
            price_type=price_type,
            find_price_quote=_find_price_quote,
            parse_iso_datetime=_parse_iso_datetime,
            format_age=_format_age,
        )

    def _run_has_fresh_component_prices(self, run: CraftRun) -> bool:
        return quote_ops.run_has_fresh_component_prices(self, run)

    def _has_fresh_price(self, *, item_id: str, city: str, quality: int, price_type: str) -> bool:
        return quote_ops.has_fresh_price(
            self._price_index,
            item_id=item_id,
            city=city,
            quality=quality,
            price_type=price_type,
            find_price_quote=_find_price_quote,
            parse_iso_datetime=_parse_iso_datetime,
        )

    def _estimate_journal_totals(
        self,
        *,
        runs: list[Any],
        setup: CraftSetup,
        price_index: dict[tuple[str, str, int], MarketPriceRecord],
    ) -> _JournalTotals:
        return journal_ops.estimate_journal_totals(
            runs=runs,
            setup=setup,
            price_index=price_index,
            resolve_market_price_for_item_ids=lambda price_index_value, item_ids, city, quality, preferred_mode: self._resolve_market_price_for_item_ids(
                price_index=price_index_value,
                item_ids=item_ids,
                city=city,
                quality=quality,
                preferred_mode=preferred_mode,
            ),
            journal_rule_for_item=_journal_rule_for_item,
            journal_fame_factor_for_item=_journal_fame_factor_for_item,
            tier_from_item_id=_tier_from_item_id,
        )

    def _resolve_market_price_for_item_ids(
        self,
        *,
        price_index: dict[tuple[str, str, int], MarketPriceRecord],
        item_ids: list[str],
        city: str,
        quality: int,
        preferred_mode: str,
    ) -> tuple[float, str, str]:
        return quote_ops.resolve_market_price_for_item_ids(
            price_index,
            item_ids=item_ids,
            city=city,
            quality=quality,
            preferred_mode=preferred_mode,
            find_price_quote=_find_price_quote,
        )

    def _price_age_text_for_item_ids(
        self,
        *,
        item_ids: Sequence[str],
        city: str,
        quality: int,
        price_type: str,
    ) -> str:
        return quote_ops.price_age_text_for_item_ids(
            self,
            item_ids=item_ids,
            city=city,
            quality=quality,
            price_type=price_type,
        )

    def _set_list_action_text(self, text: str) -> None:
        self._list_action_text = text
        self.listsChanged.emit()

    def _build_aodata_url(self) -> str | None:
        return ui_ops.build_aodata_url(self)

    def _copy_to_clipboard(self, value: str, *, success_message: str) -> None:
        ui_ops.copy_to_clipboard(self, value, success_message=success_message)

    def _export_csv_interactive(self, *, payload: str, label: str, suggested_name: str) -> None:
        ui_ops.export_csv_interactive(
            self,
            payload=payload,
            label=label,
            suggested_name=suggested_name,
        )

    def _prompt_export_path(self, *, label: str, suggested_name: str) -> str | None:
        return ui_ops.prompt_export_path(
            self,
            label=label,
            suggested_name=suggested_name,
        )

    def _export_csv(self, *, raw_path: str, payload: str, label: str) -> None:
        ui_ops.export_csv(
            self,
            raw_path=raw_path,
            payload=payload,
            label=label,
        )

    @staticmethod
    def _rows_to_csv(*, header: list[str], rows: list[list[str]]) -> str:
        return ui_ops.rows_to_csv(header=header, rows=rows)

    def _current_price_index(
        self,
        setup: CraftSetup,
        *,
        force_refresh: bool,
        allow_live: bool,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        return price_refresh_ops.current_price_index(
            self,
            setup,
            force_refresh=force_refresh,
            allow_live=allow_live,
        )

    def _refresh_price_index(
        self,
        setup: CraftSetup,
        *,
        force: bool,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        return price_refresh_ops.refresh_price_index(
            self,
            setup,
            force=force,
        )

    def _process_ui_events(self) -> None:
        price_refresh_ops.process_ui_events()

    def _should_defer_price_refresh(self) -> bool:
        return price_refresh_ops.should_defer_price_refresh(self)

    def _set_prices_status(self, source: str, message: str) -> None:
        price_refresh_ops.set_prices_status(self, source, message)

    def _set_fallback_status(self, message: str) -> None:
        price_refresh_ops.set_fallback_status(self, message)

    def _append_diag(self, message: str, *, level: str = "INFO") -> None:
        price_refresh_ops.append_diag(self, message, level=level)

    def _schedule_deferred_price_refresh(self, delay_seconds: float, *, force: bool = False) -> None:
        price_refresh_ops.schedule_deferred_price_refresh(self, delay_seconds, force=force)

    @Slot()
    def _on_deferred_price_refresh_timeout(self) -> None:
        price_refresh_ops.on_deferred_price_refresh_timeout(self)

    @Slot()
    def _on_deferred_preview_rebuild_timeout(self) -> None:
        force_refresh = bool(self._deferred_force_preview_rebuild)
        self._deferred_force_preview_rebuild = False
        self._rebuild_preview(force_price_refresh=force_refresh)

    @Slot(object, object, str)
    def _on_async_price_fetch_finished(self, index: object, meta: object, error: str) -> None:
        price_refresh_ops.on_async_price_fetch_finished(self, index, meta, error)

    @Slot()
    def _on_async_price_fetch_poll(self) -> None:
        price_refresh_ops.poll_async_price_fetch(self)

    def _set_next_live_fetch_cooldown(self, seconds: float) -> None:
        price_refresh_ops.set_next_live_fetch_cooldown(self, seconds)

    @Slot()
    def _on_refresh_cooldown_tick(self) -> None:
        price_refresh_ops.on_refresh_cooldown_tick(self)

    def _load_presets(self) -> dict[str, dict[str, object]]:
        path = self._preset_path
        try:
            return preset_ops.load_presets(path)
        except Exception as exc:
            self._log.warning("Market preset load failed: %s", exc)
            return {}

    def _save_presets(self) -> bool:
        path = self._preset_path
        try:
            preset_ops.save_presets(path, self._presets)
        except Exception as exc:
            self._log.warning("Market preset save failed: %s", exc)
            self._set_list_action_text(f"Preset save failed: {exc}")
            return False
        return True

    def _price_key(self, setup: CraftSetup) -> tuple[str, tuple[int, ...], tuple[str, ...], tuple[str, ...]]:
        return pricing_ops.price_key(
            setup,
            item_ids=tuple(self._collect_pricing_item_ids()),
            locations=tuple(self._collect_locations(setup)),
        )

    @staticmethod
    def _price_qualities(setup: CraftSetup) -> tuple[int, ...]:
        return pricing_ops.price_qualities(setup)

    @staticmethod
    def _default_market_tax_percent(premium: bool) -> float:
        return pricing_ops.default_market_tax_percent(premium)

    @staticmethod
    def _normalize_daily_bonus_percent(value: float) -> float:
        raw = int(round(float(value)))
        if raw >= 15:
            return 20.0
        if raw >= 5:
            return 10.0
        return 0.0

    @staticmethod
    def _normalize_int_filter_list(
        values: Sequence[object] | None,
        *,
        minimum: int,
        maximum: int,
    ) -> list[int]:
        return _normalize_int_values(values, minimum=minimum, maximum=maximum)

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
        return pricing_ops.is_market_location(location)

    def _load_catalog(self) -> RecipeCatalog:
        return catalog_ops.load_catalog(self._log)

    def _build_recipe_options(self) -> list[RecipeOptionRow]:
        return selection_ops.build_recipe_options(
            self._catalog,
            is_recipe_plan_candidate=_is_recipe_plan_candidate,
            recipe_identity=_recipe_identity,
            recipe_display_label=_recipe_display_label,
        )

    def _resolve_recipe(self, recipe_id: str) -> Recipe:
        recipe = catalog_ops.resolve_recipe(self._catalog, recipe_id)
        if recipe is not None:
            return recipe
        self._log.warning("Market catalog empty, using builtin fallback recipe.")
        return self._build_builtin_recipe()

    @staticmethod
    def _build_builtin_recipe() -> Recipe:
        return catalog_ops.build_builtin_recipe()

    def _build_fallback_price_index(
        self,
        setup: CraftSetup,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        locations = set(self._collect_locations(setup))
        locations.add("Bridgewatch")
        return pricing_ops.build_fallback_price_index(
            setup=setup,
            locations=locations,
            prices=self._estimate_fallback_prices(),
        )

    def _estimate_fallback_prices(self) -> dict[str, tuple[int, int]]:
        return pricing_ops.estimate_fallback_prices(
            recipes=self._recipes_for_pricing(),
        )

    @staticmethod
    def _price_by_tier(tier: int | None) -> tuple[int, int]:
        return pricing_ops.price_by_tier(tier)


def _parse_price(raw_value: str) -> int:
    text = raw_value.strip().replace(",", ".")
    if not text:
        return 0
    try:
        parsed = int(float(text))
    except ValueError:
        return 0
    return max(0, parsed)


def _parse_float(raw_value: str) -> float:
    text = str(raw_value or "").strip().replace(",", ".")
    if not text:
        return 0.0
    try:
        parsed = float(text)
    except ValueError:
        return 0.0
    return max(0.0, parsed)


def _parse_bool(raw_value: object, *, default: bool) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    if raw_value is None:
        return default
    if isinstance(raw_value, (int, float)):
        return bool(raw_value)
    normalized = str(raw_value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _default_preset_path() -> Path:
    return preset_ops.default_preset_path()


def _sanitize_preset_name(raw_value: str) -> str:
    return preset_ops.sanitize_preset_name(raw_value)


def _setup_to_dict(setup: CraftSetup) -> dict[str, object]:
    return preset_ops.setup_to_dict(setup)


def _setup_from_dict(payload: dict[str, object], *, fallback: CraftSetup) -> CraftSetup:
    return preset_ops.setup_from_dict(payload, fallback=fallback)


def _craft_plan_row_to_dict(row: CraftPlanRow) -> dict[str, object]:
    return preset_ops.craft_plan_row_to_dict(row)


def _craft_plan_rows_from_payload(
    payload: object,
    *,
    catalog: RecipeCatalog,
    fallback_city: str,
    fallback_daily_bonus_percent: float,
) -> list[CraftPlanRow] | None:
    return preset_ops.craft_plan_rows_from_payload(
        payload,
        catalog=catalog,
        fallback_city=fallback_city,
        fallback_daily_bonus_percent=fallback_daily_bonus_percent,
        normalize_daily_bonus_percent=MarketSetupState._normalize_daily_bonus_percent,
        parse_price=_parse_price,
        parse_float=_parse_float,
        parse_bool=lambda raw_value, default: _parse_bool(raw_value, default=default),
        recipe_display_label=_recipe_display_label,
        recipe_identity=_recipe_identity,
    )


def _base_item_id(item_id: str) -> str:
    return common_ops.base_item_id(item_id)


def _tier_from_item_id(item_id: str) -> int:
    return common_ops.tier_from_item_id(item_id)


def _input_group_rank(item_id: str) -> int:
    return common_ops.input_group_rank(item_id)


def _input_preview_sort_key(row: InputPreviewRow) -> tuple[int, int, str, str, str]:
    return common_ops.input_preview_sort_key(
        row,
        item_family_key=_item_family_key,
    )


def _journal_maps() -> tuple[dict[str, _JournalRule], dict[str, float]]:
    return journal_ops.journal_maps()


def _journal_rule_templates() -> dict[tuple[int, str], _JournalRule]:
    return journal_ops.journal_rule_templates()


def _item_metadata_map() -> dict[str, dict[str, str]]:
    return journal_ops.item_metadata_map()


def _infer_journal_kind_for_item(item_id: str) -> str | None:
    return journal_ops.infer_journal_kind_for_item(item_id)


def _journal_rule_fallback_for_item(item_id: str) -> _JournalRule | None:
    tier = _tier_from_item_id(item_id)
    kind = _infer_journal_kind_for_item(item_id)
    if tier <= 0 or not kind:
        return None
    return _journal_rule_templates().get((tier, kind.upper()))


def _journal_rule_for_item(item_id: str) -> _JournalRule | None:
    journal_by_item, _ = _journal_maps()
    rule = journal_by_item.get(_base_item_id(item_id))
    if rule is not None:
        return rule
    return _journal_rule_fallback_for_item(item_id)


def _journal_fame_factor_for_item(item_id: str) -> float:
    _, fame_factor_by_item = _journal_maps()
    return float(fame_factor_by_item.get(_base_item_id(item_id), 1.0))


def _journal_display_name(kind: str, tier: int) -> str:
    return journal_ops.journal_display_name(kind, tier)


def _friendly_item_label(display_name: str, item_id: str) -> str:
    return recipe_ops.friendly_item_label(display_name, item_id)


def _recipe_identity(recipe: Recipe) -> str:
    return recipe_ops.recipe_identity(recipe)


def _recipe_output_item(recipe: Recipe) -> ItemRef:
    return recipe_ops.recipe_output_item(recipe)


def _recipe_display_label(recipe: Recipe) -> str:
    return recipe_ops.recipe_display_label(recipe)


def _item_family_key(item_id: str) -> str:
    return recipe_ops.item_family_key(item_id)


def _is_recipe_plan_candidate(recipe: Recipe) -> bool:
    return recipe_ops.is_recipe_plan_candidate(recipe)


def _humanize_item_id(item_id: str) -> str:
    return recipe_ops.humanize_item_id(item_id)


def _item_id_candidates(item_id: str) -> tuple[str, ...]:
    return recipe_ops.item_id_candidates(item_id)


def _item_id_query_candidates(item_id: str) -> tuple[str, ...]:
    return recipe_ops.item_id_query_candidates(item_id)


def _mode_has_price(quote: MarketPriceRecord, preferred_mode: str | None) -> bool:
    return common_ops.mode_has_price(quote, preferred_mode)


def _find_price_quote(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
    preferred_mode: str | None,
) -> MarketPriceRecord | None:
    return common_ops.find_price_quote(
        price_index,
        item_id=item_id,
        city=city,
        quality=quality,
        preferred_mode=preferred_mode,
        item_id_candidates=_item_id_candidates,
    )


def _parse_iso_datetime(raw_value: str) -> datetime | None:
    return common_ops.parse_iso_datetime(raw_value)


def _result_row_profit_and_margin(*, allocated_cost: float, net_value: float) -> tuple[float, float]:
    return common_ops.result_row_profit_and_margin(
        allocated_cost=allocated_cost,
        net_value=net_value,
    )


def _format_age(updated_at: datetime) -> str:
    return common_ops.format_age(updated_at)


def _need_quantity_with_safety_buffer(quantity_raw: float, is_returnable: bool) -> int:
    return common_ops.need_quantity_with_safety_buffer(quantity_raw, is_returnable)


def _minimal_upfront_quantity_for_batches(batches: Sequence[tuple[float, float]]) -> float:
    return common_ops.minimal_upfront_quantity_for_batches(batches)


def _upfront_return_safety_units(batches: Sequence[tuple[float, float]]) -> int:
    return common_ops.upfront_return_safety_units(batches)


def _input_preview_row_key(item_id: str, city: str, price_type: str) -> str:
    return common_ops.input_preview_row_key(item_id, city, price_type)


def _normalize_int_values(
    values: Sequence[object] | None,
    *,
    minimum: int,
    maximum: int,
) -> list[int]:
    return common_ops.normalize_int_values(
        values,
        minimum=minimum,
        maximum=maximum,
    )
