from __future__ import annotations

from dataclasses import dataclass

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import (
    CraftRun,
    CraftSetup,
    InputLine,
    OutputLine,
    PriceType,
    ProfitBreakdown,
    Recipe,
)
from albion_dps.market.pricing import choose_unit_price


@dataclass(frozen=True)
class BatchCraftRequest:
    recipe: Recipe
    quantity: int
    input_cities: dict[str, str] | None = None
    output_cities: dict[str, str] | None = None
    input_price_types: dict[str, PriceType] | None = None
    output_price_types: dict[str, PriceType] | None = None
    manual_input_prices: dict[str, int] | None = None
    manual_output_prices: dict[str, int] | None = None


@dataclass(frozen=True)
class OutputValuation:
    line: OutputLine
    gross_value: float
    fee_value: float
    tax_value: float
    net_value: float


def build_craft_run(
    *,
    recipe: Recipe,
    quantity: int,
    setup: CraftSetup,
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    input_cities: dict[str, str] | None = None,
    output_cities: dict[str, str] | None = None,
    input_price_types: dict[str, PriceType] | None = None,
    output_price_types: dict[str, PriceType] | None = None,
    manual_input_prices: dict[str, int] | None = None,
    manual_output_prices: dict[str, int] | None = None,
) -> CraftRun:
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    inputs = build_input_lines(
        recipe=recipe,
        quantity=quantity,
        setup=setup,
        price_index=price_index,
        input_cities=input_cities or {},
        input_price_types=input_price_types or {},
        manual_input_prices=manual_input_prices or {},
    )
    outputs = build_output_lines(
        recipe=recipe,
        quantity=quantity,
        setup=setup,
        price_index=price_index,
        output_cities=output_cities or {},
        output_price_types=output_price_types or {},
        manual_output_prices=manual_output_prices or {},
    )
    return CraftRun(
        recipe=recipe,
        quantity=quantity,
        setup=setup,
        inputs=tuple(inputs),
        outputs=tuple(outputs),
    )


def build_craft_runs_batch(
    *,
    setup: CraftSetup,
    requests: list[BatchCraftRequest],
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
) -> tuple[CraftRun, ...]:
    runs: list[CraftRun] = []
    for request in requests:
        runs.append(
            build_craft_run(
                recipe=request.recipe,
                quantity=request.quantity,
                setup=setup,
                price_index=price_index,
                input_cities=request.input_cities,
                output_cities=request.output_cities,
                input_price_types=request.input_price_types,
                output_price_types=request.output_price_types,
                manual_input_prices=request.manual_input_prices,
                manual_output_prices=request.manual_output_prices,
            )
        )
    return tuple(runs)


def build_input_lines(
    *,
    recipe: Recipe,
    quantity: int,
    setup: CraftSetup,
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    input_cities: dict[str, str],
    input_price_types: dict[str, PriceType],
    manual_input_prices: dict[str, int],
) -> list[InputLine]:
    lines: list[InputLine] = []
    return_fraction = effective_return_fraction(setup=setup, recipe=recipe)
    for component in recipe.components:
        city = (
            input_cities.get(component.item.unique_name)
            or setup.default_buy_city
            or setup.craft_city
        )
        price_type = input_price_types.get(component.item.unique_name, PriceType.BUY_ORDER)
        manual_price = manual_input_prices.get(component.item.unique_name)
        quote = _pick_quote(
            price_index,
            item_id=component.item.unique_name,
            city=city,
            quality=setup.quality,
        )
        quantity_raw = component.quantity * float(quantity)
        if component.returnable:
            quantity_effective = quantity_raw * (1.0 - return_fraction)
        else:
            quantity_effective = quantity_raw
        unit_price = _select_price(
            quote=quote,
            price_type=price_type,
            manual_price=manual_price,
        )
        lines.append(
            InputLine(
                item=component.item,
                quantity=quantity_effective,
                city=city,
                price_type=price_type,
                unit_price=float(unit_price),
            )
        )
    return lines


