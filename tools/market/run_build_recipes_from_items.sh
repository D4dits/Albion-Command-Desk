#!/usr/bin/env bash
set -euo pipefail

python tools/market/extract_recipes_from_items.py \
  --items-json "${1:-data/items.json}" \
  --indexed-items "data/indexedItems.json" \
  --output "tools/market/sources/recipes_from_items.json" \
  --report "artifacts/market/recipes_from_items_report.json"

python tools/market/build_recipes.py \
  --input "tools/market/sources/recipes_from_items.json" \
  --output "albion_dps/market/data/recipes.json" \
  --report "artifacts/market/recipes_build_report.json" \
  --strict \
  --min-recipes 100
