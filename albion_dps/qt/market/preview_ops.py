from __future__ import annotations

from typing import Callable, Sequence

from albion_dps.market.engine import compute_output_valuations, effective_return_fraction
from albion_dps.market.models import CraftRun, CraftSetup, InputLine, ProfitBreakdown, Recipe
from albion_dps.qt.market.list_models import BreakdownRow, CraftPlanRow, ResultItemRow
from albion_dps.qt.market.state_types import _JournalTotals


def build_results_rows_from_runs(
    *,
    runs: list[CraftRun],
    setup: CraftSetup,
    results_sort_key: str,
    estimate_journal_totals: Callable[[list[CraftRun]], _JournalTotals],
    demand_proxy_percent: Callable[[str, str], float],
    item_label: Callable[[str, str], str],
    result_row_profit_and_margin: Callable[[float, float], tuple[float, float]],
) -> list[ResultItemRow]:
    acc: dict[tuple[str, str, str, float], dict[str, float | str]] = {}
    for run in runs:
        if not run.outputs:
            continue
        run_journal_totals = estimate_journal_totals([run])
        run_input_cost = float(sum(line.total_cost for line in run.inputs) + float(run_journal_totals.input_cost))
        valuations = compute_output_valuations(
            output_lines=run.outputs,
            station_fee_percent=setup.station_fee_percent,
            market_tax_percent=setup.market_tax_percent,
        )
        run_revenue_total = max(0.0, sum(float(v.gross_value) for v in valuations))
        run_journal_gross = float(run_journal_totals.output_value)
        run_journal_tax = float(run_journal_totals.market_tax)
        run_journal_net = max(0.0, run_journal_gross - run_journal_tax)
        for valuation in valuations:
            line = valuation.line
            share = (float(valuation.gross_value) / run_revenue_total) if run_revenue_total > 0 else 0.0
            allocated_cost = run_input_cost * share
            allocated_journal_gross = run_journal_gross * share
            allocated_journal_tax = run_journal_tax * share
            allocated_journal_net = run_journal_net * share
            key = (line.item.unique_name, line.city, line.price_type.value, float(line.unit_price))
            row = acc.get(key)
            if row is None:
                acc[key] = {
                    "item_id": line.item.unique_name,
                    "item": item_label(line.item.display_name, line.item.unique_name),
                    "quantity": float(line.quantity),
                    "city": line.city,
                    "price_type": line.price_type.value,
                    "unit_price": float(line.unit_price),
                    "total_value": float(valuation.gross_value + allocated_journal_gross),
                    "allocated_cost": float(allocated_cost),
                    "fee_value": float(valuation.fee_value),
                    "tax_value": float(valuation.tax_value + allocated_journal_tax),
                    "net_value": float(valuation.net_value + allocated_journal_net),
                }
            else:
                row["quantity"] = float(row["quantity"]) + float(line.quantity)
                row["total_value"] = float(row["total_value"]) + float(valuation.gross_value + allocated_journal_gross)
                row["allocated_cost"] = float(row["allocated_cost"]) + float(allocated_cost)
                row["fee_value"] = float(row["fee_value"]) + float(valuation.fee_value)
                row["tax_value"] = float(row["tax_value"]) + float(valuation.tax_value + allocated_journal_tax)
                row["net_value"] = float(row["net_value"]) + float(valuation.net_value + allocated_journal_net)

    rows: list[ResultItemRow] = []
    for output in acc.values():
        allocated_cost = float(output["allocated_cost"])
        fee_value = float(output["fee_value"])
        tax_value = float(output["tax_value"])
        net_value = float(output["net_value"])
        profit, margin = result_row_profit_and_margin(allocated_cost, net_value)
        rows.append(
            ResultItemRow(
                item_id=str(output["item_id"]),
                item=str(output["item"]),
                city=str(output["city"]),
                quantity=float(output["quantity"]),
                unit_price=float(output["unit_price"]),
                revenue=float(output["total_value"]),
                allocated_cost=float(allocated_cost),
                fee_value=float(fee_value),
                tax_value=float(tax_value),
                profit=float(profit),
                margin_percent=float(margin),
                demand_proxy=float(demand_proxy_percent(str(output["item_id"]), str(output["city"]))),
            )
        )

    if results_sort_key == "margin":
        rows.sort(key=lambda x: x.margin_percent, reverse=True)
    elif results_sort_key == "revenue":
        rows.sort(key=lambda x: x.revenue, reverse=True)
    else:
        rows.sort(key=lambda x: x.profit, reverse=True)
    return rows


