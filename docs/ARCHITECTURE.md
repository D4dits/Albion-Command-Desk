# Architecture (high level)

Goal: a stable, passive DPS/HPS meter for Albion Online (CLI, live + PCAP replay), without any client modification.

## Data flow

`RawPacket` → `PhotonMessage` → `CombatEvent` → `SessionMeter` → `MeterSnapshot` → CLI/TUI

- Capture (live/replay) produces `RawPacket` (timestamp + UDP payload + src/dst metadata).
- Protocol decoder parses Photon messages.
- Mapper translates Photon messages into combat-domain events (damage/heal ticks).
- Domain registries enrich/guard the stream:
  - `NameRegistry`: best-effort `entity_id -> name` mapping.
  - `PartyRegistry`: “self + party only” filter and self/party inference.
  - `FameTracker`: fame counters (optional UI stat).
- Meter aggregates events and yields snapshots + session history:
  - `SessionMeter` owns session boundaries (`battle`/`zone`/`manual`) and history.
  - `RollingMeter` owns totals + rolling DPS/HPS window.

## Module boundaries (intended)
- Capture does not know parsing/UI.
- Protocol parser does not know UI.
- UI does not do parsing; it renders snapshots + history.

## Safety / privacy constraint
The meter must never attribute damage/heal to unrelated nearby players:
- only “self” and party members are allowed to enter aggregation.
- if self/party is not resolved yet, the strict filter can keep results empty until it is.

## Useful entry points
- CLI: `albion_dps/cli.py`
- Pipeline: `albion_dps/pipeline.py`
- Session + history: `albion_dps/meter/session_meter.py`
- Aggregation window: `albion_dps/meter/aggregate.py`
- Party/self filtering: `albion_dps/domain/party_registry.py`