def compute_output_valuations(
    *,
    output_lines: list[OutputLine] | tuple[OutputLine, ...],
    station_fee_percent: float,
    market_tax_percent: float,
) -> list[OutputValuation]:
    gross_total = max(0.0, sum(line.total_value for line in output_lines))
    tax_total = max(0.0, gross_total * (market_tax_percent / 100.0))

    rows: list[OutputValuation] = []
    for line in output_lines:
        gross_value = max(0.0, float(line.total_value))
        share = (gross_value / gross_total) if gross_total > 0 else 0.0
        fee_value = _compute_station_fee_for_output_line(
            line=line,
            station_fee_percent=station_fee_percent,
        )
        tax_value = tax_total * share
        rows.append(
            OutputValuation(
                line=line,
                gross_value=gross_value,
                fee_value=fee_value,
                tax_value=tax_value,
                net_value=max(0.0, gross_value - fee_value - tax_value),
            )
        )
    return rows


def build_output_lines(
    *,
    recipe: Recipe,
    quantity: int,
    setup: CraftSetup,
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    output_cities: dict[str, str],
    output_price_types: dict[str, PriceType],
    manual_output_prices: dict[str, int],
) -> list[OutputLine]:
    lines: list[OutputLine] = []
    for output in recipe.outputs:
        city = (
            output_cities.get(output.item.unique_name)
            or setup.default_sell_city
            or setup.craft_city
        )
        price_type = output_price_types.get(output.item.unique_name, PriceType.SELL_ORDER)
        manual_price = manual_output_prices.get(output.item.unique_name)
        quote = _pick_quote(
            price_index,
            item_id=output.item.unique_name,
            city=city,
            quality=setup.quality,
        )
        unit_price = _select_price(
            quote=quote,
            price_type=price_type,
            manual_price=manual_price,
        )
        lines.append(
            OutputLine(
                item=output.item,
                quantity=output.quantity * float(quantity),
                city=city,
                price_type=price_type,
                unit_price=float(unit_price),
            )
        )
    return lines


def compute_profit_breakdown(
    *,
    input_cost: float,
    output_value: float,
    station_fee_percent: float,
    market_tax_percent: float,
    focus_used: float = 0.0,
) -> ProfitBreakdown:
    fee_value = max(0.0, output_value * (station_fee_percent / 100.0))
    tax_value = max(0.0, output_value * (market_tax_percent / 100.0))
    return ProfitBreakdown(
        input_cost=max(0.0, input_cost),
        output_value=max(0.0, output_value),
        station_fee=fee_value,
        market_tax=tax_value,
        focus_used=max(0.0, focus_used),
    )


def compute_run_profit(run: CraftRun) -> ProfitBreakdown:
    input_cost = sum(line.total_cost for line in run.inputs)
    output_value = sum(line.total_value for line in run.outputs)
    focus_used = float(run.recipe.focus_per_craft * run.quantity)
    station_fee = _compute_station_fee_total(
        output_lines=run.outputs,
        station_fee_percent=run.setup.station_fee_percent,
    )
    tax_value = max(0.0, output_value * (run.setup.market_tax_percent / 100.0))
    return ProfitBreakdown(
        input_cost=input_cost,
        output_value=output_value,
        station_fee=station_fee,
        market_tax=tax_value,
        focus_used=focus_used,
    )


def compute_batch_profit(runs: list[CraftRun] | tuple[CraftRun, ...]) -> ProfitBreakdown:
    summary = ProfitBreakdown()
    for run in runs:
        breakdown = compute_run_profit(run)
        summary.input_cost += breakdown.input_cost
        summary.output_value += breakdown.output_value
        summary.station_fee += breakdown.station_fee
        summary.market_tax += breakdown.market_tax
        summary.focus_used += breakdown.focus_used
    return summary


