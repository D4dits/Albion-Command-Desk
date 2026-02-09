from __future__ import annotations

from albion_dps.market.models import InputLine, ItemRef, OutputLine, PriceType
from albion_dps.market.planner import build_selling_entries, build_shopping_entries


def test_build_shopping_entries_groups_by_city_and_price_type() -> None:
    bars = ItemRef(unique_name="T4_METALBAR", display_name="Metal Bar", tier=4, enchantment=0)
    lines = [
        InputLine(item=bars, quantity=10.0, city="Bridgewatch", price_type=PriceType.SELL_ORDER, unit_price=1000.0),
        InputLine(item=bars, quantity=5.0, city="Bridgewatch", price_type=PriceType.SELL_ORDER, unit_price=900.0),
        InputLine(item=bars, quantity=3.0, city="Bridgewatch", price_type=PriceType.BUY_ORDER, unit_price=850.0),
    ]
    entries = build_shopping_entries(lines)
    assert len(entries) == 2
    sell_row = [x for x in entries if x.price_type == PriceType.SELL_ORDER.value][0]
    assert round(sell_row.quantity, 2) == 15.0
    assert round(sell_row.total_cost, 2) == 14500.0
    assert round(sell_row.unit_price, 2) == round(14500.0 / 15.0, 2)


def test_build_selling_entries_groups_by_city_and_price_type() -> None:
    sword = ItemRef(unique_name="T4_MAIN_SWORD", display_name="Broadsword", tier=4, enchantment=0)
    lines = [
        OutputLine(item=sword, quantity=2.0, city="Bridgewatch", price_type=PriceType.BUY_ORDER, unit_price=15000.0),
        OutputLine(item=sword, quantity=1.0, city="Bridgewatch", price_type=PriceType.BUY_ORDER, unit_price=15500.0),
    ]
    entries = build_selling_entries(lines)
    assert len(entries) == 1
    row = entries[0]
    assert row.item_id == "T4_MAIN_SWORD"
    assert round(row.quantity, 2) == 3.0
    assert round(row.total_value, 2) == 45500.0
