# Market Troubleshooting

## No live prices / fallback prices only
Symptoms:
- Status line says fallback is used.
- Many rows have `0` price.

Checks:
1. Scanner must run and see market traffic in Albion.
2. Verify internet access to AO Data endpoint for your region.
3. In Market tab click `Refresh prices`.
4. If still stale, remove cache and fetch again:
   - delete `data/market_cache.sqlite3`

## `ADP age` shows `--` / `n/a`
This means AO Data has no valid timestamp for selected mode/item/city.
Typical cause:
- price is `0` (no order on market)
- API row has zero date (`0001-01-01...`)

## Some items show technical ids (example `_LEVEL1`)
The state layer tries to humanize ids, but some rare items can still appear as ids.
If this appears frequently after dataset refresh, regenerate recipes from local game files.

## Inputs/Outputs are empty
Most common reasons:
1. No craft rows selected in Setup.
2. Invalid setup values (city/fees/runs).
3. Recipe row exists but has no valid component/output after bad dataset conversion.

Run:
- `python -m pytest -q tests/test_market_dataset_regression.py tests/test_market_catalog.py`

## Profit looks wrong
Checklist:
1. Confirm `premium` state is correct.
2. Confirm market tax assumptions:
   - transaction tax (4% premium / 8% non-premium)
   - setup fee (2.5%)
3. Confirm station fee is configured as the game building fee.
4. Confirm per-row craft city and daily bonus values.
5. Check manual overrides in Inputs/Outputs (manual values override AO Data).

## QML loads but Market tabs do not refresh
1. Open diagnostics panel in Market and check recent lines.
2. Clear diagnostics and trigger `Refresh prices`.
3. Run Qt smoke + market state tests:
   - `python -m pytest -q tests/test_qt_smoke.py tests/test_market_qt_state.py`

## Reset Market local state
1. Close the app.
2. Remove:
   - `data/market_cache.sqlite3`
   - `%USERPROFILE%\\.albion_dps\\market_presets.json` (Windows)
   - `~/.albion_dps/market_presets.json` (Linux/macOS)
3. Start app again and load Market tab.
