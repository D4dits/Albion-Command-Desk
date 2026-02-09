from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict

from albion_dps.market.models import InputLine, OutputLine


@dataclass(frozen=True)
class ShoppingEntry:
    item_id: str
    item_name: str
    city: str
    price_type: str
    quantity: float
    unit_price: float
    total_cost: float


@dataclass(frozen=True)
class SellingEntry:
    item_id: str
    item_name: str
    city: str
    price_type: str
    quantity: float
    unit_price: float
    total_value: float


def build_shopping_entries(lines: list[InputLine]) -> list[ShoppingEntry]:
    grouped: dict[tuple[str, str, str], dict[str, float | str]] = defaultdict(
        lambda: {
            "item_name": "",
            "quantity": 0.0,
            "total_cost": 0.0,
        }
    )
    for line in lines:
        key = (line.item.unique_name, line.city, line.price_type.value)
        bucket = grouped[key]
        bucket["item_name"] = line.item.display_name or line.item.unique_name
        bucket["quantity"] = float(bucket["quantity"]) + line.quantity
        bucket["total_cost"] = float(bucket["total_cost"]) + line.total_cost

    entries: list[ShoppingEntry] = []
    for (item_id, city, price_type), bucket in grouped.items():
        quantity = float(bucket["quantity"])
        total_cost = float(bucket["total_cost"])
        unit_price = (total_cost / quantity) if quantity > 0 else 0.0
        entries.append(
            ShoppingEntry(
                item_id=item_id,
                item_name=str(bucket["item_name"] or item_id),
                city=city,
                price_type=price_type,
                quantity=quantity,
                unit_price=unit_price,
                total_cost=total_cost,
            )
        )
    entries.sort(key=lambda x: (x.city.lower(), x.item_name.lower(), x.price_type))
    return entries


def build_selling_entries(lines: list[OutputLine]) -> list[SellingEntry]:
    grouped: dict[tuple[str, str, str], dict[str, float | str]] = defaultdict(
        lambda: {
            "item_name": "",
            "quantity": 0.0,
            "total_value": 0.0,
        }
    )
    for line in lines:
        key = (line.item.unique_name, line.city, line.price_type.value)
        bucket = grouped[key]
        bucket["item_name"] = line.item.display_name or line.item.unique_name
        bucket["quantity"] = float(bucket["quantity"]) + line.quantity
        bucket["total_value"] = float(bucket["total_value"]) + line.total_value

    entries: list[SellingEntry] = []
    for (item_id, city, price_type), bucket in grouped.items():
        quantity = float(bucket["quantity"])
        total_value = float(bucket["total_value"])
        unit_price = (total_value / quantity) if quantity > 0 else 0.0
        entries.append(
            SellingEntry(
                item_id=item_id,
                item_name=str(bucket["item_name"] or item_id),
                city=city,
                price_type=price_type,
                quantity=quantity,
                unit_price=unit_price,
                total_value=total_value,
            )
        )
    entries.sort(key=lambda x: (x.city.lower(), x.item_name.lower(), x.price_type))
    return entries


def aggregate_shopping(lines: list[InputLine]) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], float] = defaultdict(float)
    for line in lines:
        key = (line.item.unique_name, line.city)
        grouped[key] += line.quantity
    return dict(grouped)


def aggregate_selling(lines: list[OutputLine]) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], float] = defaultdict(float)
    for line in lines:
        key = (line.item.unique_name, line.city)
        grouped[key] += line.quantity
    return dict(grouped)
