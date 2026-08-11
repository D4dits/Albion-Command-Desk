from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, replace
from hashlib import sha256
from typing import Callable, Deque
from uuid import uuid4

from albion_dps.meter.aggregate import RollingMeter
from albion_dps.models import CombatEvent, MeterSnapshot, PhotonMessage, RawPacket
from albion_dps.protocol.map_index import extract_map_index

ZONE_PORTS = {5056, 5058}
# Keep battle session alive a bit longer to avoid mid-fight resets when combat state
# briefly drops during target swaps, movement, or packet jitter.
COMBAT_END_GRACE_SECONDS = 5.0
COMBAT_MERGE_GAP_SECONDS = 5.0
NON_PLAYER_LABEL_PREFIXES = ("@", "MOB_", "NPC_")


@dataclass(frozen=True)
class SessionEntry:
    label: str
    damage: float
    heal: float
    dps: float
    hps: float
    source_id: int | None = None


@dataclass(frozen=True)
class SessionSummary:
    mode: str
    start_ts: float
    end_ts: float
    duration: float
    label: str | None
    entries: list[SessionEntry]
    total_damage: float
    total_heal: float
    reason: str
    totals_by_id: dict[int, dict[str, float]] = field(default_factory=dict)
    encounter_id: str = ""
    source: str = "live"
    roster_names: tuple[str, ...] = ()
    participant_names: tuple[str, ...] = ()


