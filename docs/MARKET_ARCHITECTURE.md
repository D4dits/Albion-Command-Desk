# Market Architecture

## Scope
The Market module is a crafting/refining profitability workspace inside the Qt app.
It is isolated from DPS parsing/aggregation logic.

## Runtime components
- `albion_dps/qt/market/state.py`
  - Owns UI state for Setup/Inputs/Outputs/Results.
  - Validates setup changes and triggers recalculation.
  - Builds table models consumed by QML.
- `albion_dps/market/service.py`
  - Facade for market data access.
  - Uses AO Data client and local SQLite cache.
- `albion_dps/market/aod_client.py`
  - Calls AO Data endpoints (`stats/prices`, `stats/charts`).
  - Handles request batching, partial price results, rate-limit handling, and request telemetry.
- `albion_dps/market/cache.py`
  - TTL cache (`data/market_cache.sqlite3`) with stale-read support.
- `albion_dps/market/catalog.py`
  - Loads recipe catalog (`albion_dps/market/data/recipes.json`).
  - Validates integrity and normalizes component metadata.
  - Builds crystallized recipe variants from supported artifact/final-item craft paths.
- `albion_dps/market/engine.py`
  - Pricing and profit engine.
  - Computes input costs, output revenue, taxes/fees, return rate, and breakdown.

## Data flow
1. User changes setup or selected crafts in QML.
2. `MarketSetupState` computes required recipe item ids/cities, expands safe AO Data query aliases, and refreshes price index.
3. `MarketDataService` resolves data path:
   - cache hit -> `cache` or `stale_cache`
   - partial cache hit -> `partial_cache` or `partial_stale_cache`
   - no usable cache -> live AO Data fetch -> cache write
   - fetch failure/no rows -> fallback synthetic price index
4. In Qt runtime, live price fetches run in a Python worker thread. The worker returns through a queue polled by a GUI `QTimer`, so Qt objects are updated only on the GUI thread.
5. `engine` calculates:
   - input lines (need, stock, buy qty, unit, total)
   - output lines (gross, fee, tax, net)
   - summary KPI and breakdown
6. Qt list models are rebuilt and rendered in Market sub-tabs.

## Price resolution rules
- Inputs default mode: `buy_order`.
- Outputs default mode: `sell_order`.
- If manual value is set for an item, manual value is used.
- Item id aliases are handled both during AO Data requests and when matching returned/cache rows:
  - `@N` enchant ids
  - `_LEVELN` material ids
  - `_LEVELN@N` enchanted refined material ids
  - quality fallback to `quality=1` when needed
- Live AO Data requests include the alias variants required to get real AO Data rows for enchanted refined materials. This fixes cases where the recipe component is `T6_METALBAR_LEVEL2`, but AO Data exposes the current market row as `T6_METALBAR_LEVEL2@2`.
- Alias matching does not fall back from enchanted materials to plain tier materials. `T6_METALBAR_LEVEL2` must not use `T6_METALBAR` as a silent substitute.

## Freshness and ranking rules
- `price_age_text` uses the timestamp for the selected mode:
  - input `sell_order` rows use `sell_price_min_date`,
  - input `buy_order` rows use `buy_price_max_date`,
  - average/other modes use the newest valid buy/sell timestamp.
- AO Data zero dates such as `0001-01-01T00:00:00` are treated as missing and render as `n/a`.
- Craft rows missing fresh component prices are not ranked as profitable candidates.
- The `Hide missing ADP prices` option filters affected rows from setup/inputs/outputs/results preview tables.

## AO Data refresh behavior
- Cache and stale cache can be shown immediately while live refresh continues in the background.
- Partial cache hits are accepted when they cover the currently requested item/location/quality rows.
- Price requests are split into URL-safe batches and can return partial results when one batch fails.
- `429 Too Many Requests` is treated as a cooldown signal for price fetches and does not perform long retry/backoff loops in the GUI workflow.
- Large craft-plan changes batch/defer preview rebuilds so adding recipe families does not recalculate after every row.

## Return-rate model
- Return rate is derived from production bonus profile (location/city rules), focus toggle, and daily bonus.
- Artifact/relic/rune/soul-like recipe components are treated as non-returnable.
- Crystallized components are treated as non-returnable one-time inputs and are not reduced by RRR.

## Crystallized variants
- Recipes that can be crafted through crystallized components are exposed as separate variants with a `#CRYSTALLIZED` recipe id suffix.
- UI rows expose `uses_crystallized` so Market search/setup can show a dedicated badge.
- The variant keeps the final craft visible in Market, but the required crystallized input is modeled as a non-returnable component.
- Family-selection logic keeps normal and crystallized variants discoverable together so users can compare the standard and crystallized paths.
- Dataset tests assert that the default catalog contains crystallized variants and that final-item variants keep their expected component structure.

## Persistence
- Setup presets: `~/.albion_dps/market_presets.json`.
- Market cache: `data/market_cache.sqlite3`.

## Testing layers
- Unit/snapshot tests: engine and pricing invariants.
- Integration tests: AO Data client + cache behavior.
- Dataset regression tests: recipe catalog integrity and expected baseline shape.
- Qt state tests: setup interactions, aliasing, enchanted refined material queries, diagnostics, stock handling.
- Crystallized tests: catalog variant generation, setup/search exposure, and non-returnable component handling.
