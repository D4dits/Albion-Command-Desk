from __future__ import annotations

from albion_dps.market.models import InputLine, ItemRef, PriceType
from albion_dps.qt.market.list_models import InputPreviewRow, OutputPreviewRow


def merge_journal_input_rows(
    *,
    input_acc: dict[tuple[str, str, str, float], dict[str, object]],
    journal_totals,
    buy_city: str,
    quality: int,
    price_age_text_for_item_ids,
    journal_display_name,
    input_price_types: dict[str, PriceType] | None,
    to_price_type,
    include_item_ref: bool,
) -> None:
    for journal_line in journal_totals.lines:
        if journal_line.empty_quantity <= 0:
            continue
        empty_unit_price = float(journal_line.input_cost) / float(journal_line.empty_quantity)
        empty_item_id = str(journal_line.empty_item_id)
        empty_name = f"{journal_display_name(journal_line.kind, journal_line.tier)} (empty)"
        journal_input_price_type = str(journal_line.input_price_mode or PriceType.SELL_ORDER.value)
        key = (
            empty_item_id,
            buy_city,
            journal_input_price_type,
            float(empty_unit_price),
        )
        row = input_acc.get(key)
        journal_input_age = price_age_text_for_item_ids(
            item_ids=[
                str(journal_line.empty_price_item_id or ""),
                f"{empty_item_id}_EMPTY",
                empty_item_id,
            ],
            city=buy_city,
            quality=quality,
            price_type=journal_input_price_type,
        )
        if journal_input_age.strip().lower() in {"", "n/a", "unknown"}:
            journal_input_age = "npc"
        if row is None:
            payload: dict[str, object] = {
                "item_id": empty_item_id,
                "item": empty_name,
                "city": buy_city,
                "price_type": journal_input_price_type,
                "price_age_text": journal_input_age,
                "unit_price": float(empty_unit_price),
                "quantity": float(journal_line.empty_quantity),
                "returnable": False,
            }
            if include_item_ref:
                payload["item_ref"] = ItemRef(
                    unique_name=empty_item_id,
                    display_name=empty_name,
                    tier=int(journal_line.tier),
                    enchantment=0,
                )
                payload["total_cost"] = float(journal_line.input_cost)
            input_acc[key] = payload
        else:
            row["quantity"] = float(row["quantity"]) + float(journal_line.empty_quantity)
            if include_item_ref:
                row["total_cost"] = float(row["total_cost"]) + float(journal_line.input_cost)
        if input_price_types is not None:
            input_price_types.setdefault(empty_item_id, to_price_type(journal_input_price_type))


def build_input_rows(
    *,
    input_acc: dict[tuple[str, str, str, float], dict[str, object]],
    input_stock_quantities: dict[str, float],
    manual_input_prices: dict[str, int],
    completed_input_item_ids: set[str],
    need_quantity_with_safety_buffer,
    input_preview_row_key,
    sort_key,
) -> tuple[list[InputPreviewRow], list[InputLine]]:
    input_rows: list[InputPreviewRow] = []
    adjusted_inputs: list[InputLine] = []
    for row in input_acc.values():
        item_id = str(row["item_id"])
        quantity_raw = float(row["quantity"])
        is_returnable = bool(row.get("returnable", False))
        need_qty = float(max(0, need_quantity_with_safety_buffer(quantity_raw, is_returnable)))
        stock_qty = float(max(0.0, input_stock_quantities.get(item_id, 0.0)))
        stock_qty = min(stock_qty, need_qty)
        buy_qty = max(0.0, need_qty - stock_qty)
        unit_price = float(row["unit_price"])
        total_cost = float(buy_qty * unit_price)
        input_rows.append(
            InputPreviewRow(
                item_id=item_id,
                row_key=input_preview_row_key(item_id, str(row["city"]), str(row["price_type"])),
                item=str(row["item"]),
                quantity=need_qty,
                stock_quantity=stock_qty,
                buy_quantity=buy_qty,
                city=str(row["city"]),
                price_type=str(row["price_type"]),
                price_age_text=str(row["price_age_text"]),
                manual_price=manual_input_prices.get(item_id, 0),
                unit_price=unit_price,
                total_cost=total_cost,
                completed=item_id in completed_input_item_ids or buy_qty <= 0.0,
            )
        )
        item_ref = row.get("item_ref")
        if isinstance(item_ref, ItemRef):
            adjusted_inputs.append(
                InputLine(
                    item=item_ref,
                    quantity=buy_qty,
                    city=str(row["city"]),
                    price_type=PriceType(str(row["price_type"])),
                    unit_price=unit_price,
                )
            )
    input_rows.sort(key=sort_key)
    return input_rows, adjusted_inputs