def _compute_station_fee_total(
    *,
    output_lines: list[OutputLine] | tuple[OutputLine, ...],
    station_fee_percent: float,
) -> float:
    return sum(
        _compute_station_fee_for_output_line(
            line=line,
            station_fee_percent=station_fee_percent,
        )
        for line in output_lines
    )


def _compute_station_fee_for_output_line(
    *,
    line: OutputLine,
    station_fee_percent: float,
) -> float:
    if line.item.tier is not None and int(line.item.tier) <= 2:
        return 0.0
    item_value = int(line.item.item_value or 0)
    if item_value <= 0:
        # Some item dumps omit item_value for specific variants.
        # Use a conservative approximation so fee does not collapse to zero.
        estimated = int(round(max(0.0, float(line.unit_price)) * 0.075))
        item_value = max(1, estimated)
    if item_value <= 0:
        return 0.0
    quantity = max(0.0, float(line.quantity))
    usage_fee = max(0.0, float(station_fee_percent))
    return quantity * (item_value * 0.1125) * (usage_fee / 100.0)


def effective_return_fraction(*, setup: CraftSetup, recipe: Recipe | None = None) -> float:
    explicit_percent = max(0.0, min(95.0, setup.return_rate_percent))
    if explicit_percent > 0.0:
        return explicit_percent / 100.0
    computed_percent = _auto_return_rate_percent(setup=setup, recipe=recipe)
    return min(0.95, computed_percent / 100.0)


def _auto_return_rate_percent(*, setup: CraftSetup, recipe: Recipe | None) -> float:
    # Formula from Albion wiki:
    # RRR = 1 - 1/(1 + ProductionBonus/100)
    daily_bonus = _normalize_daily_bonus_percent(setup.daily_bonus_percent)
    has_city_bonus = _has_city_bonus(setup=setup, recipe=recipe)
    is_refining = _is_refining_recipe(recipe)
    use_focus = bool(setup.focus_enabled)
    production_bonus = 18.0
    if is_refining:
        production_bonus += 40.0 if has_city_bonus else 0.0
    else:
        production_bonus += 15.0 if has_city_bonus else 0.0
    production_bonus += float(daily_bonus)
    if use_focus:
        production_bonus += 59.0
    rrr_fraction = 1.0 - (1.0 / (1.0 + (production_bonus / 100.0)))
    return max(0.0, min(95.0, rrr_fraction * 100.0))


def _normalize_daily_bonus_percent(value: float) -> int:
    raw = int(round(float(value)))
    if raw >= 15:
        return 20
    if raw >= 5:
        return 10
    return 0


def _is_refining_recipe(recipe: Recipe | None) -> bool:
    if recipe is None:
        return False
    station = (recipe.station or "").strip().lower()
    refining_stations = (
        "smelter",
        "lumbermill",
        "weaver",
        "tanner",
        "stonemason",
        "mill",
        "butcher",
    )
    return any(name in station for name in refining_stations)


def _has_city_bonus(*, setup: CraftSetup, recipe: Recipe | None) -> bool:
    if recipe is None:
        return False
    craft_city = setup.craft_city.strip()
    if not craft_city:
        return False

    explicit_city = recipe.city_bonus.strip()
    if explicit_city:
        return _normalize_location(explicit_city) == _normalize_location(craft_city)

    categories = _recipe_categories(recipe)
    if not categories:
        return False
    city_key = _normalize_location(craft_city)
    city_categories = _CITY_SPECIALIZATION_CATEGORIES.get(city_key, set())
    return any(category in city_categories for category in categories)


