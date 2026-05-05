from __future__ import annotations

from albion_dps.market.engine import build_craft_run, compute_run_profit, effective_return_fraction
from albion_dps.market.models import CraftRun, CraftSetup, Recipe
from albion_dps.qt.market.list_models import CraftPlanRow


def prepare_preview_runs(
    state,
    *,
    setup: CraftSetup,
    planned_recipes: list[tuple[CraftPlanRow, Recipe]],
    price_index,
    recipe_identity,
) -> tuple[list[CraftRun], list[tuple[CraftPlanRow, Recipe]], list[str]]:
    runs: list[CraftRun] = []
    prepared_recipes: list[tuple[CraftPlanRow, Recipe]] = []
    skipped_rows: list[str] = []
    for row, recipe in planned_recipes:
        state._ensure_price_preferences_for_recipe(recipe)
        row_setup = state._setup_for_plan_row(setup, row)
        try:
            run = build_craft_run(
                recipe=recipe,
                quantity=max(1, int(row.runs)),
                setup=row_setup,
                price_index=price_index,
                input_price_types=dict(state._input_price_types),
                output_cities=dict(state._output_cities),
                output_price_types=dict(state._output_price_types),
                manual_input_prices=dict(state._manual_input_prices),
                manual_output_prices=dict(state._manual_output_prices),
            )
        except Exception as exc:
            recipe_id = recipe_identity(recipe)
            skipped_rows.append(recipe_id)
            state._append_diag(
                f"Preview build skipped recipe {recipe_id}: {exc}",
                level="WARN",
            )
            continue
        runs.append(run)
        prepared_recipes.append((row, recipe))
    return runs, prepared_recipes, skipped_rows


def compute_run_maps(
    state,
    *,
    setup: CraftSetup,
    prepared_recipes: list[tuple[CraftPlanRow, Recipe]],
    runs: list[CraftRun],
) -> tuple[dict[int, float], dict[int, float], dict[int, bool]]:
    run_profit_by_row: dict[int, float | None] = {}
    run_rrr_by_row: dict[int, float] = {}
    run_fresh_by_row: dict[int, bool] = {}
    for (plan_row, recipe), run in zip(prepared_recipes, runs):
        breakdown = compute_run_profit(run)
        has_fresh_component_prices = state._run_has_fresh_component_prices(run)
        run_profit_by_row[int(plan_row.row_id)] = (
            float(breakdown.margin_percent) if has_fresh_component_prices else None
        )
        row_setup = state._setup_for_plan_row(setup, plan_row)
        run_rrr_by_row[int(plan_row.row_id)] = float(
            effective_return_fraction(setup=row_setup, recipe=recipe) * 100.0
        )
        run_fresh_by_row[int(plan_row.row_id)] = has_fresh_component_prices
    return run_profit_by_row, run_rrr_by_row, run_fresh_by_row


def filter_visible_runs(
    state,
    *,
    prepared_recipes: list[tuple[CraftPlanRow, Recipe]],
    runs: list[CraftRun],
    run_fresh_by_row: dict[int, bool],
) -> tuple[list[CraftRun], list[tuple[CraftPlanRow, Recipe]]]:
    visible_runs: list[CraftRun] = list(runs)
    visible_prepared_recipes: list[tuple[CraftPlanRow, Recipe]] = list(prepared_recipes)
    if not state._hide_rows_without_fresh_prices:
        return visible_runs, visible_prepared_recipes

    visible_runs = []
    visible_prepared_recipes = []
    for (plan_row, recipe), run in zip(prepared_recipes, runs):
        if run_fresh_by_row.get(int(plan_row.row_id), True):
            visible_prepared_recipes.append((plan_row, recipe))
            visible_runs.append(run)
    hidden_count = len(runs) - len(visible_runs)
    if hidden_count > 0:
        state._append_diag(
            f"Hidden {hidden_count} craft row(s) missing fresh AO Data component prices.",
            level="INFO",
        )
    return visible_runs, visible_prepared_recipes


def split_selected_visible_runs(
    *,
    visible_prepared_recipes: list[tuple[CraftPlanRow, Recipe]],
    visible_runs: list[CraftRun],
) -> tuple[list[CraftRun], list[tuple[CraftPlanRow, Recipe]]]:
    selected_visible_runs: list[CraftRun] = []
    selected_visible_prepared_recipes: list[tuple[CraftPlanRow, Recipe]] = []
    for (plan_row, recipe), run in zip(visible_prepared_recipes, visible_runs):
        if not plan_row.enabled:
            continue
        selected_visible_prepared_recipes.append((plan_row, recipe))
        selected_visible_runs.append(run)
    return selected_visible_runs, selected_visible_prepared_recipes


def selected_input_item_ids(
    *,
    selected_visible_runs: list[CraftRun],
    selected_journal_totals,
) -> list[str]:
    selected_inputs = [line for run in selected_visible_runs for line in run.inputs]
    item_ids: set[str] = {str(line.item.unique_name) for line in selected_inputs}
    for journal_line in selected_journal_totals.lines:
        if journal_line.empty_quantity > 0:
            item_ids.add(str(journal_line.empty_item_id))
    return sorted(item_ids)
