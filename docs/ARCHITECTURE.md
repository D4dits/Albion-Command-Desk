# Architecture (high level)

Goal: a stable, passive Albion Online desktop companion (Qt GUI, live + PCAP replay), without any client modification.

## Data flow

`RawPacket` -> `PhotonMessage` -> `CombatEvent` -> `SessionMeter` -> `MeterSnapshot` -> Qt UI

Loot uses the same passive capture path:

`RawPacket` -> `PhotonMessage` -> `LootTracker` -> `LootEvent` -> `LootState` -> Qt UI / TXT export

- Capture (live/replay) produces `RawPacket` (timestamp + UDP payload + src/dst metadata).
- Protocol decoder parses Photon messages.
- Mapper translates Photon messages into combat-domain events (damage/heal ticks).
- Domain registries enrich/guard the stream:
  - `NameRegistry`: best-effort `entity_id -> name` mapping.
  - `PartyRegistry`: "self + party only" filter and self/party inference; late IDs can be accepted once names resolve.
  - `FameTracker`: fame counters (optional UI stat).
- Item resolver enriches UI:
  - `ItemResolver`: maps equipment item IDs -> weapon subcategory for per-weapon colors.
  - Loot and Market reuse item IDs/names where available; unknown/stale game data falls back to technical IDs.
- Meter aggregates events and yields snapshots + session history:
  - `SessionMeter` owns session boundaries (`battle`/`zone`/`manual`) and history.
  - `RollingMeter` owns totals + rolling DPS/HPS window.
- Loot aggregates item pickup events:
  - `LootTracker` owns protocol/container state and emits `LootEvent` records.
  - `LootLogWriter` persists the live session text log.
  - `LootState` filters, imports, exports, and exposes QML models for feed and summary panels.
- Map resolver enriches zone labels:
  - `MapResolver`: maps map indices to localized names (from `map_index.json`).

## Qt UI (PySide6/QML)
- Implemented in main: Qt runner bridges snapshots to QAbstractListModel models.
- QML renders scoreboard, history cards, key legend, and fame stats.
- Shared design tokens are centralized in `albion_dps/qt/ui/Theme.qml`.
- Shared tab styling primitive is centralized in `albion_dps/qt/ui/ShellTabButton.qml`.
- Shared panel/table primitives are centralized in `albion_dps/qt/ui/CardPanel.qml` and `albion_dps/qt/ui/TableSurface.qml`.
- Shared panel/table primitives use level-based surface hierarchy to reduce per-view style duplication.
- Shell/layout breakpoints are centralized in `Theme.qml` and consumed by `Main.qml` for compact/narrow responsive behavior.
- Phase PH2-UXR visual direction (active):
  - dark neutral base surfaces (`surface*`) with cool blue action accents (`brandPrimary*`)
  - warm support/highlight accent (`brandWarmAccent`) reserved for premium/support cues
  - semantic state layers include both foreground and background tokens (`state*` + `state*Bg`)
  - control/button/table families have dedicated state tokens to prevent ad-hoc color literals
  - spacing/radius/elevation scales are tokenized to keep component rhythm consistent during visual modernization
- Phase 0 shell contract (frozen):
  - `shellHeader` in `Main.qml` has two fixed zones:
    - `shellLeftZone`: app title + contextual status summary.
    - `shellRightZone`: `shellMeterZone` -> `shellUpdateBanner` -> `shellUpdateZone` -> `shellSupportZone`.
  - Global navigation remains centered directly under header in a width-clamped nav zone.
- Planned extraction map for Phase 1:
  - `shellHeader` fragment
  - `shellUpdateZone` fragment
  - `shellSupportZone` fragment
- Header runtime helpers:
  - update checks (manifest-based, non-blocking),
  - persisted update preference (`Auto update`),
  - manual check trigger (`Check now`).
- Runtime startup profiles:
  - `core`: starts GUI without live capture backend (market/scanner/replay workflows available).
  - `live`: starts GUI with packet capture backend.

## Install and update delivery
- Bootstrap installers:
  - Windows: `tools/install/windows/install.ps1`
  - Linux: `tools/install/linux/install.sh`
  - macOS: `tools/install/macos/install.sh`