def _recipe_categories(recipe: Recipe) -> set[str]:
    categories: set[str] = set()
    station = _normalize_station(recipe.station)
    categories.update(_STATION_CATEGORY_MAP.get(station, set()))

    item_name = recipe.item.unique_name.strip().upper()
    for token, category in _ITEM_TOKEN_CATEGORY_MAP.items():
        if token in item_name:
            categories.add(category)
    if "_OFF_" in item_name:
        categories.add("off_hand")
    if "_HEAD_PLATE_" in item_name:
        categories.add("plate_helmet")
    if "_ARMOR_PLATE_" in item_name:
        categories.add("plate_armor")
    if "_SHOES_PLATE_" in item_name:
        categories.add("plate_shoes")
    if "_HEAD_LEATHER_" in item_name:
        categories.add("leather_helmet")
    if "_ARMOR_LEATHER_" in item_name:
        categories.add("leather_armor")
    if "_SHOES_LEATHER_" in item_name:
        categories.add("leather_shoes")
    if "_HEAD_CLOTH_" in item_name:
        categories.add("cloth_helmet")
    if "_ARMOR_CLOTH_" in item_name:
        categories.add("cloth_armor")
    if "_SHOES_CLOTH_" in item_name:
        categories.add("cloth_shoes")
    return categories


def _normalize_station(value: str) -> str:
    return "".join(ch for ch in value.strip().lower() if ch.isalnum())


def _normalize_location(value: str) -> str:
    lowered = value.strip().lower()
    out = "".join(ch for ch in lowered if ch.isalnum() or ch == " ")
    out = " ".join(out.split())
    return out


_STATION_CATEGORY_MAP: dict[str, set[str]] = {
    "axe": {"axe"},
    "bow": {"bow"},
    "crossbow": {"crossbow"},
    "dagger": {"dagger"},
    "hammer": {"hammer"},
    "mace": {"mace"},
    "spear": {"spear"},
    "sword": {"sword"},
    "quarterstaff": {"quarterstaff"},
    "arcanestaff": {"arcane"},
    "cursestaff": {"cursed"},
    "firestaff": {"fire"},
    "froststaff": {"frost"},
    "holystaff": {"holy"},
    "naturestaff": {"nature"},
    "shapeshifterstaff": {"shapeshifter"},
    "knuckles": {"wargloves"},
    "platehelmet": {"plate_helmet"},
    "platearmor": {"plate_armor"},
    "plateshoes": {"plate_shoes"},
    "leatherhelmet": {"leather_helmet"},
    "leatherarmor": {"leather_armor"},
    "leathershoes": {"leather_shoes"},
    "clothhelmet": {"cloth_helmet"},
    "clotharmor": {"cloth_armor"},
    "clothshoes": {"cloth_shoes"},
    "offhand": {"off_hand"},
    "offhands": {"off_hand"},
    "gatherergear": {"gatherer_gear"},
    "tools": {"tools"},
    "food": {"food"},
    "cape": {"cape"},
    "capes": {"cape"},
    "bag": {"bag"},
    "potion": {"potion"},
    "alchemy": {"potion"},
    "ore": {"ore"},
    "wood": {"wood"},
    "fiber": {"fiber"},
    "hide": {"hide"},
    "rock": {"stone"},
}


_ITEM_TOKEN_CATEGORY_MAP: dict[str, str] = {
    "_MAIN_AXE": "axe",
    "_2H_AXE": "axe",
    "_MAIN_BOW": "bow",
    "_2H_BOW": "bow",
    "_MAIN_CROSSBOW": "crossbow",
    "_2H_CROSSBOW": "crossbow",
    "_MAIN_DAGGER": "dagger",
    "_2H_DAGGER": "dagger",
    "_MAIN_HAMMER": "hammer",
    "_2H_HAMMER": "hammer",
    "_MAIN_MACE": "mace",
    "_2H_MACE": "mace",
    "_MAIN_SPEAR": "spear",
    "_2H_SPEAR": "spear",
    "_MAIN_SWORD": "sword",
    "_2H_SWORD": "sword",
    "_MAIN_QUARTERSTAFF": "quarterstaff",
    "_2H_QUARTERSTAFF": "quarterstaff",
    "_MAIN_ARCANESTAFF": "arcane",
    "_2H_ARCANESTAFF": "arcane",
    "_MAIN_CURSEDSTAFF": "cursed",
    "_2H_CURSEDSTAFF": "cursed",
    "_MAIN_FIRESTAFF": "fire",
    "_2H_FIRESTAFF": "fire",
    "_MAIN_FROSTSTAFF": "frost",
    "_2H_FROSTSTAFF": "frost",
    "_MAIN_HOLYSTAFF": "holy",
    "_2H_HOLYSTAFF": "holy",
    "_MAIN_NATURESTAFF": "nature",
    "_2H_NATURESTAFF": "nature",
    "_MAIN_SHAPESHIFTERSTAFF": "shapeshifter",
    "_2H_SHAPESHIFTERSTAFF": "shapeshifter",
    "_MAIN_KNUCKLES": "wargloves",
    "_2H_KNUCKLES": "wargloves",
}


