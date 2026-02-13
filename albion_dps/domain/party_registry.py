from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from collections.abc import Iterable

from albion_dps.domain.name_registry import NameRegistry
from albion_dps.models import CombatEvent, PhotonMessage, RawPacket
from albion_dps.protocol.protocol16 import (
    Protocol16Error,
    decode_event_data,
    decode_operation_request,
    decode_operation_response,
)
from albion_dps.protocol.map_index import extract_map_index_from_response

PARTY_EVENT_CODE = 1
PARTY_SUBTYPE_KEY = 252
PARTY_SUBTYPE_NAME_KEYS = {
    212: 5,
    227: 13,
    229: 6,
    214: 2,
    221: 0,
}
PARTY_SUBTYPE_ROSTER = {212, 227, 229}
PARTY_SUBTYPE_DISBAND = 213
PARTY_SUBTYPE_PLAYER_LEFT = 216
PARTY_SUBTYPE_PLAYER_JOINED = 214
PARTY_SUBTYPE_MEMBER_REMOVED = 233
SELF_SUBTYPE_NAME_KEYS = {
    228: 1,
    238: 0,
}
MATCH_ROSTER_SUBTYPE = 120
MATCH_ROSTER_NAME_KEY = 2
MATCH_ROSTER_MIN_SIZE = 5
MATCH_ROSTER_TTL_SECONDS = 120.0
PARTY_FALLBACK_SUBTYPE_MIN = 200
PARTY_FALLBACK_SUBTYPE_MAX = 260
PARTY_FALLBACK_MAX_ROSTER_SIZE = 20
PARTY_FALLBACK_SINGLE_GUID_KEYS = (1, 3, 4, 5, 12)
COMBAT_TARGET_SUBTYPE = 21
COMBAT_TARGET_A_KEY = 0
COMBAT_TARGET_B_KEY = 1
SERVER_PORTS = {5055, 5056, 5058}
ZONE_PORTS = {5056, 5058}
TARGET_REQUEST_OPCODE = 1
TARGET_REQUEST_ID_KEY = 5
TARGET_SELF_NAME_MIN_COUNT = 5
TARGET_SELF_NAME_MIN_RATIO = 2.0
TARGET_SELF_NAME_WINDOW_SECONDS = 60.0
TARGET_SELF_NAME_CONFIRM_COUNT = 20
SELF_ID_CANDIDATE_TTL_SECONDS = 15.0
SELF_ID_CORRELATION_WINDOW_SECONDS = 0.75
SELF_ID_MIN_SCORE = 1.0
SELF_ID_MIN_SCORE_GAP = 1.0
TARGET_LINK_WINDOW_SECONDS = 2.0
TARGET_LINK_REORDER_SECONDS = 0.15
OPERATION_CODE_KEY = 253
JOIN_OPERATION_CODE = 2
CHANGE_CLUSTER_OPERATION_CODE = 35
JOIN_SELF_ID_KEY = 0
JOIN_SELF_NAME_KEY = 2
NON_PLAYER_NAME_PREFIXES = ("@",)
NON_PLAYER_NAMES = {"SYSTEM"}
KNOWN_PARTY_SUBTYPES = (
    set(PARTY_SUBTYPE_NAME_KEYS)
    | set(PARTY_SUBTYPE_ROSTER)
    | set(SELF_SUBTYPE_NAME_KEYS)
    | {
        PARTY_SUBTYPE_DISBAND,
        PARTY_SUBTYPE_PLAYER_LEFT,
        PARTY_SUBTYPE_PLAYER_JOINED,
        PARTY_SUBTYPE_MEMBER_REMOVED,
        MATCH_ROSTER_SUBTYPE,
        COMBAT_TARGET_SUBTYPE,
    }
)