@dataclass
class SessionMeter:
    window_seconds: float = 10.0
    battle_timeout_seconds: float = 10.0
    history_limit: int = 10
    mode: str = "battle"
    name_lookup: Callable[[int], str | None] | None = None
    map_lookup: Callable[[str], str | None] | None = None
    roster_lookup: Callable[[], set[str]] | None = None
    history_store: object | None = None
    source: str = "live"
    source_reference: str = ""
    _history: dict[str, Deque[SessionSummary]] = field(
        default_factory=lambda: {
            "battle": deque(maxlen=10),
            "zone": deque(maxlen=10),
            "manual": deque(maxlen=10),
        }
    )
    _meter: RollingMeter = field(init=False)
    _session_start: float | None = None
    _last_event_ts: float | None = None
    _last_seen_ts: float | None = None
    _active: bool = False
    _manual_active: bool = False
    _zone_key: str | None = None
    _zone_label: str | None = None
    _zone_socket: str | None = None
    _map_index: str | None = None
    _combatants: set[int] = field(default_factory=set)
    _seen_sources: set[int] = field(default_factory=set)
    _participant_ids: set[int] = field(default_factory=set)
    _source_labels: dict[int, str] = field(default_factory=dict)
    _combat_end_ts: float | None = None
    _last_combat_event_ts: float | None = None
    _saw_combat_state: bool = False

    def __post_init__(self) -> None:
        self._meter = RollingMeter(window_seconds=self.window_seconds, session_timeout_seconds=None)
        for key, entries in self._history.items():
            if entries.maxlen != self.history_limit:
                self._history[key] = deque(entries, maxlen=self.history_limit)
        if self.history_store is not None:
            for mode in self._history:
                loaded = self.history_store.load(mode, self.history_limit)
                self._history[mode] = deque(
                    reversed(loaded), maxlen=self.history_limit
                )

    def set_mode(self, mode: str) -> None:
        if mode == self.mode:
            return
        self._end_session(self._last_seen_ts or self._last_event_ts or 0.0, "mode_change")
        self.mode = mode
        self._manual_active = False
        self._combatants.clear()
        self._combat_end_ts = None
        self._last_combat_event_ts = None
        self._saw_combat_state = False
        if self.mode == "zone" and self._zone_key is not None:
            self._start_session(self._last_seen_ts or 0.0)

    def toggle_manual(self) -> bool:
        if self.mode != "manual":
            return False
        if self._manual_active:
            self._manual_active = False
            self._end_session(self._last_seen_ts or self._last_event_ts or 0.0, "manual_stop")
            return False
        self._manual_active = True
        self._start_session(self._last_seen_ts or 0.0)
        return True

    def end_session(self) -> None:
        self._end_session(self._last_seen_ts or self._last_event_ts or 0.0, "manual_end")

    def finalize(self) -> None:
        if not self._active:
            return
        end_ts = self._last_seen_ts or self._last_event_ts or 0.0
        if self.mode == "battle":
            if self._combat_end_ts is not None:
                if self._last_event_ts is not None and self._last_event_ts > self._combat_end_ts:
                    end_ts = self._last_event_ts
                else:
                    end_ts = self._combat_end_ts
                self._end_session(end_ts, "combat_state")
                return
            if self._idle_end_ready(end_ts):
                self._end_session(self._idle_end_timestamp(), "idle")
                return
        self._end_session(end_ts, "stream_end")

    def _combat_end_ready(self, now_ts: float) -> bool:
        if self._combat_end_ts is None:
            return False
        last_activity_ts = self._last_combat_event_ts
        if last_activity_ts is None:
            return now_ts - self._combat_end_ts >= COMBAT_END_GRACE_SECONDS
        # Combat-state events can briefly drop while party damage/heal events
        # continue to stream in. Only honor the combat-state stop once both the
        # stop marker and the last observed combat activity are outside grace.
        effective_end_ts = max(self._combat_end_ts, last_activity_ts)
        return now_ts - effective_end_ts >= COMBAT_END_GRACE_SECONDS

    def _idle_end_ready(self, now_ts: float) -> bool:
        last_activity_ts = self._last_combat_event_ts
        if last_activity_ts is None:
            return False
        return now_ts - last_activity_ts >= self.battle_timeout_seconds

    def _idle_end_timestamp(self) -> float:
        if self._last_combat_event_ts is None:
            return self._last_seen_ts or self._last_event_ts or 0.0
        return self._last_combat_event_ts + self.battle_timeout_seconds

    def observe_message(self, message: PhotonMessage, packet: RawPacket | None = None) -> None:
        map_index = extract_map_index(message)
        if not map_index:
            return
        timestamp = packet.timestamp if packet is not None else (self._last_seen_ts or self._last_event_ts or 0.0)
        if self._map_index is None:
            self._map_index = map_index
            if self._zone_key is None:
                self._set_zone_key(map_index, timestamp)
            else:
                self._zone_key = map_index
                self._zone_label = self._format_zone_label()
            return
        if map_index != self._map_index:
            self._map_index = map_index
            self._set_zone_key(map_index, timestamp)

    def observe_packet(self, packet: RawPacket) -> None:
        self._last_seen_ts = packet.timestamp
        zone_socket = _infer_zone_key(packet)
        if zone_socket is not None:
            if zone_socket != self._zone_socket:
                self._zone_socket = zone_socket
                if self._map_index is None:
                    self._set_zone_key(zone_socket, packet.timestamp)
                else:
                    self._zone_label = self._format_zone_label()
            elif self._map_index is None and self._zone_key is None:
                self._set_zone_key(zone_socket, packet.timestamp)

        if (
            self.mode == "battle"
            and self._active
            and self._idle_end_ready(packet.timestamp)
        ):
            self._end_session(self._idle_end_timestamp(), "idle")

        if (
            self.mode == "battle"
            and self._active
            and self._combat_end_ts is not None
            and self._combat_end_ready(packet.timestamp)
        ):
            end_ts = self._combat_end_ts
            if self._last_event_ts is not None and self._last_event_ts > end_ts:
                end_ts = self._last_event_ts
            self._end_session(end_ts, "combat_state")

        if self._active:
            self._meter.touch(packet.timestamp)

    def _set_zone_key(self, zone_key: str, timestamp: float) -> None:
        if self._zone_key is None:
            self._zone_key = zone_key
            self._zone_label = self._format_zone_label()
            if self.mode == "zone":
                self._start_session(timestamp)
            return
        if zone_key != self._zone_key:
            previous_label = self._zone_label
            self._zone_key = zone_key
            self._zone_label = self._format_zone_label()
            if self.mode == "zone":
                if self._active:
                    self._end_session(
                        timestamp, "zone_change", label_override=previous_label
                    )
                self._start_session(timestamp)

    def _format_zone_label(self) -> str | None:
        map_label = None
        if self._map_index:
            if self.map_lookup is not None:
                map_label = self.map_lookup(self._map_index)
            if not map_label:
                map_label = self._map_index
        if map_label:
            return map_label
        return self._zone_socket

    def push(self, event: CombatEvent) -> None:
        if self.mode == "manual" and not self._manual_active:
            return
        if (
            self.mode == "battle"
            and self._active
            and self._idle_end_ready(event.timestamp)
        ):
            self._end_session(self._idle_end_timestamp(), "idle")
        # Passive regeneration/self-heal is common outside a fight. It should
        # be counted once an encounter is active, but must not create a fight by
        # itself.
        if (
            self.mode == "battle"
            and not self._active
            and event.kind == "heal"
            and event.source_id == event.target_id
        ):
            return
        if not self._active:
            self._start_session(event.timestamp)
        if self._last_event_ts is None or event.timestamp > self._last_event_ts:
            self._last_event_ts = event.timestamp
        if self._last_seen_ts is None or event.timestamp > self._last_seen_ts:
            self._last_seen_ts = event.timestamp
        if self._combat_end_ts is not None:
            if event.timestamp - self._combat_end_ts > COMBAT_END_GRACE_SECONDS:
                self._combat_end_ts = None
        self._seen_sources.add(event.source_id)
        self._participant_ids.add(event.source_id)
        self._remember_source_label(event.source_id)
        if event.kind == "damage" or (
            event.kind == "heal" and event.source_id != event.target_id
        ):
            if (
                self._last_combat_event_ts is None
                or event.timestamp > self._last_combat_event_ts
            ):
                self._last_combat_event_ts = event.timestamp
        self._meter.push(event)

    def observe_combat_state(
        self, entity_id: int, in_active: bool, in_passive: bool, timestamp: float
    ) -> None:
        if self.mode != "battle":
            return
        self._saw_combat_state = True
        if self._last_seen_ts is None or timestamp > self._last_seen_ts:
            self._last_seen_ts = timestamp
        in_combat = in_active or in_passive
        if in_combat:
            if not self._active:
                self._start_session(timestamp)
            self._combatants.add(entity_id)
            self._participant_ids.add(entity_id)
            self._combat_end_ts = None
            return
        if entity_id in self._combatants:
            self._combatants.remove(entity_id)
        if not self._combatants:
            self._combat_end_ts = timestamp

    def observe_incoming_damage(self, target_id: int, timestamp: float) -> None:
        """Use damage received by a party member as a fight boundary signal.

        The hostile source is intentionally not added to meter totals.
        """
        if self.mode != "battle":
            return
        if not self._active:
            self._start_session(timestamp)
        if self._last_seen_ts is None or timestamp > self._last_seen_ts:
            self._last_seen_ts = timestamp
        if (
            self._last_combat_event_ts is None
            or timestamp > self._last_combat_event_ts
        ):
            self._last_combat_event_ts = timestamp
        self._combatants.add(target_id)
        self._participant_ids.add(target_id)

    def snapshot(self) -> MeterSnapshot:
        if not self._active:
            return MeterSnapshot(timestamp=self._last_seen_ts or 0.0, totals={})
        now = self._last_seen_ts or self._last_event_ts
        snapshot = self._meter.snapshot(now=now)
        duration = 0.0
        if self._session_start is not None:
            duration = max(snapshot.timestamp - self._session_start, 0.0)
        return MeterSnapshot(
            timestamp=snapshot.timestamp,
            totals=_totals_with_encounter_rates(snapshot.totals, duration),
            names=snapshot.names,
            duration=duration,
        )

    def history(self, limit: int | None = None) -> list[SessionSummary]:
        entries = list(reversed(self._history.get(self.mode, deque())))
        if limit is None or limit <= 0:
            return entries
        return entries[:limit]

    def set_history_limit(self, limit: int) -> None:
        normalized = max(1, int(limit))
        if normalized == self.history_limit:
            return
        self.history_limit = normalized
        for key, entries in list(self._history.items()):
            if entries.maxlen != normalized:
                self._history[key] = deque(entries, maxlen=normalized)
            if self.history_store is not None:
                self.history_store.prune(key, normalized)

    def delete_history(self, encounter_id: str) -> bool:
        if not encounter_id:
            return False
        removed = False
        for mode, entries in list(self._history.items()):
            filtered = [item for item in entries if item.encounter_id != encounter_id]
            if len(filtered) != len(entries):
                self._history[mode] = deque(filtered, maxlen=self.history_limit)
                removed = True
        if self.history_store is not None:
            removed = self.history_store.delete(encounter_id) or removed
        return removed

    def clear_history(self, mode: str | None = None) -> int:
        modes = [mode] if mode in self._history else list(self._history)
        removed = 0
        for key in modes:
            removed += len(self._history[key])
            self._history[key].clear()
        if self.history_store is not None:
            return self.history_store.clear(mode)
        return removed

    def merge_event_into_history(self, event: CombatEvent) -> bool:
        history = self._history.get(self.mode)
        if not history:
            return False
        label = self.name_lookup(event.source_id) if self.name_lookup else None
        if not label:
            label = str(event.source_id)
        for idx in range(len(history) - 1, -1, -1):
            summary = history[idx]
            if (
                event.timestamp < (summary.start_ts - COMBAT_END_GRACE_SECONDS)
                or event.timestamp > (summary.end_ts + COMBAT_END_GRACE_SECONDS)
            ):
                continue
            if summary.totals_by_id:
                totals_by_id = _clone_totals(summary.totals_by_id)
                stats = totals_by_id.setdefault(
                    event.source_id,
                    {"damage": 0.0, "heal": 0.0, "dps": 0.0, "hps": 0.0},
                )
                if event.kind == "damage":
                    stats["damage"] = float(stats.get("damage", 0.0)) + event.amount
                else:
                    stats["heal"] = float(stats.get("heal", 0.0)) + event.amount
                entries = _build_entries_from_totals_by_id(
                    totals_by_id,
                    summary.duration,
                    self.name_lookup,
                    label_overrides={
                        int(entry.source_id): entry.label
                        for entry in summary.entries
                        if entry.source_id is not None and entry.label
                    },
                )
                total_damage = sum(entry.damage for entry in entries)
                total_heal = sum(entry.heal for entry in entries)
                history[idx] = replace(
                    summary,
                    entries=entries,
                    total_damage=total_damage,
                    total_heal=total_heal,
                    totals_by_id=totals_by_id,
                )
                if self.history_store is not None:
                    self.history_store.save(history[idx])
                return True
            grouped: dict[str, tuple[float, float]] = {
                entry.label: (entry.damage, entry.heal) for entry in summary.entries
            }
            damage, heal = grouped.get(label, (0.0, 0.0))
            if event.kind == "damage":
                damage += event.amount
            else:
                heal += event.amount
            grouped[label] = (damage, heal)
            entries = _build_entries_from_grouped(grouped, summary.duration)
            total_damage = sum(entry.damage for entry in entries)
            total_heal = sum(entry.heal for entry in entries)
            history[idx] = replace(
                summary,
                entries=entries,
                total_damage=total_damage,
                total_heal=total_heal,
            )
            if self.history_store is not None:
                self.history_store.save(history[idx])
            return True
        return False

    def refresh_history_labels(self) -> bool:
        if self.name_lookup is None:
            return False
        history = self._history.get(self.mode)
        if not history:
            return False
        changed = False
        for idx in range(len(history)):
            summary = history[idx]
            if summary.totals_by_id:
                old_labels = [entry.label for entry in summary.entries]
                entries = _build_entries_from_totals_by_id(
                    summary.totals_by_id,
                    summary.duration,
                    self.name_lookup,
                    label_overrides={
                        int(entry.source_id): entry.label
                        for entry in summary.entries
                        if entry.source_id is not None and entry.label
                    },
                )
                total_damage = sum(entry.damage for entry in entries)
                total_heal = sum(entry.heal for entry in entries)
                if [entry.label for entry in entries] != old_labels:
                    changed = True
                history[idx] = replace(
                    summary,
                    entries=entries,
                    total_damage=total_damage,
                    total_heal=total_heal,
                )
                if self.history_store is not None and changed:
                    self.history_store.save(history[idx])
                continue
            grouped: dict[str, tuple[float, float]] = {}
            changed_local = False
            for entry in summary.entries:
                label = entry.label
                if label.isdigit():
                    mapped = self.name_lookup(int(label))
                    if mapped:
                        label = mapped
                        changed_local = True
                if label in grouped:
                    changed_local = True
                damage, heal = grouped.get(label, (0.0, 0.0))
                grouped[label] = (damage + entry.damage, heal + entry.heal)
            entries = _build_entries_from_grouped(grouped, summary.duration)
            total_damage = sum(entry.damage for entry in entries)
            total_heal = sum(entry.heal for entry in entries)
            if changed_local:
                changed = True
            history[idx] = replace(
                summary,
                entries=entries,
                total_damage=total_damage,
                total_heal=total_heal,
            )
            if self.history_store is not None and changed_local:
                self.history_store.save(history[idx])
        return changed

    def _remember_source_label(self, source_id: int) -> None:
        if self.name_lookup is None:
            return
        label = self.name_lookup(source_id)
        if not label:
            return
        previous = self._source_labels.get(source_id)
        if previous and not _is_non_player_label(previous):
            return
        if previous and _is_non_player_label(label):
            return
        self._source_labels[source_id] = label

    def manual_active(self) -> bool:
        return self._manual_active

    def zone_label(self) -> str | None:
        return self._zone_label

    def _start_session(self, timestamp: float) -> None:
        self._meter = RollingMeter(window_seconds=self.window_seconds, session_timeout_seconds=None)
        self._session_start = timestamp
        self._last_event_ts = None
        self._active = True
        self._combat_end_ts = None
        self._last_combat_event_ts = None
        self._seen_sources.clear()
        self._participant_ids.clear()
        self._source_labels.clear()

    def _end_session(
        self,
        timestamp: float,
        reason: str,
        *,
        label_override: str | None = None,
    ) -> None:
        if not self._active:
            return
        start_ts = self._session_start if self._session_start is not None else timestamp
        end_ts = timestamp
        duration = max(end_ts - start_ts, 0.0)
        snapshot = self._meter.snapshot(now=end_ts)
        entries = _build_entries(
            snapshot,
            duration,
            self.name_lookup,
            label_overrides=dict(self._source_labels),
        )
        totals_by_id = _clone_totals(snapshot.totals)
        if not entries:
            self._meter = RollingMeter(window_seconds=self.window_seconds, session_timeout_seconds=None)
            self._session_start = None
            self._last_event_ts = None
            self._active = False
            return
        total_damage = sum(entry.damage for entry in entries)
        total_heal = sum(entry.heal for entry in entries)
        summary = SessionSummary(
            mode=self.mode,
            start_ts=start_ts,
            end_ts=end_ts,
            duration=duration,
            label=(label_override if label_override is not None else self._zone_label)
            if self.mode == "zone"
            else None,
            entries=entries,
            total_damage=total_damage,
            total_heal=total_heal,
            reason=reason,
            totals_by_id=totals_by_id,
            encounter_id=self._new_encounter_id(start_ts, end_ts, totals_by_id),
            source=self.source,
            roster_names=tuple(sorted(self.roster_lookup() if self.roster_lookup else set())),
            participant_names=tuple(sorted(self._participant_labels())),
        )
        history = self._history.setdefault(self.mode, deque(maxlen=self.history_limit))
        existing_index = next(
            (
                index
                for index, item in enumerate(history)
                if item.encounter_id and item.encounter_id == summary.encounter_id
            ),
            None,
        )
        if existing_index is not None:
            history[existing_index] = summary
        elif self.mode == "battle" and history:
            last = history[-1]
            gap = start_ts - last.end_ts
            if 0.0 <= gap <= COMBAT_MERGE_GAP_SECONDS:
                merged_start = last.start_ts
                merged_end = summary.end_ts
                merged_duration = max(merged_end - merged_start, 0.0)
                merged_totals_by_id = _merge_totals(last.totals_by_id, summary.totals_by_id)
                if merged_totals_by_id:
                    merged_entries = _build_entries_from_totals_by_id(
                        merged_totals_by_id,
                        merged_duration,
                        self.name_lookup,
                        label_overrides={
                            **{
                                int(entry.source_id): entry.label
                                for entry in last.entries
                                if entry.source_id is not None and entry.label
                            },
                            **{
                                int(entry.source_id): entry.label
                                for entry in summary.entries
                                if entry.source_id is not None and entry.label
                            },
                        },
                    )
                else:
                    grouped: dict[str, tuple[float, float]] = {
                        entry.label: (entry.damage, entry.heal) for entry in last.entries
                    }
                    for entry in summary.entries:
                        damage, heal = grouped.get(entry.label, (0.0, 0.0))
                        grouped[entry.label] = (damage + entry.damage, heal + entry.heal)
                    merged_entries = _build_entries_from_grouped(grouped, merged_duration)
                merged_total_damage = sum(entry.damage for entry in merged_entries)
                merged_total_heal = sum(entry.heal for entry in merged_entries)
                history[-1] = replace(
                    last,
                    end_ts=merged_end,
                    duration=merged_duration,
                    entries=merged_entries,
                    total_damage=merged_total_damage,
                    total_heal=merged_total_heal,
                    totals_by_id=merged_totals_by_id,
                    participant_names=tuple(
                        sorted(set(last.participant_names) | set(summary.participant_names))
                    ),
                )
            else:
                history.append(summary)
        else:
            history.append(summary)
        if self.history_store is not None and history:
            persisted = next(
                (
                    item
                    for item in history
                    if item.encounter_id == summary.encounter_id
                ),
                history[-1],
            )
            self.history_store.save(persisted)
            self.history_store.prune(self.mode, self.history_limit)
        self._meter = RollingMeter(window_seconds=self.window_seconds, session_timeout_seconds=None)
        self._session_start = None
        self._last_event_ts = None
        self._active = False
        self._combat_end_ts = None
        self._combatants.clear()
        self._source_labels.clear()
        self._last_combat_event_ts = None
        self._seen_sources.clear()
        self._participant_ids.clear()

    def _participant_labels(self) -> set[str]:
        labels: set[str] = set()
        for entity_id in self._participant_ids:
            label = self.name_lookup(entity_id) if self.name_lookup else None
            if label and not _is_non_player_label(label):
                labels.add(label)
        return labels

    def _new_encounter_id(
        self,
        start_ts: float,
        end_ts: float,
        totals_by_id: dict[int, dict[str, float]],
    ) -> str:
        if self.source == "replay":
            fingerprint = repr(
                (
                    self.source_reference,
                    self.mode,
                    round(start_ts, 6),
                    round(end_ts, 6),
                    sorted(
                        (entity_id, stats.get("damage", 0.0), stats.get("heal", 0.0))
                        for entity_id, stats in totals_by_id.items()
                    ),
                )
            )
            return sha256(fingerprint.encode("utf-8")).hexdigest()[:32]
        return uuid4().hex