_CITY_SPECIALIZATION_CATEGORIES: dict[str, set[str]] = {
    "martlock": {"axe", "quarterstaff", "frost", "plate_shoes", "hide"},
    "bridgewatch": {"crossbow", "dagger", "cursed", "plate_armor", "cloth_shoes", "stone"},
    "lymhurst": {"sword", "bow", "arcane", "leather_helmet", "leather_shoes", "fiber"},
    "fort sterling": {"hammer", "spear", "holy", "plate_helmet", "cloth_armor", "wood"},
    "fortsterling": {"hammer", "spear", "holy", "plate_helmet", "cloth_armor", "wood"},
    "thetford": {"mace", "nature", "fire", "leather_armor", "cloth_helmet", "ore"},
    "caerleon": {"wargloves", "shapeshifter", "gatherer_gear", "off_hand", "tools", "food"},
    "brecilien": {"cape", "bag", "potion"},
    "arthurs rest": {"axe", "crossbow", "hammer", "mace", "sword", "wargloves", "plate_helmet", "plate_armor", "plate_shoes"},
    "arthur's rest": {"axe", "crossbow", "hammer", "mace", "sword", "wargloves", "plate_helmet", "plate_armor", "plate_shoes"},
    "merlyns rest": {"bow", "dagger", "quarterstaff", "spear", "nature", "shapeshifter", "leather_helmet", "leather_armor", "leather_shoes"},
    "merlyn's rest": {"bow", "dagger", "quarterstaff", "spear", "nature", "shapeshifter", "leather_helmet", "leather_armor", "leather_shoes"},
    "morganas rest": {"arcane", "cursed", "fire", "frost", "holy", "cloth_helmet", "cloth_armor", "cloth_shoes"},
    "morgana's rest": {"arcane", "cursed", "fire", "frost", "holy", "cloth_helmet", "cloth_armor", "cloth_shoes"},
}


def _pick_quote(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
) -> MarketPriceRecord | None:
    key = (item_id, city, quality)
    quote = price_index.get(key)
    if quote is not None:
        return quote
    key_q1 = (item_id, city, 1)
    quote = price_index.get(key_q1)
    if quote is not None:
        return quote
    for candidate_key, candidate in price_index.items():
        if candidate_key[0] == item_id and candidate_key[1] == city:
            return candidate
    return None


def _select_price(
    *,
    quote: MarketPriceRecord | None,
    price_type: PriceType,
    manual_price: int | None,
) -> int:
    if _has_manual_price(manual_price):
        return int(manual_price)
    if quote is None:
        if price_type == PriceType.MANUAL:
            return int(manual_price or 0)
        return 0
    avg_price = None
    if quote.buy_price_max > 0 and quote.sell_price_min > 0:
        avg_price = int((quote.buy_price_max + quote.sell_price_min) / 2)
    return choose_unit_price(
        price_type=price_type,
        buy_price_max=quote.buy_price_max,
        sell_price_min=quote.sell_price_min,
        average_price=avg_price,
        manual_price=manual_price,
    )


def _has_manual_price(value: int | None) -> bool:
    return value is not None and int(value) > 0
