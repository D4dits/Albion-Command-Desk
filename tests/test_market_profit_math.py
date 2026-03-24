from __future__ import annotations

from albion_dps.market.models import ProfitBreakdown
from albion_dps.qt.market import state as market_state


def test_result_row_profit_and_margin_use_net_value_against_allocated_cost() -> None:
    profit, margin = market_state._result_row_profit_and_margin(
        allocated_cost=399177.0,
        net_value=767039.0,
    )

    assert profit == 367862.0
    assert margin == ((767039.0 - 399177.0) / 399177.0) * 100.0


def test_profit_breakdown_margin_is_based_on_input_cost() -> None:
    breakdown = ProfitBreakdown(
        input_cost=399177.0,
        output_value=983918.0,
        station_fee=27378.0,
        market_tax=70304.0,
    )

    assert breakdown.net_profit == 487059.0
    assert breakdown.margin_percent == (487059.0 / 399177.0) * 100.0


def test_result_row_formula_matches_profit_breakdown_when_net_value_is_precomputed() -> None:
    breakdown = ProfitBreakdown(
        input_cost=50000.0,
        output_value=90000.0,
        station_fee=4500.0,
        market_tax=9000.0,
    )

    profit, margin = market_state._result_row_profit_and_margin(
        allocated_cost=breakdown.input_cost,
        net_value=breakdown.output_value - breakdown.station_fee - breakdown.market_tax,
    )

    assert profit == breakdown.net_profit
    assert margin == breakdown.margin_percent