def _build_entries(
    snapshot: MeterSnapshot,
    duration: float,
    name_lookup: Callable[[int], str | None] | None,
    *,
    label_overrides: dict[int, str] | None = None,
) -> list[SessionEntry]:
    return _build_entries_from_totals_by_id(
        snapshot.totals,
        duration,
        name_lookup,
        label_overrides=label_overrides,
    )


def _totals_with_encounter_rates(
    totals: dict[int, dict[str, float]], duration: float
) -> dict[int, dict[str, float]]:
    result: dict[int, dict[str, float]] = {}
    for source_id, stats in totals.items():
        damage = float(stats.get("damage", 0.0))
        heal = float(stats.get("heal", 0.0))
        result[source_id] = {
            "damage": damage,
            "heal": heal,
            "dps": damage / duration if duration > 0 else 0.0,
            "hps": heal / duration if duration > 0 else 0.0,
        }
    return result


def _build_entries_from_grouped(
    grouped: dict[str, tuple[float, float]], duration: float
) -> list[SessionEntry]:
    entries: list[SessionEntry] = []
    for label, (damage, heal) in grouped.items():
        if duration > 0:
            dps = damage / duration
            hps = heal / duration
        else:
            dps = 0.0
            hps = 0.0
        entries.append(
            SessionEntry(
                label=label,
                damage=damage,
                heal=heal,
                dps=dps,
                hps=hps,
                source_id=None,
            )
        )
    entries.sort(key=lambda item: item.damage, reverse=True)
    return entries


