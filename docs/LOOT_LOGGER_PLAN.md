# Loot Logger Status and Plan

## Current Status

The native loot logger is implemented as a first-class module inside Albion Command Desk. It does not reuse external AO Loot Logger code; earlier external projects were used only as protocol research references.

Implemented:
- `LootTracker` observes decoded Photon messages from live capture and PCAP replay.
- Party/self filtering is enforced through `PartyRegistry` when available.
- Item pickups are recorded as `LootEvent` rows with looter, item, quantity, source name, and source kind.
- Current loot pickup variants are covered, including party-member grabbed-loot events and inventory move flows seen in newer captures.
- `LootLogWriter` writes session text logs under `artifacts/loot/`.
- Import/export supports the stable text format and preserves `source_kind` for newer logs.
- Qt `Loot` tab shows feed rows, source badges, category filters, imported/live mode state, top looters, top items, and player-corpse summaries.
- Silver is intentionally not part of the live UI focus; the feature is item-first.

## Product Rules

- Only party/self looters should be tracked when party information is known.
- Do not scan or present unrelated nearby players.
- Player corpse loot should be visually distinct from mob/container/system loot.
- Imported old logs remain readable, but they cannot recover party events that were not written into the file originally.
- If a PCAP contains complete party traffic but the log was generated before a parser fix, regenerate/replay the log with the current code.

## Runtime Flow

`RawPacket` -> `PhotonMessage` -> `PartyRegistry` / `NameRegistry` -> `LootTracker` -> `LootLogWriter` -> `LootState` -> `LootTab.qml`

Core files:
- `albion_dps/domain/loot_types.py`
- `albion_dps/domain/loot_tracker.py`
- `albion_dps/domain/loot_log_writer.py`
- `albion_dps/domain/loot_export.py`
- `albion_dps/domain/loot_import.py`
- `albion_dps/qt/loot_state.py`
- `albion_dps/qt/ui/LootTab.qml`
- `albion_dps/qt/ui/LootSummaryPanel.qml`

## Data Model

### `LootPlayer`

- `player_name`
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
- `source_name`
- `source_kind`
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
- `slot_items`

## Source Kinds

- `player`: item came from a player corpse. In UI this is the high-attention red path.
- `mob`: source looks like a mob/container owner from protocol context.
- `system`: source was produced by system/container/inventory operation flow, for example loot chest imports.
- `unknown`: item and looter were known, but source context was incomplete.
- `silver`: retained in domain/import compatibility, but not shown as the primary live feature.

## Export Format

The text export header is:

```text
timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name;item_id;item_name;quantity;looted_from__alliance;looted_from__guild;looted_from__name;source_kind
```

Notes:
- `source_kind` is required for new logs.
- Old logs without `source_kind` are accepted and inferred best-effort.
- Imported old logs cannot contain party events that were never exported.

## UI Behavior

Loot tab supports:
- live log path display,
- imported log mode with `Back to Live`,
- `Import Log`,
- `Copy Summary`,
- `Copy View`,
- `Export View`,
- `Open Folder`,
- category chips for all items/weapons/armor/bags/capes/mounts/consumables/resources/artifacts/other,
- search across looter, guild/alliance, item, source, and summary,
- looter and source-kind filters,
- right-side summary panels.

Current UI color rules:
- red row/badge: player corpse source,
- yellow row/badge: mob/container/system source,
- neutral row: unknown or normal source.

## Validation

Primary tests:
- `tests/test_loot_tracker.py`
- `tests/test_loot_tracker_pcaps.py`
- `tests/test_loot_export.py`
- `tests/test_loot_import.py`
- `tests/test_loot_log_writer.py`
- `tests/test_qt_loot_state.py`
- `tests/test_qml_loot_tab.py`

Useful targeted command:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_loot_tracker.py tests/test_loot_tracker_pcaps.py tests/test_loot_export.py tests/test_loot_import.py tests/test_loot_log_writer.py tests/test_qt_loot_state.py tests/test_qml_loot_tab.py
```

## Known Limitations

- Loot visibility depends on packet context. If capture starts after party/roster context or source/container setup packets were missed, some rows can be incomplete or absent.
- Party members are only visible if the packet stream contains their loot event and the party registry can identify them safely.
- Old text logs are not raw captures. They cannot be re-parsed for events that were not exported.
- Item names depend on local game data. Unknown/stale IDs fall back to technical Albion IDs.
- Albion protocol updates can change subtype/parameter layout. In that case, update parser assumptions and add a regression PCAP before UI work.

## Remaining Work

1. Add a current Loot tab screenshot to `website/assets/` and update the gallery.
2. Add a small in-app explanation panel for color/source meanings.
3. Add optional JSONL export if external tooling needs lossless machine-readable logs.
4. Add value estimates only after item identity and market price mapping are stable enough for loot use.
5. Keep adding PCAP regression fixtures for party loot scenarios after major Albion patches.
