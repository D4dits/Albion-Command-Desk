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
  - Handles retry/backoff and request telemetry.
- `albion_dps/market/cache.py`
  - TTL cache (`data/market_cache.sqlite3`) with stale-read support.
- `albion_dps/market/catalog.py`
  - Loads recipe catalog (`albion_dps/market/data/recipes.json`).
  - Validates integrity and normalizes component metadata.
- `albion_dps/market/engine.py`
  - Pricing and profit engine.
  - Computes input costs, output revenue, taxes/fees, return rate, and breakdown.

## Data flow
1. User changes setup or selected crafts in QML.
2. `MarketSetupState` computes required item ids/cities and refreshes price index.
3. `MarketDataService` resolves data path:
   - cache hit -> `cache` or `stale_cache`
   - no usable cache -> live AO Data fetch -> cache write
   - fetch failure/no rows -> fallback synthetic price index
4. `engine` calculates:
   - input lines (need, stock, buy qty, unit, total)
   - output lines (gross, fee, tax, net)
   - summary KPI and breakdown
5. Qt list models are rebuilt and rendered in Market sub-tabs.

## Price resolution rules
- Inputs default mode: `buy_order`.
- Outputs default mode: `sell_order`.
- If manual value is set for an item, manual value is used.
- Item id aliases are handled when matching AO Data rows:
  - `@N` enchant ids
  - `_LEVELN` material ids
  - quality fallback to `quality=1` when needed

## Return-rate model
- Return rate is derived from production bonus profile (location/city rules), focus toggle, and daily bonus.
- Artifact/relic/rune/soul-like recipe components are treated as non-returnable.

## Persistence
- Setup presets: `~/.albion_dps/market_presets.json`.
- Market cache: `data/market_cache.sqlite3`.

## Testing layers
- Unit/snapshot tests: engine and pricing invariants.
- Integration tests: AO Data client + cache behavior.
- Dataset regression tests: recipe catalog integrity and expected baseline shape.
- Qt state tests: setup interactions, aliasing, diagnostics, stock handling.