def accumulate_output_rows(
    *,
    valuations,
    quality: int,
    price_age_text,
    item_label,
) -> dict[tuple[str, str, str, float], dict[str, object]]:
    output_acc: dict[tuple[str, str, str, float], dict[str, object]] = {}
    for valuation in valuations:
        line = valuation.line
        key = (line.item.unique_name, line.city, line.price_type.value, float(line.unit_price))
        row = output_acc.get(key)
        if row is None:
            output_acc[key] = {
                "item_id": line.item.unique_name,
                "item": item_label(line.item.display_name, line.item.unique_name),
                "city": line.city,
                "price_type": line.price_type.value,
                "price_age_text": price_age_text(
                    item_id=line.item.unique_name,
                    city=line.city,
                    quality=quality,
                    price_type=line.price_type.value,
                ),
                "unit_price": float(line.unit_price),
                "quantity": float(line.quantity),
                "total_value": float(valuation.gross_value),
                "fee_value": float(valuation.fee_value),
                "tax_value": float(valuation.tax_value),
                "net_value": float(valuation.net_value),
            }
        else:
            row["quantity"] = float(row["quantity"]) + float(line.quantity)
            row["total_value"] = float(row["total_value"]) + float(valuation.gross_value)
            row["fee_value"] = float(row["fee_value"]) + float(valuation.fee_value)
            row["tax_value"] = float(row["tax_value"]) + float(valuation.tax_value)
            row["net_value"] = float(row["net_value"]) + float(valuation.net_value)
    return output_acc


def merge_journal_output_rows(
    *,
    output_acc: dict[tuple[str, str, str, float], dict[str, object]],
    journal_totals,
    sell_city: str,
    quality: int,
    price_age_text_for_item_ids,
    journal_display_name,
    output_price_types: dict[str, PriceType] | None,
    output_cities: dict[str, str] | None,
    to_price_type,
) -> None:
    for journal_line in journal_totals.lines:
        if journal_line.full_quantity <= 0:
            continue
        full_item_id = str(journal_line.full_item_id)
        full_name = f"{journal_display_name(journal_line.kind, journal_line.tier)} (full)"
        full_unit_price = float(journal_line.output_value) / float(journal_line.full_quantity)
        journal_output_price_type = str(journal_line.output_price_mode or PriceType.SELL_ORDER.value)
        key = (
            full_item_id,
            sell_city,
            journal_output_price_type,
            float(full_unit_price),
        )
        row = output_acc.get(key)
        if row is None:
            output_acc[key] = {
                "item_id": full_item_id,
                "item": full_name,
                "city": sell_city,
                "price_type": journal_output_price_type,
                "price_age_text": price_age_text_for_item_ids(
                    item_ids=[str(journal_line.full_price_item_id or ""), full_item_id],
                    city=sell_city,
                    quality=quality,
                    price_type=journal_output_price_type,
                ),
                "unit_price": float(full_unit_price),
                "quantity": float(journal_line.full_quantity),
                "total_value": float(journal_line.output_value),
                "fee_value": 0.0,
                "tax_value": float(journal_line.market_tax),
                "net_value": float(journal_line.output_value - journal_line.market_tax),
            }
        else:
            row["quantity"] = float(row["quantity"]) + float(journal_line.full_quantity)
            row["total_value"] = float(row["total_value"]) + float(journal_line.output_value)
            row["tax_value"] = float(row["tax_value"]) + float(journal_line.market_tax)
            row["net_value"] = float(row["net_value"]) + float(journal_line.output_value - journal_line.market_tax)
        if output_price_types is not None:
            output_price_types.setdefault(full_item_id, to_price_type(journal_output_price_type))
        if output_cities is not None and sell_city:
            output_cities.setdefault(full_item_id, sell_city)


def build_output_rows(
    *,
    output_acc: dict[tuple[str, str, str, float], dict[str, object]],
    manual_output_prices: dict[str, int],
    completed_output_item_ids: set[str],
) -> list[OutputPreviewRow]:
    output_rows = [
        OutputPreviewRow(
            item_id=str(row["item_id"]),
            item=str(row["item"]),
            quantity=float(row["quantity"]),
            city=str(row["city"]),
            price_type=str(row["price_type"]),
            price_age_text=str(row.get("price_age_text", "n/a")),
            manual_price=manual_output_prices.get(str(row["item_id"]), 0),
            unit_price=float(row["unit_price"]),
            total_value=float(row["total_value"]),
            fee_value=float(row["fee_value"]),
            tax_value=float(row["tax_value"]),
            net_value=float(row["net_value"]),
            completed=str(row["item_id"]) in completed_output_item_ids,
        )
        for row in output_acc.values()
    ]
    output_rows.sort(key=lambda x: (x.item.lower(), x.city.lower()))
    return output_rows
