from __future__ import annotations

from collections import defaultdict

from albion_dps.market.models import InputLine, OutputLine


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