- Shared post-install smoke checks:
  - `tools/install/common/smoke_check.py`
- Release metadata contract and publication:
  - Spec: `docs/release/RELEASE_MANIFEST_SPEC.md`
  - Builder: `tools/release/manifest/build_manifest.py`
  - CI workflow: `.github/workflows/release-manifest.yml`
- Clean-machine bootstrap validation:
  - CI workflow: `.github/workflows/bootstrap-smoke.yml`

## Market profit math
- Planner inputs are split into:
  - raw materials / components input cost,
  - journal empty input cost,
  - output-side station fee,
  - output-side market tax.
- Session/top-level market KPIs use:
  - `net_profit = output_value - input_cost - station_fee - market_tax`
  - `margin_percent = net_profit / input_cost * 100`
- Result rows use the same logic on a per-row allocated basis:
  - `allocated_cost` is the row's proportional share of input cost,
  - `net_value` is already post-fee/post-tax,
  - `row_profit = net_value - allocated_cost`
  - `row_margin = row_profit / allocated_cost * 100`
- This keeps row math aligned with top-level KPIs while still showing fee/tax as separate columns.

## Crystallized recipe handling
- The recipe catalog builds crystallized variants from local recipe data where a crystallized component can replace an artifact/final-item craft path.
- Crystallized variants are marked with `uses_crystallized=True` and receive a UI badge in Market search/setup rows.
- Crystallized inputs are non-returnable. They are included one-to-one in upfront shopping requirements and are not reduced by RRR.
- Normal returnable materials still use the existing upfront/economic quantity split.

## Loot logger behavior
- Loot tracking is party-scoped: if a `PartyRegistry` is available, the tracker accepts only known self/party looters.
- Current item-focused UI excludes silver from live summaries; the domain tracker can still include silver when explicitly configured for tests or future views.
- Supported source classes:
  - `player`: player corpse, rendered as high-attention red in the Loot UI.
  - `mob`: mob/container-like source.
  - `system`: inventory/container/system operation flow, for example loot chest imports.
  - `unknown`: event had an item/looter but insufficient source context.
- Export/import format includes `source_kind` so newer logs preserve source classification. Older logs without that column are still accepted with best-effort inference.
- Protocol assumptions are locked with unit tests plus local PCAP replay tests. If Albion changes loot packet shapes again, update `LootTracker` first, then refresh the replay fixture expectations.

## Module boundaries (intended)
- Capture does not know parsing/UI.
- Protocol parser does not know UI.
- UI does not do parsing; it renders snapshots + history.

## Safety / privacy constraint
The app must not attribute combat or loot to unrelated nearby players:
- Meter aggregation allows only self and party members once party context is known.
- Loot logging accepts only party/self looters when party state is available.
- If self/party is not resolved yet, strict filters can keep results empty until safe context exists.

## Useful entry points
- Desktop launcher (Qt GUI): `albion_dps/cli.py`
- Profile commands:
  - `albion-command-desk core`
  - `albion-command-desk live`
  - `albion-command-desk replay <pcap>`
- Pipeline: `albion_dps/pipeline.py`
- Session + history: `albion_dps/meter/session_meter.py`
- Aggregation window: `albion_dps/meter/aggregate.py`
- Party/self filtering: `albion_dps/domain/party_registry.py`
- Item resolver + weapon colors: `albion_dps/domain/item_resolver.py`, `albion_dps/domain/weapon_colors.py`
- Loot domain: `albion_dps/domain/loot_tracker.py`, `albion_dps/domain/loot_types.py`, `albion_dps/domain/loot_log_writer.py`
- Loot UI state: `albion_dps/qt/loot_state.py`
- Map resolver: `albion_dps/domain/map_resolver.py`
- Market recipe catalog: `albion_dps/market/catalog.py`
- Market Qt state: `albion_dps/qt/market/state.py`
- Qt runner: `albion_dps/qt/runner.py`
- Qt models: `albion_dps/qt/models.py`
- Qt QML UI: `albion_dps/qt/ui/Main.qml`