def accumulate_input_preview_rows(
    *,
    prepared_recipes: list[tuple[CraftPlanRow, Recipe]],
    runs: list[CraftRun],
    price_age_text: Callable[[str, str, str], str],
    item_label: Callable[[str, str], str],
    minimal_upfront_quantity_for_batches: Callable[[Sequence[tuple[float, float]]], float],
    upfront_return_safety_units: Callable[[Sequence[tuple[float, float]]], int],
) -> dict[tuple[str, str, str, float], dict[str, object]]:
    input_acc: dict[tuple[str, str, str, float], dict[str, object]] = {}
    for (_, recipe), run in zip(prepared_recipes, runs):
        return_fraction = effective_return_fraction(setup=run.setup, recipe=recipe)
        for component, line in zip(recipe.components, run.inputs):
            key = (line.item.unique_name, line.city, line.price_type.value, float(line.unit_price))
            row = input_acc.get(key)
            if row is None:
                input_acc[key] = {
                    "item_id": line.item.unique_name,
                    "item": item_label(line.item.display_name, line.item.unique_name),
                    "item_ref": line.item,
                    "city": line.city,
                    "price_type": line.price_type.value,
                    "price_age_text": price_age_text(line.item.unique_name, line.city, line.price_type.value),
                    "unit_price": float(line.unit_price),
                    "quantity": 0.0,
                    "total_cost": 0.0,
                    "returnable": bool(component.returnable),
                    "return_batches": [],
                }
                row = input_acc[key]
            if component.returnable:
                batches = row.setdefault("return_batches", [])
                if isinstance(batches, list):
                    batches.extend(
                        [
                            (float(component.quantity), float(return_fraction))
                            for _ in range(int(run.quantity))
                        ]
                    )
                effective_batches = batches if isinstance(batches, list) else []
                preview_quantity = minimal_upfront_quantity_for_batches(effective_batches)
                preview_quantity += float(upfront_return_safety_units(effective_batches))
            else:
                preview_quantity = float(row.get("quantity", 0.0)) + float(line.quantity)
            row["quantity"] = float(preview_quantity)
            row["total_cost"] = float(preview_quantity * float(line.unit_price))
            row["returnable"] = bool(row.get("returnable", False) or component.returnable)
    return input_acc


def build_breakdown_rows(
    *,
    selected_material_input_total_cost: float,
    journal_totals: _JournalTotals,
    breakdown: ProfitBreakdown,
) -> list[BreakdownRow]:
    rows: list[BreakdownRow] = [
        BreakdownRow(label="Raw materials", value=float(selected_material_input_total_cost)),
    ]
    if journal_totals.input_cost > 0:
        rows.append(BreakdownRow(label="Journals (empty)", value=float(journal_totals.input_cost)))
    rows.append(BreakdownRow(label="Station fee", value=float(breakdown.station_fee)))
    rows.append(BreakdownRow(label="Market tax", value=float(breakdown.market_tax)))
    if journal_totals.output_value > 0:
        rows.append(BreakdownRow(label="Journals (full)", value=float(journal_totals.output_value)))
    rows.append(BreakdownRow(label="Net profit", value=float(breakdown.net_profit)))
    return rows


def compute_input_total_from_lines(
    *,
    input_lines: list[InputLine] | tuple[InputLine, ...],
    input_stock_quantities: dict[str, float],
) -> float:
    input_acc: dict[tuple[str, str, str, float], dict[str, float | str]] = {}
    for line in input_lines:
        key = (line.item.unique_name, line.city, line.price_type.value, float(line.unit_price))
        row = input_acc.get(key)
        if row is None:
            input_acc[key] = {
                "item_id": line.item.unique_name,
                "city": line.city,
                "price_type": line.price_type.value,
                "unit_price": float(line.unit_price),
                "quantity": float(line.quantity),
            }
        else:
            row["quantity"] = float(row["quantity"]) + float(line.quantity)

    total_cost = 0.0
    for row in input_acc.values():
        item_id = str(row["item_id"])
        quantity_raw = float(row["quantity"])
        stock_qty = float(max(0.0, input_stock_quantities.get(item_id, 0.0)))
        stock_qty = min(stock_qty, quantity_raw)
        buy_qty = max(0.0, quantity_raw - stock_qty)
        unit_price = float(row["unit_price"])
        total_cost += float(buy_qty * unit_price)

    return float(total_cost)


__all__ = [
    "accumulate_input_preview_rows",
    "build_breakdown_rows",
    "build_results_rows_from_runs",
    "compute_input_total_from_lines",
]
