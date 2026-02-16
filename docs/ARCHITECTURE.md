# Architecture (high level)

Goal: a stable, passive DPS/HPS meter for Albion Online (Qt GUI, live + PCAP replay), without any client modification.

## Data flow

`RawPacket` -> `PhotonMessage` -> `CombatEvent` -> `SessionMeter` -> `MeterSnapshot` -> Qt UI

- Capture (live/replay) produces `RawPacket` (timestamp + UDP payload + src/dst metadata).
- Protocol decoder parses Photon messages.
- Mapper translates Photon messages into combat-domain events (damage/heal ticks).
- Domain registries enrich/guard the stream:
  - `NameRegistry`: best-effort `entity_id -> name` mapping.
  - `PartyRegistry`: "self + party only" filter and self/party inference; late IDs can be accepted once names resolve.
  - `FameTracker`: fame counters (optional UI stat).
- Item resolver enriches UI:
  - `ItemResolver`: maps equipment item IDs -> weapon subcategory for per-weapon colors.
- Meter aggregates events and yields snapshots + session history:
  - `SessionMeter` owns session boundaries (`battle`/`zone`/`manual`) and history.
  - `RollingMeter` owns totals + rolling DPS/HPS window.
- Map resolver enriches zone labels:
  - `MapResolver`: maps map indices to localized names (from `map_index.json`).

## Qt UI (PySide6/QML)
- Implemented in main: Qt runner bridges snapshots to QAbstractListModel models.
- QML renders scoreboard, history cards, key legend, and fame stats.
- Shared design tokens are centralized in `albion_dps/qt/ui/Theme.qml`.
- Shared tab styling primitive is centralized in `albion_dps/qt/ui/ShellTabButton.qml`.
- Shared panel/table primitives are centralized in `albion_dps/qt/ui/CardPanel.qml` and `albion_dps/qt/ui/TableSurface.qml`.
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

## Module boundaries (intended)
- Capture does not know parsing/UI.
- Protocol parser does not know UI.
- UI does not do parsing; it renders snapshots + history.

## Safety / privacy constraint
The meter must never attribute damage/heal to unrelated nearby players:
- only "self" and party members are allowed to enter aggregation.
- if self/party is not resolved yet, the strict filter can keep results empty until it is.

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
- Map resolver: `albion_dps/domain/map_resolver.py`
- Qt runner: `albion_dps/qt/runner.py`
- Qt models: `albion_dps/qt/models.py`
- Qt QML UI: `albion_dps/qt/ui/Main.qml`