def _build_entries_from_totals_by_id(
    totals: dict[int, dict[str, float]],
    duration: float,
    name_lookup: Callable[[int], str | None] | None,
    *,
    label_overrides: dict[int, str] | None = None,
) -> list[SessionEntry]:
    grouped: dict[str, dict[str, float | int | None]] = {}
    for source_id, stats in totals.items():
        damage = float(stats.get("damage", 0.0))
        heal = float(stats.get("heal", 0.0))
        label = (label_overrides or {}).get(source_id)
        if not label and name_lookup:
            label = name_lookup(source_id)
        if not label:
            label = str(source_id)
        existing = grouped.get(label)
        if existing is None:
            grouped[label] = {
                "damage": damage,
                "heal": heal,
                "source_id": source_id,
            }
            continue
        existing["damage"] = float(existing["damage"]) + damage
        existing["heal"] = float(existing["heal"]) + heal
        # If multiple entity IDs resolve to one label (map/cluster swaps),
        # keep grouped row label-only to avoid misleading single source_id.
        if existing.get("source_id") != source_id:
            existing["source_id"] = None

    entries: list[SessionEntry] = []
    for label, aggregated in grouped.items():
        total_damage = float(aggregated["damage"])
        total_heal = float(aggregated["heal"])
        if duration > 0:
            dps = total_damage / duration
            hps = total_heal / duration
        else:
            dps = 0.0
            hps = 0.0
        source_id_value = aggregated.get("source_id")
        entries.append(
            SessionEntry(
                label=label,
                damage=total_damage,
                heal=total_heal,
                dps=dps,
                hps=hps,
                source_id=source_id_value if isinstance(source_id_value, int) else None,
            )
        )
    entries.sort(key=lambda item: item.damage, reverse=True)
    return entries