@dataclass
class PartyRegistry:
    strict: bool = True
    _party_names: set[str] = field(default_factory=set)
    _party_ids: set[int] = field(default_factory=set)
    _resolved_party_names: set[str] = field(default_factory=set)
    _party_guids: set[bytes] = field(default_factory=set)
    _party_guid_names: dict[bytes, str] = field(default_factory=dict)
    _combat_ids_seen: set[int] = field(default_factory=set)
    _target_ids: set[int] = field(default_factory=set)
    _self_ids: set[int] = field(default_factory=set)
    _primary_self_id: int | None = None
    _self_name: str | None = None
    _self_name_confirmed: bool = False
    _recent_target_ids: deque[tuple[float, int]] = field(
        default_factory=lambda: deque(maxlen=500)
    )
    _recent_outbound_ts: deque[float] = field(default_factory=lambda: deque(maxlen=500))
    _target_request_ts: dict[int, float] = field(default_factory=dict)
    _self_candidate_scores: dict[int, float] = field(default_factory=dict)
    _self_candidate_last_ts: dict[int, float] = field(default_factory=dict)
    _self_candidate_link_hits: dict[int, int] = field(default_factory=dict)
    _self_candidate_combat_hits: dict[int, int] = field(default_factory=dict)
    _match_roster_names: set[str] = field(default_factory=set)
    _match_roster_order: list[str] = field(default_factory=list)
    _match_friend_ids: set[int] = field(default_factory=set)
    _match_enemy_ids: set[int] = field(default_factory=set)
    _match_pending_friend_ids: set[int] = field(default_factory=set)
    _match_pending_enemy_ids: set[int] = field(default_factory=set)
    _match_roster_seen_ts: float | None = None
    _recent_target_links: deque[tuple[float, int, int]] = field(
        default_factory=lambda: deque(maxlen=500)
    )
    _last_packet_fingerprint: tuple[float, str, int, str, int, int] | None = None
    _zone_key: str | None = None
    _map_index: str | None = None
    _membership_version: int = 0

    def observe(self, message: PhotonMessage, packet: RawPacket | None = None) -> None:
        if packet is not None:
            self._observe_packet_once(packet)
            self._apply_target_request(message, packet)
        if message.event_code is None:
            self._apply_join_response(message)
            return
        if message.event_code != PARTY_EVENT_CODE:
            return
        try:
            event = decode_event_data(message.payload)
        except Protocol16Error:
            return

        subtype = event.parameters.get(PARTY_SUBTYPE_KEY)
        if not isinstance(subtype, int):
            return
        if subtype == PARTY_SUBTYPE_DISBAND:
            if _looks_like_party_disband(event.parameters):
                self._clear_party()
            return
        if subtype == COMBAT_TARGET_SUBTYPE:
            self._apply_target_link(event.parameters, packet)
            return
        if subtype == PARTY_SUBTYPE_PLAYER_LEFT:
            guid = _coerce_guid(event.parameters.get(1))
            if guid is not None:
                self._remove_party_guid(guid)
            return
        if subtype == PARTY_SUBTYPE_MEMBER_REMOVED:
            guid = _coerce_guid(event.parameters.get(1))
            if guid is None:
                return
            name = self._party_guid_names.get(guid)
            if (
                name is not None
                and self._self_name is not None
                and name == self._self_name
            ):
                self._clear_party()
                return
            self._remove_party_guid(guid)
            return
        if subtype == PARTY_SUBTYPE_PLAYER_JOINED:
            guid = _coerce_guid(event.parameters.get(1))
            names = _coerce_names(event.parameters.get(PARTY_SUBTYPE_NAME_KEYS.get(subtype)))
            if guid is None or not names:
                return
            self._add_party_member(guid, names[0])
            return
        if subtype == MATCH_ROSTER_SUBTYPE:
            names = _coerce_names(event.parameters.get(MATCH_ROSTER_NAME_KEY))
            if len(names) >= MATCH_ROSTER_MIN_SIZE:
                self._set_match_roster(names)
            return
        if subtype in PARTY_SUBTYPE_ROSTER:
            guids, names = _extract_party_roster(event.parameters, subtype)
            if guids is not None:
                self._set_party_roster(guids, names)
                return
        if self._apply_unknown_party_fallback(subtype, event.parameters):
            return
        name_key = PARTY_SUBTYPE_NAME_KEYS.get(subtype)
        if name_key is None:
            name_key = SELF_SUBTYPE_NAME_KEYS.get(subtype)
        if name_key is None:
            return
        names = _coerce_names(event.parameters.get(name_key))
        if not names:
            return
        if subtype in SELF_SUBTYPE_NAME_KEYS:
            self.set_self_name(names[0], confirmed=False)
            return
        self._party_names.update(names)
        self._reset_party_ids_after_roster_change()

    def _apply_join_response(self, message: PhotonMessage) -> None:
        try:
            response = decode_operation_response(message.payload)
        except Protocol16Error:
            return
        op_code = response.parameters.get(OPERATION_CODE_KEY, response.code)
        if op_code == JOIN_OPERATION_CODE:
            entity_id = response.parameters.get(JOIN_SELF_ID_KEY)
            if isinstance(entity_id, int) and entity_id > 0:
                self._set_self_id(entity_id, replace=True)
            name = response.parameters.get(JOIN_SELF_NAME_KEY)
            if isinstance(name, str) and name:
                self.set_self_name(name, confirmed=True)
        elif op_code != CHANGE_CLUSTER_OPERATION_CODE:
            return

        map_index = extract_map_index_from_response(response)
        if map_index:
            self._set_map_index(map_index, allow_reset=op_code == CHANGE_CLUSTER_OPERATION_CODE)

    def observe_packet(self, packet: RawPacket) -> None:
        self._last_packet_fingerprint = (
            packet.timestamp,
            packet.src_ip,
            packet.src_port,
            packet.dst_ip,
            packet.dst_port,
            len(packet.payload),
        )
        self._update_zone_key(packet)
        if packet.dst_port in ZONE_PORTS and packet.src_port not in SERVER_PORTS:
            self._recent_outbound_ts.append(packet.timestamp)
        _prune_deque(self._recent_outbound_ts, packet.timestamp, SELF_ID_CANDIDATE_TTL_SECONDS)
        _prune_deque_pairs(self._recent_target_ids, packet.timestamp, TARGET_SELF_NAME_WINDOW_SECONDS)
        _prune_deque_triples(self._recent_target_links, packet.timestamp, TARGET_LINK_WINDOW_SECONDS)
        self._prune_candidate_scores(packet.timestamp)
        cutoff = packet.timestamp - SELF_ID_CANDIDATE_TTL_SECONDS
        for target_id, ts in list(self._target_request_ts.items()):
            if ts < cutoff:
                self._target_request_ts.pop(target_id, None)

    def observe_combat_event(
        self,
        event: CombatEvent,
        name_registry: NameRegistry | None = None,
    ) -> None:
        if self._primary_self_id is not None:
            self._apply_match_roster_inference(event, name_registry)
            return
        if not isinstance(event.target_id, int) or not isinstance(event.source_id, int):
            return
        requested_ts = self._target_request_ts.get(event.target_id)
        if requested_ts is None:
            return
        if not _has_outbound_correlation(self._recent_outbound_ts, event.timestamp):
            return
        self._add_self_candidate_score(event.source_id, event.timestamp, weight=1.0)
        self._self_candidate_combat_hits[event.source_id] = (
            self._self_candidate_combat_hits.get(event.source_id, 0) + 1
        )
        self._apply_match_roster_inference(event, name_registry)

    def try_resolve_self_id(self, name_registry: NameRegistry | None = None) -> None:
        if self._primary_self_id is not None:
            return
        self._prune_candidate_scores(None)
        if not self._self_candidate_scores:
            return

        if (
            name_registry is not None
            and self._self_name_confirmed
            and self._self_name
        ):
            matches = [
                entity_id
                for entity_id in self._self_candidate_scores.keys()
                if name_registry.lookup(entity_id) == self._self_name
            ]
            if len(matches) == 1:
                if (
                    self._self_candidate_link_hits.get(matches[0], 0) > 0
                    and self._self_candidate_combat_hits.get(matches[0], 0) > 0
                ):
                    self._accept_self_id_candidate(matches[0])
                return

        best_id, best_score = max(self._self_candidate_scores.items(), key=lambda item: item[1])
        second_score = max(
            (score for entity_id, score in self._self_candidate_scores.items() if entity_id != best_id),
            default=0.0,
        )
        if best_score >= SELF_ID_MIN_SCORE and (best_score - second_score) >= SELF_ID_MIN_SCORE_GAP:
            if self._self_candidate_combat_hits.get(best_id, 0) <= 0:
                return
            self._accept_self_id_candidate(best_id)

    def seed_names(self, names: Iterable[str]) -> None:
        for name in names:
            if isinstance(name, str) and name:
                self._party_names.add(name)

    def seed_ids(self, ids: Iterable[int]) -> None:
        for entity_id in ids:
            if isinstance(entity_id, int):
                self._party_ids.add(entity_id)

    def seed_self_ids(self, ids: Iterable[int]) -> None:
        for entity_id in ids:
            if isinstance(entity_id, int):
                self._set_self_id(entity_id, replace=False)

    def _set_self_id(self, entity_id: int, *, replace: bool) -> None:
        if not isinstance(entity_id, int):
            return
        if replace:
            previous = set(self._self_ids)
            self._self_ids.clear()
            if previous:
                self._party_ids.difference_update(previous)
            self._primary_self_id = None
        self._party_ids.add(entity_id)
        self._self_ids.add(entity_id)
        if self._primary_self_id is None:
            self._primary_self_id = entity_id

    def set_self_name(self, name: str, *, confirmed: bool = False) -> None:
        if not isinstance(name, str) or not name:
            return
        if confirmed:
            self._self_name = name
            self._self_name_confirmed = True
            self._maybe_trim_match_roster()
            return
        if not _looks_like_player_name(name):
            return
        if self._self_name_confirmed:
            return
        if self._self_name is None:
            self._self_name = name

    def _apply_unknown_party_fallback(self, subtype: int, parameters: dict[int, object]) -> bool:
        if subtype in KNOWN_PARTY_SUBTYPES:
            return False
        if subtype < PARTY_FALLBACK_SUBTYPE_MIN or subtype > PARTY_FALLBACK_SUBTYPE_MAX:
            return False

        guid_list_fields = _extract_party_guid_list_fields(parameters)
        single_guid_fields = _extract_party_single_guid_fields(parameters)
        if not guid_list_fields and not single_guid_fields:
            return False
        name_fields = _extract_party_name_fields(parameters)

        for guids in sorted(guid_list_fields, key=len, reverse=True):
            if len(guids) < 2:
                continue
            for names in name_fields:
                if len(names) != len(guids):
                    continue
                self._set_party_roster(guids, names)
                return True

        single_guid = single_guid_fields[0] if single_guid_fields else None
        if single_guid is None:
            return False

        single_name = parameters.get(2)
        if isinstance(single_name, str) and _looks_like_player_name(single_name):
            self._add_party_member(single_guid, single_name)
            return True
        return False

    def _maybe_trim_match_roster(self) -> None:
        if not self._self_name or not self._match_roster_order:
            return
        roster = self._match_roster_order
        if len(roster) < MATCH_ROSTER_MIN_SIZE * 2 or len(roster) % 2 != 0:
            return
        half = len(roster) // 2
        first = roster[:half]
        second = roster[half:]
        if self._self_name in first:
            self._set_match_roster(first)
        elif self._self_name in second:
            self._set_match_roster(second)

    def snapshot_names(self) -> set[str]:
        return set(self._party_names)

    def snapshot_ids(self) -> set[int]:
        return set(self._party_ids)

    def snapshot_guids(self) -> set[bytes]:
        return set(self._party_guids)

    def snapshot_self_ids(self) -> set[int]:
        return set(self._self_ids)

    def membership_version(self) -> int:
        return self._membership_version

    def has_ids(self) -> bool:
        if self.strict:
            return bool(self._self_ids)
        return bool(self._party_ids)

    def has_unresolved_names(self) -> bool:
        if not self._party_names:
            return False
        return bool(self._party_names.difference(self._resolved_party_names))

    def sync_names(self, name_registry: NameRegistry) -> None:
        if not self._party_names:
            return
        snapshot = name_registry.snapshot()
        mapped_ids: set[int] = set()
        for entity_id, name in snapshot.items():
            if name not in self._party_names:
                continue
            if not isinstance(entity_id, int) or entity_id <= 0:
                continue
            if (
                entity_id in self._self_ids
                and self._self_name_confirmed
                and self._self_name is not None
                and name != self._self_name
            ):
                continue
            if entity_id not in self._combat_ids_seen and entity_id not in self._self_ids:
                continue
            mapped_ids.add(entity_id)
            self._resolved_party_names.add(name)
        if mapped_ids:
            self._party_ids.update(mapped_ids)
        self._resolve_match_pending(name_registry)

    def sync_guids(self, name_registry: NameRegistry) -> None:
        if not self._party_guids:
            return
        snapshot = name_registry.snapshot_guid_names()
        updated = False
        for guid in list(self._party_guids):
            name = snapshot.get(guid)
            if not name:
                continue
            if self._party_guid_names.get(guid) != name:
                self._party_guid_names[guid] = name
                if name not in self._party_names:
                    self._party_names.add(name)
                    updated = True
        id_guids = name_registry.snapshot_id_guids()
        mapped_ids: set[int] = set()
        for entity_id, guid in id_guids.items():
            if guid not in self._party_guids:
                continue
            if not isinstance(entity_id, int) or entity_id <= 0:
                continue
            mapped_ids.add(entity_id)
            name = snapshot.get(guid) or self._party_guid_names.get(guid)
            if name:
                if name not in self._party_names:
                    self._party_names.add(name)
                    updated = True
                self._resolved_party_names.add(name)
        if mapped_ids:
            self._party_ids.update(mapped_ids)
        if updated:
            self._reset_party_ids_after_roster_change()

    def infer_self_name_from_targets(self, name_registry: NameRegistry) -> None:
        if self._self_name_confirmed:
            return
        if self._party_names:
            return
        if not self._recent_target_ids:
            return

        last_ts = self._recent_target_ids[-1][0]
        cutoff = last_ts - TARGET_SELF_NAME_WINDOW_SECONDS
        counts: dict[str, int] = {}
        distinct_ids: dict[str, set[int]] = {}
        for ts, entity_id in self._recent_target_ids:
            if ts < cutoff:
                continue
            name = name_registry.lookup(entity_id)
            if not _looks_like_player_name(name):
                continue
            counts[name] = counts.get(name, 0) + 1
            distinct_ids.setdefault(name, set()).add(entity_id)
        if not counts:
            return

        sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        best_name, best_count = sorted_counts[0]
        second_count = sorted_counts[1][1] if len(sorted_counts) > 1 else 0
        if best_count < TARGET_SELF_NAME_MIN_COUNT:
            return
        if second_count > 0 and (best_count / float(second_count)) < TARGET_SELF_NAME_MIN_RATIO:
            return
        confirm = best_count >= TARGET_SELF_NAME_CONFIRM_COUNT or len(distinct_ids.get(best_name, set())) >= 2
        if self._self_name is not None and self._self_name != best_name:
            return
        self.set_self_name(best_name, confirmed=confirm)

    def sync_id_names(self, name_registry: NameRegistry) -> None:
        if not self._self_ids:
            return
        if not self._self_name or not self._self_name_confirmed:
            return
        for entity_id in self._self_ids:
            name_registry.record(entity_id, self._self_name)

    def sync_self_name(self, name_registry: NameRegistry) -> None:
        if self._self_ids:
            for entity_id in self._self_ids:
                mapped = name_registry.lookup(entity_id)
                if mapped:
                    if self._self_name_confirmed and self._self_name and mapped != self._self_name:
                        continue
                    if self._self_name != mapped or not self._self_name_confirmed:
                        self.set_self_name(mapped, confirmed=True)
                    return
        if (
            not self._self_ids
            and self._self_name_confirmed
            and self._self_name
            and _looks_like_player_name(self._self_name)
        ):
            snapshot = name_registry.snapshot()
            for entity_id, name in snapshot.items():
                if name == self._self_name and isinstance(entity_id, int) and entity_id > 0:
                    self._set_self_id(entity_id, replace=False)
            if self._self_ids:
                return
        if not self._party_names:
            return
        snapshot = name_registry.snapshot()
        name_ids: dict[str, set[int]] = {name: set() for name in self._party_names}
        for entity_id, name in snapshot.items():
            if name in name_ids and isinstance(entity_id, int) and entity_id > 0:
                name_ids[name].add(entity_id)
        non_self_names = set()
        for name, ids in name_ids.items():
            if any(entity_id in self._party_ids and entity_id not in self._self_ids for entity_id in ids):
                non_self_names.add(name)
        candidates = [name for name in self._party_names if name not in non_self_names]
        if len(candidates) == 1:
            self.set_self_name(candidates[0], confirmed=True)

    def allows(self, source_id: int, name_registry: NameRegistry | None = None) -> bool:
        if not isinstance(source_id, int):
            return False
        self._combat_ids_seen.add(source_id)
        if self.strict:
            if not self._self_ids:
                if name_registry is None:
                    return False
                name = name_registry.lookup(source_id)
                if self._self_name_confirmed and self._self_name:
                    if name == self._self_name:
                        return True
                if self._party_names:
                    return name is not None and name in self._party_names
                return False
            if source_id in self._party_ids or source_id in self._self_ids:
                return True
            if name_registry is None or not self._party_names:
                return False
            name = name_registry.lookup(source_id)
            return name is not None and name in self._party_names
        if self._party_ids:
            if source_id in self._party_ids:
                return True
            if name_registry is None or not self._party_names:
                return False
            name = name_registry.lookup(source_id)
            return name is not None and name in self._party_names
        if not self._party_names or name_registry is None:
            return True
        name = name_registry.lookup(source_id)
        return name is not None and name in self._party_names

    def _apply_target_request(self, message: PhotonMessage, packet: RawPacket) -> None:
        if message.event_code is not None:
            return
        if packet.dst_port not in ZONE_PORTS:
            return
        try:
            request = decode_operation_request(message.payload)
        except Protocol16Error:
            return
        if request.code != TARGET_REQUEST_OPCODE:
            return
        entity_id = request.parameters.get(TARGET_REQUEST_ID_KEY)
        if isinstance(entity_id, int):
            self._target_ids.add(entity_id)
            self._recent_target_ids.append((packet.timestamp, entity_id))
            self._target_request_ts[entity_id] = packet.timestamp
            self._apply_target_link_hint_from_recent_links(entity_id, packet.timestamp)

    def _apply_target_link(self, parameters: dict[int, object], packet: RawPacket | None) -> None:
        first = parameters.get(COMBAT_TARGET_A_KEY)
        second = parameters.get(COMBAT_TARGET_B_KEY)
        if not isinstance(first, int) or not isinstance(second, int):
            return
        ts = packet.timestamp if packet is not None else 0.0
        self._recent_target_links.append((ts, first, second))
        if not self._target_ids:
            return
        self._apply_target_link_hint(first, second, ts)

    def _apply_target_link_hint_from_recent_links(self, target_id: int, ts: float) -> None:
        for link_ts, first, second in reversed(self._recent_target_links):
            if (ts - link_ts) > TARGET_LINK_WINDOW_SECONDS:
                break
            if (ts - link_ts) > TARGET_LINK_REORDER_SECONDS:
                continue
            if first == target_id and second != target_id:
                self._apply_target_link_hint(first, second, ts)
            elif second == target_id and first != target_id:
                self._apply_target_link_hint(first, second, ts)

    def _apply_target_link_hint(self, first: int, second: int, ts: float) -> None:
        if first in self._target_ids and second not in self._target_ids:
            candidate = second
        elif second in self._target_ids and first not in self._target_ids:
            candidate = first
        else:
            return
        self._add_self_candidate_score(candidate, ts, weight=0.5)
        self._self_candidate_link_hits[candidate] = self._self_candidate_link_hits.get(candidate, 0) + 1

    def _accept_self_id_candidate(self, candidate_id: int) -> None:
        if not isinstance(candidate_id, int):
            return
        if self._primary_self_id is None:
            self._primary_self_id = candidate_id
            self._self_ids.add(candidate_id)
            self._party_ids.add(candidate_id)
            return
        if candidate_id != self._primary_self_id:
            return
        self._self_ids.add(candidate_id)
        self._party_ids.add(candidate_id)

    def _add_self_candidate_score(self, candidate_id: int, ts: float, *, weight: float) -> None:
        if not isinstance(candidate_id, int):
            return
        current = float(self._self_candidate_scores.get(candidate_id, 0.0))
        self._self_candidate_scores[candidate_id] = current + float(weight)
        self._self_candidate_last_ts[candidate_id] = float(ts)

    def _prune_candidate_scores(self, now: float | None) -> None:
        if now is None:
            if self._self_candidate_last_ts:
                now = max(self._self_candidate_last_ts.values())
            else:
                return
        cutoff = now - SELF_ID_CANDIDATE_TTL_SECONDS
        for entity_id, ts in list(self._self_candidate_last_ts.items()):
            if ts < cutoff:
                self._self_candidate_last_ts.pop(entity_id, None)
                self._self_candidate_scores.pop(entity_id, None)
                self._self_candidate_link_hits.pop(entity_id, None)
                self._self_candidate_combat_hits.pop(entity_id, None)

    def _observe_packet_once(self, packet: RawPacket) -> None:
        fingerprint = (
            packet.timestamp,
            packet.src_ip,
            packet.src_port,
            packet.dst_ip,
            packet.dst_port,
            len(packet.payload),
        )
        if fingerprint == self._last_packet_fingerprint:
            return
        self._last_packet_fingerprint = fingerprint
        self.observe_packet(packet)

    def _update_zone_key(self, packet: RawPacket) -> None:
        if self._map_index is not None:
            return
        zone_key = _infer_zone_key(packet)
        if zone_key is None:
            return
        if self._zone_key is None:
            self._zone_key = zone_key
            return
        if zone_key != self._zone_key:
            self._zone_key = zone_key
            self._reset_for_zone_change()

    def _set_map_index(self, map_index: str, *, allow_reset: bool) -> None:
        if not map_index:
            return
        if self._map_index is None:
            self._map_index = map_index
            self._zone_key = map_index
            return
        if map_index == self._map_index:
            return
        self._map_index = map_index
        self._zone_key = map_index
        if allow_reset:
            self._reset_for_zone_change()

    def _reset_for_zone_change(self) -> None:
        self._target_ids.clear()
        self._recent_target_ids.clear()
        self._recent_outbound_ts.clear()
        self._target_request_ts.clear()
        self._self_candidate_scores.clear()
        self._self_candidate_last_ts.clear()
        self._self_candidate_link_hits.clear()
        self._self_candidate_combat_hits.clear()
        keep_match_roster = False
        if self._match_roster_names and self._match_roster_seen_ts is not None:
            now = self._last_packet_fingerprint[0] if self._last_packet_fingerprint else None
            if now is not None and (now - self._match_roster_seen_ts) <= MATCH_ROSTER_TTL_SECONDS:
                keep_match_roster = True
        if not keep_match_roster:
            self._match_roster_names.clear()
            self._match_roster_order.clear()
            self._match_friend_ids.clear()
            self._match_enemy_ids.clear()
            self._match_pending_friend_ids.clear()
            self._match_pending_enemy_ids.clear()
            self._match_roster_seen_ts = None
        if self._self_name_confirmed and self._self_ids:
            self._party_ids.intersection_update(self._self_ids)
        else:
            previous = set(self._self_ids)
            self._self_ids.clear()
            if previous:
                self._party_ids.difference_update(previous)
            self._primary_self_id = None
        self._combat_ids_seen.clear()

    def _clear_party(self) -> None:
        had_party_state = bool(
            self._party_names
            or self._party_guids
            or self._party_guid_names
            or self._match_roster_names
            or self._match_friend_ids
            or self._match_enemy_ids
            or self._match_pending_friend_ids
            or self._match_pending_enemy_ids
        )
        self._party_names.clear()
        self._resolved_party_names.clear()
        self._party_guids.clear()
        self._party_guid_names.clear()
        self._match_roster_names.clear()
        self._match_roster_order.clear()
        self._match_friend_ids.clear()
        self._match_enemy_ids.clear()
        self._match_pending_friend_ids.clear()
        self._match_pending_enemy_ids.clear()
        self._match_roster_seen_ts = None
        if self._self_ids:
            self._party_ids.intersection_update(self._self_ids)
        else:
            self._party_ids.clear()
        if had_party_state:
            self._membership_version += 1

    def _reset_party_ids_after_roster_change(self) -> None:
        self._resolved_party_names.clear()
        if self._self_ids:
            self._party_ids.intersection_update(self._self_ids)
        else:
            self._party_ids.clear()

    def _set_party_roster(self, guids: list[bytes], names: list[str] | None) -> None:
        next_guids = set(guids)
        next_guid_names: dict[bytes, str] = {}
        if names:
            for guid, name in zip(guids, names):
                if name:
                    next_guid_names[guid] = name
        next_names = set(next_guid_names.values())
        changed = (
            next_guids != self._party_guids
            or next_guid_names != self._party_guid_names
            or next_names != self._party_names
        )
        self._party_guids = set(guids)
        self._party_guid_names.clear()
        self._party_names.clear()
        if names:
            for guid, name in zip(guids, names):
                if name:
                    self._party_guid_names[guid] = name
                    self._party_names.add(name)
        self._reset_party_ids_after_roster_change()
        if changed:
            self._membership_version += 1

    def _add_party_member(self, guid: bytes | None, name: str | None) -> None:
        changed = False
        if guid is not None and guid not in self._party_guids:
            changed = True
        if name and name not in self._party_names:
            changed = True
        if guid is not None and name and self._party_guid_names.get(guid) != name:
            changed = True
        if guid is not None:
            self._party_guids.add(guid)
        if name:
            self._party_names.add(name)
        if guid is not None and name:
            self._party_guid_names[guid] = name
        self._reset_party_ids_after_roster_change()
        if changed:
            self._membership_version += 1

    def _remove_party_guid(self, guid: bytes) -> None:
        if guid not in self._party_guids:
            return
        self._party_guids.discard(guid)
        name = self._party_guid_names.pop(guid, None)
        if name is not None:
            if name not in self._party_guid_names.values():
                self._party_names.discard(name)
                self._resolved_party_names.discard(name)
        self._reset_party_ids_after_roster_change()
        self._membership_version += 1

    def _set_match_roster(self, names: list[str]) -> None:
        roster = list(names)
        trimmed = False
        self._match_roster_order = roster
        if (
            self._self_name
            and len(roster) >= MATCH_ROSTER_MIN_SIZE * 2
            and len(roster) % 2 == 0
        ):
            half = len(roster) // 2
            first = roster[:half]
            second = roster[half:]
            if self._self_name in first:
                roster = first
                trimmed = True
            elif self._self_name in second:
                roster = second
                trimmed = True
        self._match_roster_names = set(roster)
        self._match_friend_ids.clear()
        self._match_enemy_ids.clear()
        self._match_pending_friend_ids.clear()
        self._match_pending_enemy_ids.clear()
        if (
            self._self_name
            and self._self_name in roster
            and (trimmed or len(roster) <= MATCH_ROSTER_MIN_SIZE)
        ):
            if not self._party_names.issuperset(roster):
                self._party_names.update(roster)
                self._reset_party_ids_after_roster_change()
        if self._last_packet_fingerprint is not None:
            self._match_roster_seen_ts = self._last_packet_fingerprint[0]
        else:
            self._match_roster_seen_ts = None

    def _apply_match_roster_inference(
        self,
        event: CombatEvent,
        name_registry: NameRegistry | None,
    ) -> None:
        if not self._match_roster_names or name_registry is None:
            return
        if not isinstance(event.source_id, int) or not isinstance(event.target_id, int):
            return
        source_name = name_registry.lookup(event.source_id)
        target_name = name_registry.lookup(event.target_id)
        if (
            source_name is not None
            and source_name not in self._match_roster_names
            and target_name is not None
            and target_name not in self._match_roster_names
        ):
            return

        source_is_party = event.source_id in self._party_ids or event.source_id in self._self_ids
        target_is_party = event.target_id in self._party_ids or event.target_id in self._self_ids
        if event.kind == "damage":
            if source_is_party:
                self._mark_match_enemy(event.target_id, target_name)
            if target_is_party:
                self._mark_match_enemy(event.source_id, source_name)
        else:
            if source_is_party:
                self._mark_match_friend(event.target_id, target_name)
            if target_is_party:
                self._mark_match_friend(event.source_id, source_name)

    def _mark_match_enemy(self, entity_id: int, name: str | None) -> None:
        if not isinstance(entity_id, int):
            return
        if name is None:
            self._match_pending_enemy_ids.add(entity_id)
            return
        if name is not None and name not in self._match_roster_names:
            return
        self._match_enemy_ids.add(entity_id)
        if entity_id in self._match_friend_ids:
            self._match_friend_ids.discard(entity_id)
            self._party_ids.discard(entity_id)
            if name and name in self._party_names:
                self._party_names.discard(name)
                self._resolved_party_names.discard(name)

    def _mark_match_friend(self, entity_id: int, name: str | None) -> None:
        if not isinstance(entity_id, int):
            return
        if name is None:
            self._match_pending_friend_ids.add(entity_id)
            return
        if name is None or name not in self._match_roster_names:
            return
        if entity_id in self._match_enemy_ids:
            return
        if entity_id not in self._match_friend_ids:
            self._match_friend_ids.add(entity_id)
        if entity_id not in self._party_ids:
            self._party_ids.add(entity_id)
        if name not in self._party_names:
            self._party_names.add(name)
        self._resolved_party_names.add(name)

    def _resolve_match_pending(self, name_registry: NameRegistry) -> None:
        if not self._match_roster_names:
            return
        if self._match_pending_friend_ids:
            for entity_id in list(self._match_pending_friend_ids):
                name = name_registry.lookup(entity_id)
                if name is None:
                    continue
                self._match_pending_friend_ids.discard(entity_id)
                self._mark_match_friend(entity_id, name)
        if self._match_pending_enemy_ids:
            for entity_id in list(self._match_pending_enemy_ids):
                name = name_registry.lookup(entity_id)
                if name is None:
                    continue
                self._match_pending_enemy_ids.discard(entity_id)
                self._mark_match_enemy(entity_id, name)


