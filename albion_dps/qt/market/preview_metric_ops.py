from __future__ import annotations

from albion_dps.qt.market.preview_ops import (
    accumulate_input_preview_rows,
    build_breakdown_rows,
    build_results_rows_from_runs,
    compute_input_total_from_lines,
)


def build_results_rows(state, *, runs, input_total, item_label, result_row_profit_and_margin):
    _ = input_total
    return build_results_rows_from_runs(
        runs=runs,
        setup=state._setup,
        results_sort_key=state._results_sort_key,
        estimate_journal_totals=lambda selected_runs: state._estimate_journal_totals(
            runs=selected_runs,
            setup=state._setup,
            price_index=state._price_index,
        ),
        demand_proxy_percent=lambda item_id, city: state._demand_proxy_percent(
            item_id=item_id,
            city=city,
            quality=state._setup.quality,
        ),
        item_label=item_label,
        result_row_profit_and_margin=lambda allocated_cost, net_value: result_row_profit_and_margin(
            allocated_cost=allocated_cost,
            net_value=net_value,
        ),
    )


def accumulate_inputs(
    state,
    *,
    prepared_recipes,
    runs,
    item_label,
    minimal_upfront_quantity_for_batches,
    upfront_return_safety_units,
):
    return accumulate_input_preview_rows(
        prepared_recipes=prepared_recipes,
        runs=runs,
        price_age_text=lambda item_id, city, price_type: state._price_age_text(
            item_id=item_id,
            city=city,
            quality=state._setup.quality,
            price_type=price_type,
        ),
        item_label=item_label,
        minimal_upfront_quantity_for_batches=minimal_upfront_quantity_for_batches,
        upfront_return_safety_units=upfront_return_safety_units,
    )


def build_breakdown(state):
    return build_breakdown_rows(
        selected_material_input_total_cost=state._selected_material_input_total_cost,
        journal_totals=state._results_journal_totals,
        breakdown=state._breakdown,
    )


def compute_input_total(state, *, input_lines, prepared_recipes):
    _ = prepared_recipes
    return compute_input_total_from_lines(
        input_lines=input_lines,
        input_stock_quantities=state._input_stock_quantities,
    )