def _is_non_player_label(label: str) -> bool:
    return label.startswith(NON_PLAYER_LABEL_PREFIXES)


def _clone_totals(totals: dict[int, dict[str, float]]) -> dict[int, dict[str, float]]:
    cloned: dict[int, dict[str, float]] = {}
    for source_id, stats in totals.items():
        cloned[source_id] = {
            "damage": float(stats.get("damage", 0.0)),
            "heal": float(stats.get("heal", 0.0)),
            "dps": float(stats.get("dps", 0.0)),
            "hps": float(stats.get("hps", 0.0)),
        }
    return cloned


def _merge_totals(
    left: dict[int, dict[str, float]],
    right: dict[int, dict[str, float]],
) -> dict[int, dict[str, float]]:
    if not left and not right:
        return {}
    merged = _clone_totals(left)
    for source_id, stats in right.items():
        existing = merged.setdefault(
            source_id,
            {"damage": 0.0, "heal": 0.0, "dps": 0.0, "hps": 0.0},
        )
        existing["damage"] = float(existing.get("damage", 0.0)) + float(stats.get("damage", 0.0))
        existing["heal"] = float(existing.get("heal", 0.0)) + float(stats.get("heal", 0.0))
        existing["dps"] = 0.0
        existing["hps"] = 0.0
    return merged


def _infer_zone_key(packet: RawPacket) -> str | None:
    if packet.src_port in ZONE_PORTS:
        return f"{packet.src_ip}:{packet.src_port}"
    if packet.dst_port in ZONE_PORTS:
        return f"{packet.dst_ip}:{packet.dst_port}"
    return None
