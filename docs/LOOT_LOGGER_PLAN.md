# Loot Logger Plan

## Goal

Add a native loot logger to Albion Command Desk that tracks items looted by players, can filter to party members, exports a compatible text format for external viewers when needed, and later exposes a dedicated UI tab.

We will not reuse the external AO Loot Logger code. We only use it as protocol/reference research.

## Product Scope

### MVP

- Detect loot pickup events from Albion Photon traffic.
- Resolve:
  - who looted
  - what item was looted
  - quantity
  - who it was looted from
- Persist/export loot logs in a viewer-compatible text format.
- Support replay validation from local `.pcap` files.

### V2

- Dedicated `Loot` tab in Qt UI.
- `Party only` filter.
- Aggregations:
  - by looter
  - by victim/source
  - by item
  - by estimated value
- CSV and JSON export.

## Technical Approach

The feature should be built as a new domain observer connected to the existing Photon pipeline.

Core existing building blocks already available:

- raw packet capture and replay
- Photon framing decode
- Protocol16 parameter decode
- `NameRegistry`
- `PartyRegistry`
- local item databases from extracted game files

This means loot logging should be implemented as a first-class module inside the current architecture, not as a parallel tool.

## Proposed Modules

### Domain

- `albion_dps/domain/loot_types.py`
- `albion_dps/domain/loot_tracker.py`
- optionally `albion_dps/domain/loot_export.py`

### Qt / UI

- `albion_dps/qt/loot/`
- `albion_dps/qt/ui/LootTab.qml`

### Tests

- `tests/test_loot_tracker.py`
- `tests/test_loot_export.py`
- `tests/test_loot_pcap*.py`
- later `tests/test_qml_loot_tab.py`

## Data Model

### `LootPlayer`

- `name`
- `guild_name`
- `alliance_name`

### `LootItemRef`

- `item_num_id`
- `unique_name`
- `display_name`

### `LootEvent`

- `timestamp`
- `looted_by`
- `looted_from`
- `item`
- `quantity`
- `is_silver`
- `raw_event_code`
- `raw_subtype`

### `LootContainer`

- `container_id`
- `container_uuid`
- `owner_name`
- `owner_kind`
- `items`

## Implementation Stages

### Stage 0: Protocol Verification

Objective:
- confirm the live/replay protocol shape on our own captures before committing to parser contracts

Tasks:
- add a temporary debug utility that dumps Protocol16 event `code` plus parameter `252` subtype
- inspect local captures for loot-related traffic
- verify equivalents of:
  - new loot container
  - attach item container
  - detach item container
  - new simple/equipment item
  - other grabbed loot

Output:
- confirmed subtype map for current Albion build
- at least one local `.pcap` with reproducible loot pickup sequence

### Stage 1: Core Domain Tracker

Objective:
- add a native loot observer that consumes `PhotonMessage`

Tasks:
- create `LootTracker.observe(message, packet)`
- decode `EventData` using existing `Protocol16`
- maintain in-memory state for:
  - known players
  - loot objects
  - containers
- append final `LootEvent` records when pickup events are seen

Notes:
- the final pickup event is the preferred source of truth
- container/object tracking is supporting state, not the main output

### Stage 2: Item Resolution

Objective:
- map item numeric ids to stable Albion item ids and names

Tasks:
- expose a clean lookup API over local extracted databases
- reuse local `indexedItems.json` and `items.json`
- avoid remote fetch dependency
- add fallback behavior for unknown ids

Preferred outcome:
- `item_num_id -> unique_name -> display_name`

### Stage 3: Export Layer

Objective:
- write logs in a stable format

Tasks:
- implement writer for viewer-compatible text format:
  - `timestamp_utc`
  - `looted_by__alliance`
  - `looted_by__guild`
  - `looted_by__name`
  - `item_id`
  - `item_name`
  - `quantity`
  - `looted_from__alliance`
  - `looted_from__guild`
  - `looted_from__name`
- add optional native exports:
  - CSV
  - JSONL

Notes:
- compatible export should be treated as an adapter, not our internal canonical format

### Stage 4: Pipeline Integration

Objective:
- integrate loot tracking into replay and live runtime

Tasks:
- extend `stream_snapshots(...)` observer flow to notify `LootTracker`
- instantiate tracker in `qt/runner.py`
- define ownership/lifecycle:
  - reset on app restart
  - optional reset on zone change
  - optional rotate log file

Open design choice:
- keep a single rolling session log
- or rotate per run/day/session

### Stage 5: Replay Tests

Objective:
- prove correctness before live UI work

Tasks:
- create unit tests for event parsing
- create replay tests from local captures
- validate:
  - loot item identity
  - quantity
  - looter name
  - source name
  - ignored silver behavior if configured
  - missing-name fallback behavior

This stage is mandatory before UI work.

### Stage 6: Basic UI

Objective:
- expose loot data inside the application

Tasks:
- create `LootTab`
- add live table
- add filters:
  - party only
  - include silver
  - item search
- add export actions

Initial UI fields:
- time
- looted by
- item
- quantity
- looted from
- guild/alliance context

### Stage 7: Aggregations and Value Layer

Objective:
- make the tab operationally useful, not just a raw event console

Tasks:
- summary by player
- summary by item
- summary by source/victim
- estimated market value using existing market data when available

## Integration With Existing Systems

### `NameRegistry`

Should remain the main source for resolving player names and related entity context.

### `PartyRegistry`

Should be used for `party only` filtering and possibly for identifying self vs party members.

### Item Databases

Use local extracted databases already supported by the project. Do not depend on external hosted item dumps at runtime.

## Risks

### Protocol Drift

Loot event subtype/parameter layout may have changed compared to older public loot logger tools.

Mitigation:
- validate using our own captures first
- encode parser assumptions in replay tests

### Incomplete Context

Some events may arrive without full player metadata already loaded.

Mitigation:
- allow delayed/fallback player records
- keep event with partial info instead of dropping it

### Capture Constraints

Like other packet tools, this may fail with VPN/tunnel/cloud-streamed setups.

Mitigation:
- document limitations clearly
- reuse existing capture startup diagnostics

### Item Resolution Gaps

Unknown numeric ids may appear if local item databases are stale.

Mitigation:
- expose “unknown item” fallback
- rely on local extractor/update flow

## Delivery Order

1. Protocol verification on local captures
2. `LootTracker` domain model and parser
3. item id resolution layer
4. viewer-compatible export
5. replay tests
6. runtime integration
7. `Loot` tab
8. aggregations/value estimates

## Recommended Workflow

For a solo-maintained project:

- use a dedicated branch, for example `feature/loot-logger`
- commit in small vertical slices
- merge directly into `main` after local verification

Pull requests are optional here. They are useful only if you want:

- a reviewable history in GitHub
- issue/commit linkage
- easier rollback boundaries

If you are the only developer, the practical setup is:

- branch for the whole feature
- local commits after each stage
- merge fast-forward or regular merge into `main`

That gives you isolation without adding PR overhead.

## Recommended First Slice

The best first implementation slice is:

1. add `LootTracker`
2. parse final loot pickup event
3. resolve item names from local databases
4. export compatible text log
5. add one replay test based on a local loot `.pcap`

Do not start from UI.
