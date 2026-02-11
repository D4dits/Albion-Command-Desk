# Market Dataset Update and Cache Cleanup

## Goal
Rebuild Market recipes from local Albion data and clear stale market cache when needed.

## Prerequisites
- Activated project venv.
- Local game files available (`data/items.json` pipeline source).

## Step 1: Refresh local game item databases
Windows:
```powershell
.\tools\extract_items\run_extract_items.ps1 -GameRoot "C:\Program Files\Albion Online"
```

Linux/macOS:
```bash
./tools/extract_items/run_extract_items.sh --game-root "/path/to/Albion Online"
```

Expected outputs:
- `data/indexedItems.json`
- `data/items.json`
- `data/map_index.json`

## Step 2: Rebuild market recipes from `items.json`
Windows:
```powershell
.\tools\market\run_build_recipes_from_items.ps1 -Strict
```

Linux/macOS:
```bash
./tools/market/run_build_recipes_from_items.sh --strict
```

Expected outputs:
- `albion_dps/market/data/recipes.json`
- `artifacts/market/recipes_from_items_report.json`
- `artifacts/market/recipes_build_report.json`

## Step 3: Run regression tests
```powershell
python -m pytest -q tests/test_market_dataset_regression.py tests/test_market_catalog.py
```

Optional full market suite:
```powershell
python -m pytest -q tests/test_market_*.py tests/test_qt_smoke.py
```

## Step 4: Cleanup market cache (if prices behave unexpectedly)
Delete:
- `data/market_cache.sqlite3`

This forces a clean AO Data fetch on next Market refresh.

## Step 5: Cleanup presets (optional)
If setup presets are broken or incompatible, remove:
- Windows: `%USERPROFILE%\.albion_dps\market_presets.json`
- Linux/macOS: `~/.albion_dps/market_presets.json`
