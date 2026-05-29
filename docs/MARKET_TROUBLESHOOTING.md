# Market Troubleshooting

## No live prices / fallback prices only
Symptoms:
- Status line says fallback is used.
- Many rows have `0` price.
- Status line may show `cooldown` after AO Data returns `429 Too Many Requests`.

Checks:
1. Scanner must run and see market traffic in Albion.
2. Verify internet access to AO Data endpoint for your region.
3. In Market tab click `Refresh prices`.
4. If AO Data reports `429`, wait for the displayed cooldown before refreshing again. The app keeps cache/fallback prices visible while live prices are rate-limited.
5. If still stale, remove cache and fetch again:
   - delete `data/market_cache.sqlite3`

## App closes while fetching Market prices
The Market refresh path should not close the app during live AO Data fetches. If it still happens:
1. Start the app from a terminal so Python/Qt output remains visible.
2. Reproduce the refresh.
3. Capture the terminal output and Market diagnostics.
4. Run:
   - `python -m pytest -q tests/test_market_qt_state.py tests/test_market_aod_client.py tests/test_market_service.py`

## `ADP age` shows `--` / `n/a`
This means AO Data has no valid timestamp for selected mode/item/city.
Typical cause:
- price is `0` (no order on market)
- API row has zero date (`0001-01-01...`)

When live AO Data returns a valid price, the Market tab stores that row with the application's fetch time. After a successful `Refresh prices`, valid rows should therefore move back to a fresh age instead of staying red because the upstream order timestamp was old.

For enchanted refined materials such as `Metal Bar T6.2` or `Planks T6.2`, AO Data can expose the real market row under an alias:
- recipe/component id: `T6_METALBAR_LEVEL2`
- live AO Data price id: `T6_METALBAR_LEVEL2@2`

Current builds request both forms. If `ADP age` still shows `n/a` after scanning the item in the correct city:
1. Confirm the Market region and city match the scanner traffic, for example `europe` + `Martlock`.
2. Click `Refresh prices`.
3. Open `Show diagnostics` and confirm the request includes `*_LEVEL2@2` for T6.2 materials.
4. Delete `data/market_cache.sqlite3` and refresh again if stale zero rows were cached.
5. If the API still returns zero rows for every alias, scan the exact market item again and wait for AO Data ingestion.

## Some items show technical ids (example `_LEVEL1`)
The state layer tries to humanize ids, but some rare items can still appear as ids.
If this appears frequently after dataset refresh, regenerate recipes from local game files.

## Crystallized craft badge is missing
Crystallized variants are separate recipe rows generated from the local recipe catalog.

Checks:
1. Search in Market using the final item family, not only the base artifact component.
2. Confirm the recipe row has a `#CRYSTALLIZED` variant in the catalog:
   - `python -m pytest -q tests/test_market_catalog.py -k crystallized`
3. If no crystallized variants exist after a game patch, regenerate local game data and recipe dataset.
4. Remember that crystallized inputs are non-returnable. They should appear as one-time components and should not be reduced by RRR.

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
6. Check whether the craft row is marked as missing ADP prices. Missing fresh component prices are not ranked as profitable candidates.

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