def _infer_zone_key(packet: RawPacket) -> str | None:
    if packet.src_port in ZONE_PORTS:
        return f"{packet.src_ip}:{packet.src_port}"
    if packet.dst_port in ZONE_PORTS:
        return f"{packet.dst_ip}:{packet.dst_port}"
    return None


def _coerce_names(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    return []


def _looks_like_party_disband(parameters: dict[int, object]) -> bool:
    extra_keys = set(parameters.keys()) - {1, 252}
    if extra_keys:
        return False
    return isinstance(parameters.get(1), int)


def _coerce_guid(value: object) -> bytes | None:
    if isinstance(value, (bytes, bytearray)) and len(value) == 16:
        return bytes(value)
    return None


def _coerce_guid_list(value: object) -> list[bytes] | None:
    if _coerce_guid(value) is not None:
        return [bytes(value)]
    if isinstance(value, list) and value:
        items = [bytes(item) for item in value if _coerce_guid(item) is not None]
        return items if items else None
    return None


def _extract_party_roster(
    parameters: dict[int, object],
    subtype: int,
) -> tuple[list[bytes] | None, list[str] | None]:
    if subtype == 212:
        guid_keys = (4, 3)
        name_key = 5
    elif subtype == 227:
        guid_keys = (12,)
        name_key = 13
    else:
        guid_keys = (5,)
        name_key = 6

    guids: list[bytes] | None = None
    for key in guid_keys:
        guids = _coerce_guid_list(parameters.get(key))
        if guids:
            break

    names = _coerce_names(parameters.get(name_key))
    if guids and names and len(names) != len(guids):
        return None, None
    return guids, names if names else None


def _extract_party_guid_list_fields(parameters: dict[int, object]) -> list[list[bytes]]:
    fields: list[list[bytes]] = []
    for key, value in parameters.items():
        if key == PARTY_SUBTYPE_KEY:
            continue
        if not isinstance(value, list):
            continue
        guids = [bytes(item) for item in value if _coerce_guid(item) is not None]
        if not guids or len(guids) != len(value):
            continue
        if len(guids) > PARTY_FALLBACK_MAX_ROSTER_SIZE:
            continue
        fields.append(guids)
    return fields


def _extract_party_single_guid_fields(parameters: dict[int, object]) -> list[bytes]:
    fields: list[bytes] = []
    for key in PARTY_FALLBACK_SINGLE_GUID_KEYS:
        guid = _coerce_guid(parameters.get(key))
        if guid is not None:
            fields.append(guid)
    return fields


def _extract_party_name_fields(parameters: dict[int, object]) -> list[list[str]]:
    fields: list[list[str]] = []
    for key, value in parameters.items():
        if key == PARTY_SUBTYPE_KEY:
            continue
        names = _coerce_names(value)
        if not names:
            continue
        if len(names) > PARTY_FALLBACK_MAX_ROSTER_SIZE:
            continue
        if not all(_looks_like_player_name(name) for name in names):
            continue
        fields.append(names)
    return fields


def _looks_like_player_name(name: str | None) -> bool:
    if not isinstance(name, str) or not name:
        return False
    if name in NON_PLAYER_NAMES:
        return False
    if name.startswith(NON_PLAYER_NAME_PREFIXES):
        return False
    return True


def _prune_deque(values: deque[float], now: float, window_seconds: float) -> None:
    cutoff = now - window_seconds
    while values and values[0] < cutoff:
        values.popleft()


def _prune_deque_pairs(values: deque[tuple[float, int]], now: float, window_seconds: float) -> None:
    cutoff = now - window_seconds
    while values and values[0][0] < cutoff:
        values.popleft()


def _prune_deque_triples(values: deque[tuple[float, int, int]], now: float, window_seconds: float) -> None:
    cutoff = now - window_seconds
    while values and values[0][0] < cutoff:
        values.popleft()


def _has_outbound_correlation(outbound_ts: deque[float], event_ts: float) -> bool:
    for ts in reversed(outbound_ts):
        if ts > event_ts:
            continue
        if (event_ts - ts) <= SELF_ID_CORRELATION_WINDOW_SECONDS:
            return True
        break
    return False
