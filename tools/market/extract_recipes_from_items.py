from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from albion_dps.market.recipes_from_items import extract_recipes_from_items_json


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract normalized market recipes from local items.json (game data).",
    )
    parser.add_argument(
        "--items-json",
        default="data/items.json",
        help="Path to extracted game items.json.",
    )
    parser.add_argument(
        "--indexed-items",
        default="data/indexedItems.json",
        help="Optional path to indexedItems.json for readable display names.",
    )
    parser.add_argument(
        "--output",
        default="tools/market/sources/recipes_from_items.json",
        help="Output path for extracted normalized recipe rows.",
    )
    parser.add_argument(
        "--report",
        default="artifacts/market/recipes_from_items_report.json",
        help="Output path for extraction report JSON.",
    )
    parser.add_argument(
        "--exclude-locked",
        action="store_true",
        help="Exclude rows with @unlockedtocraft=false.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    items_path = Path(args.items_json)
    if not items_path.exists():
        print(f"items.json not found: {items_path}", file=sys.stderr)
        return 2

    indexed_path = Path(args.indexed_items)
    indexed_value = indexed_path if indexed_path.exists() else None

    rows, report = extract_recipes_from_items_json(
        items_json_path=items_path,
        indexed_items_path=indexed_value,
        include_locked=not bool(args.exclude_locked),
    )
    output_path = Path(args.output)
    report_path = Path(args.report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"recipes_out: {report.recipes_out}")
    print(f"craftable_nodes: {report.craftable_nodes}")
    print(f"multi_requirement_nodes: {report.multi_requirement_nodes}")
    print(f"skipped_no_resources: {report.skipped_no_resources}")
    print(f"output: {output_path}")
    print(f"report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
