from __future__ import annotations

from albion_dps.market.engine import ProfitBreakdown
from albion_dps.market.models import CraftSetup
from albion_dps.qt.market.state_types import _JournalTotals


def recipes_for_preview(state) -> list[tuple[object, object]]:
    rows: list[tuple[object, object]] = []
    for row in state._craft_plan_rows:
        recipe = state._catalog.get(row.recipe_id)
        if recipe is None:
            continue
        rows.append((row, recipe))
    return rows


def setup_for_plan_row(setup: CraftSetup, row) -> CraftSetup:
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


def recipes_for_pricing(state, *, recipe_identity) -> list[object]:
    recipes: list[object] = []
    seen: set[str] = set()
    for row in state._craft_plan_rows:
        recipe = state._catalog.get(row.recipe_id)
        if recipe is None:
            continue
        recipe_key = recipe_identity(recipe)
        if recipe_key in seen:
            continue
        seen.add(recipe_key)
        recipes.append(recipe)
    return recipes


def collect_pricing_item_ids(
    state,
    *,
    recipes_for_pricing,
    item_id_query_candidates,
    journal_rule_for_item,
) -> list[str]:
    _ = item_id_query_candidates
    item_ids: set[str] = set()
    for recipe in recipes_for_pricing():
        for component in recipe.components:
            item_ids.add(str(component.item.unique_name))
        for output in recipe.outputs:
            item_ids.add(str(output.item.unique_name))
        journal_rule = journal_rule_for_item(recipe.item.unique_name)
        if journal_rule is not None:
            item_ids.add(journal_rule.empty_item_id)
            item_ids.add(f"{journal_rule.empty_item_id}_EMPTY")
            item_ids.add(journal_rule.full_item_id)
    return sorted(item_ids)


def collect_locations(state, setup: CraftSetup, *, is_market_location) -> list[str]:
    location_set = {
        setup.craft_city.strip(),
        setup.default_buy_city.strip(),
        setup.default_sell_city.strip(),
    }
    for row in state._craft_plan_rows:
        city_value = row.craft_city.strip()
        if city_value:
            location_set.add(city_value)
    locations = sorted(location for location in (location_set - {""}) if is_market_location(location))
    if not locations:
        locations = ["Bridgewatch"]
    return locations


def clear_preview_state(state, note: str) -> None:
    state._inputs_model.set_items([])
    state._inputs_on_model.set_items([])
    state._outputs_model.set_items([])
    state._outputs_on_model.set_items([])
    state._shopping_model.set_items([])
    state._selling_model.set_items([])
    state._results_items_model.set_items([])
    state._breakdown_model.set_items([])
    state._set_plan_profit_map({}, fresh_component_prices={})
    state._shopping_csv = ""
    state._selling_csv = ""
    state._results_csv = ""
    state._breakdown = ProfitBreakdown(notes=[note] if note else [])
    state._base_input_total_cost = 0.0
    state._journal_totals = _JournalTotals()
    state._results_journal_totals = _JournalTotals()
    state._selected_material_input_total_cost = 0.0
    state._selected_input_total_cost = 0.0
    state._selected_output_total_value = 0.0
    state._selected_output_net_value = 0.0
    state._selected_net_profit_value = 0.0
    state._selected_margin_percent = 0.0
    state._selected_input_item_ids = []
    state._selected_output_item_ids = []
    state.inputsChanged.emit()
    state.outputsChanged.emit()
    state.resultsChanged.emit()
    state.listsChanged.emit()
    state.resultsDetailsChanged.emit()
