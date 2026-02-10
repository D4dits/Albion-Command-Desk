#!/usr/bin/env bash
set -euo pipefail

python tools/market/extract_recipes_from_items.py "$@"
