from __future__ import annotations

from dataclasses import dataclass, field

from albion_dps.models import PhotonMessage, RawPacket
from albion_dps.protocol.protocol16 import Protocol16Error, decode_event_data

NAME_EVENT_CODE = 1
NAME_ID_KEY = 0
NAME_VALUE_KEY = 1
NAME_SUBTYPE_KEY = 252
NAME_SUBTYPE_ID_NAME = 275
NAME_SUBTYPE_NAME_KEY = 2
NAME_SUBTYPE_ENTITY_NAME = 166
NAME_SUBTYPE_ENTITY_ID_KEY = 0
NAME_SUBTYPE_ENTITY_ALT_ID_KEY = 4
NAME_SUBTYPE_ENTITY_NAME_KEY = 5
NAME_SUBTYPE_UNIT_INFO = 29
NAME_SUBTYPE_UNIT_NAME_KEY = 1
NAME_UNIT_EQUIPMENT_LIST_KEY = 40
NAME_SUBTYPE_CHARACTER_INFO = 30
NAME_SUBTYPE_CHARACTER_NAME_KEY = 5
NAME_SUBTYPE_EQUIPMENT = 90
NAME_EQUIPMENT_ENTITY_ID_KEY = 0
NAME_EQUIPMENT_ITEM_LIST_KEY = 2
NAME_EQUIPMENT_MIN_MATCHES = 3
NAME_EQUIPMENT_MIN_RATIO = 2.0
NAME_PARTY_JOINED_SUBTYPE = 212
NAME_PARTY_PLAYER_JOINED_SUBTYPE = 214
NAME_CURRENT_PARTY_PLAYER_JOINED_SUBTYPE = 233
NAME_PARTY_JOINED_GUID_KEYS = (3, 4)
NAME_PARTY_JOINED_NAME_KEYS = (5, 6)
NON_PLAYER_NAME_PREFIXES = ("@", "MOB_", "NPC_")
NON_PLAYER_NAMES = {"SYSTEM", "System", "owner", "friend", "user"}


@dataclass
class NameRegistry:
    _names: dict[int, str] = field(default_factory=dict)
    # Player identity is deliberately kept separate from the generic entity
    # label cache. Albion reuses parameter keys across event types, so a later
    # mob/status event may legitimately update ``_names`` for the same numeric
    # id. It must not erase a player identity established by NewCharacter.
    _player_names: dict[int, str] = field(default_factory=dict)
    _guid_names: dict[bytes, str] = field(default_factory=dict)
    _id_guids: dict[int, bytes] = field(default_factory=dict)
    _strong_name_ids: dict[str, set[int]] = field(default_factory=dict)
    _weak_name_ids: dict[str, set[int]] = field(default_factory=dict)
    _strong_id_names: dict[int, str] = field(default_factory=dict)
    _item_names: dict[int, set[str]] = field(default_factory=dict)
    _entity_items: dict[int, list[int]] = field(default_factory=dict)
    _local_entity_ts: dict[int, float] = field(default_factory=dict)

    def observe(self, message: PhotonMessage, packet: RawPacket | None = None) -> None:
        if message.event_code is None:
            return
        if message.event_code != NAME_EVENT_CODE:
            return
        try:
            event = decode_event_data(message.payload)
        except Protocol16Error:
            return

        self._apply_event(event.parameters, packet)

    def snapshot(self) -> dict[int, str]:
        merged = dict(self._names)
        merged.update(self._player_names)
        for entity_id, guid in self._id_guids.items():
            name = self._guid_names.get(guid)
            if _looks_like_player_name(name):
                merged[entity_id] = name
        return merged

    def lookup(self, entity_id: int) -> str | None:
        name = self._names.get(entity_id)
        if name is not None:
            return name
        guid = self._id_guids.get(entity_id)
        if guid is None:
            return None
        return self._guid_names.get(guid)

    def lookup_player(self, entity_id: int) -> str | None:
        name = self._player_names.get(entity_id)
        if name is not None:
            return name
        guid = self._id_guids.get(entity_id)
        if guid is None:
            return None
        name = self._guid_names.get(guid)
        return name if _looks_like_player_name(name) else None

    def snapshot_players(self) -> dict[int, str]:
        players = dict(self._player_names)
        for entity_id, guid in self._id_guids.items():
            if entity_id in players:
                continue
            name = self._guid_names.get(guid)
            if _looks_like_player_name(name):
                players[entity_id] = name
        return players

    def record(self, entity_id: int, name: str) -> None:
        self._store(entity_id, name)
        self._store_player(entity_id, name)

    def record_local(self, entity_id: int, name: str, timestamp: float) -> None:
        self._store(entity_id, name)
        self._store_player(entity_id, name)
        self._mark_local(entity_id, timestamp)

    def record_weak(self, entity_id: int, name: str) -> None:
        self._store(entity_id, name, weak=True)

    def record_player_if_unknown(self, entity_id: int, name: str) -> None:
        if self.lookup_player(entity_id) is not None:
            return
        self._store(entity_id, name)
        self._store_player(entity_id, name)

    def snapshot_guid_names(self) -> dict[bytes, str]:
        return dict(self._guid_names)

    def snapshot_id_guids(self) -> dict[int, bytes]:
        return dict(self._id_guids)

    def lookup_guid(self, entity_id: int) -> bytes | None:
        return self._id_guids.get(entity_id)

    def items_for(self, entity_id: int) -> list[int]:
        items = self._entity_items.get(entity_id)
        if not items:
            return []
        return list(items)

    def snapshot_recent_ids(self, now: float, max_age: float) -> set[int]:
        if max_age <= 0:
            return set()
        cutoff = now - max_age
        return {
            entity_id
            for entity_id, ts in self._local_entity_ts.items()
            if ts >= cutoff
        }

    def _apply_event(self, parameters: dict[int, object], packet: RawPacket | None) -> None:
        self._apply_party_roster(parameters)
        self._apply_guid_link(parameters)
        subtype = parameters.get(NAME_SUBTYPE_KEY)
        timestamp = packet.timestamp if packet is not None else None
        if subtype == NAME_SUBTYPE_ENTITY_NAME:
            name = parameters.get(NAME_SUBTYPE_ENTITY_NAME_KEY)
            if isinstance(name, str) and name:
                entity_id = parameters.get(NAME_SUBTYPE_ENTITY_ID_KEY)
                alt_entity_id = parameters.get(NAME_SUBTYPE_ENTITY_ALT_ID_KEY)
                self._store(entity_id, name)
                self._store(alt_entity_id, name)
                self._store_player(entity_id, name)
                self._store_player(alt_entity_id, name)
                self._mark_local(entity_id, timestamp)
                self._mark_local(alt_entity_id, timestamp)
        if subtype == NAME_SUBTYPE_UNIT_INFO:
            name = parameters.get(NAME_SUBTYPE_UNIT_NAME_KEY)
            entity_id = parameters.get(NAME_SUBTYPE_ENTITY_ID_KEY)
            if isinstance(name, str) and name:
                self._store(entity_id, name)
                self._store(parameters.get(7), name)
                self._store_player(entity_id, name)
            items = parameters.get(NAME_UNIT_EQUIPMENT_LIST_KEY)
            if isinstance(entity_id, int) and isinstance(items, list):
                filtered = [item for item in items if isinstance(item, int) and item > 0]
                if filtered:
                    self._entity_items[entity_id] = filtered
            self._mark_local(entity_id, timestamp)
        if subtype == NAME_SUBTYPE_CHARACTER_INFO:
            name = parameters.get(NAME_SUBTYPE_CHARACTER_NAME_KEY)
            if isinstance(name, str) and name:
                entity_id = parameters.get(NAME_SUBTYPE_ENTITY_ID_KEY)
                self._store(entity_id, name)
                self._mark_local(entity_id, timestamp)
                item_id = parameters.get(1)
                if isinstance(item_id, int):
                    self._item_names.setdefault(item_id, set()).add(name)
                    if isinstance(entity_id, int):
                        self._infer_name_from_items(entity_id)
                    if self._entity_items:
                        for target_id, items in list(self._entity_items.items()):
                            if item_id in items:
                                self._infer_name_from_items(target_id)
        if subtype == NAME_SUBTYPE_EQUIPMENT:
            entity_id = parameters.get(NAME_EQUIPMENT_ENTITY_ID_KEY)
            items = parameters.get(NAME_EQUIPMENT_ITEM_LIST_KEY)
            if isinstance(entity_id, int) and isinstance(items, list):
                filtered = [item for item in items if isinstance(item, int) and item > 0]
                if filtered:
                    self._entity_items[entity_id] = filtered
                    self._infer_name_from_items(entity_id)
            self._mark_local(entity_id, timestamp)
        if subtype == NAME_SUBTYPE_ID_NAME:
            entity_id = parameters.get(NAME_ID_KEY)
            name = parameters.get(NAME_SUBTYPE_NAME_KEY)
            self._store(entity_id, name, weak=True)
            self._store_player(entity_id, name)
        raw_id = parameters.get(NAME_ID_KEY)
        raw_name = parameters.get(NAME_VALUE_KEY)

        if isinstance(raw_id, list) and isinstance(raw_name, list):
            for entity_id, name in zip(raw_id, raw_name):
                self._store(entity_id, name)
            return

        self._store(raw_id, raw_name)

    def _mark_local(self, entity_id: object, timestamp: float | None) -> None:
        if timestamp is None:
            return
        if isinstance(entity_id, int) and entity_id > 0:
            self._local_entity_ts[entity_id] = float(timestamp)

    def _store(self, entity_id: object, name: object, *, weak: bool = False) -> None:
        if isinstance(entity_id, int) and isinstance(name, str) and name:
            if weak:
                strong_name = self._strong_id_names.get(entity_id)
                if strong_name is not None and strong_name != name:
                    return
                strong_ids = self._strong_name_ids.get(name, set())
                if strong_ids and entity_id not in strong_ids:
                    return
                self._weak_name_ids.setdefault(name, set()).add(entity_id)
            else:
                strong_ids = self._strong_name_ids.setdefault(name, set())
                strong_ids.add(entity_id)
                self._strong_id_names[entity_id] = name
                weak_ids = self._weak_name_ids.get(name)
                if weak_ids:
                    for weak_id in list(weak_ids):
                        if weak_id in strong_ids:
                            continue
                        if self._names.get(weak_id) == name:
                            self._names.pop(weak_id, None)
                    weak_ids.intersection_update(strong_ids)
            self._names[entity_id] = name
            return
        guid_entity_id = _coerce_guid(entity_id)
        if guid_entity_id is not None and isinstance(name, str) and name:
            self._guid_names[guid_entity_id] = name

    def _store_player(self, entity_id: object, name: object) -> None:
        if (
            isinstance(entity_id, int)
            and entity_id > 0
            and _looks_like_player_name(name)
        ):
            self._player_names[entity_id] = name

    def _apply_guid_link(self, parameters: dict[int, object]) -> None:
        subtype = parameters.get(252)
        if subtype == 40:
            guid = _coerce_guid(parameters.get(3))
            entity_id = parameters.get(1)
            if isinstance(entity_id, int) and entity_id > 0 and guid is not None:
                self._bind_guid(entity_id, guid)
                return
        candidates: list[tuple[int, int]] = []
        if subtype == NAME_PARTY_PLAYER_JOINED_SUBTYPE:
            candidates.append((0, 1))
        if subtype in (11, 29):
            candidates.append((0, 7))
        if subtype == 308:
            candidates.append((0, 5))
            candidates.append((0, 9))
        for id_key, guid_key in candidates:
            candidate_id = parameters.get(id_key)
            candidate_guid = parameters.get(guid_key)
            if not isinstance(candidate_id, int) or candidate_id <= 0:
                continue
            guid = _coerce_guid(candidate_guid)
            if guid is None:
                continue
            self._bind_guid(candidate_id, guid)
            return

    def _bind_guid(self, entity_id: int, guid: bytes) -> None:
        previous_guid = self._id_guids.get(entity_id)
        if previous_guid is not None and previous_guid != guid:
            self._player_names.pop(entity_id, None)
        self._id_guids[entity_id] = guid

    def _apply_party_roster(self, parameters: dict[int, object]) -> None:
        subtype = parameters.get(252)
        if subtype in (
            NAME_PARTY_PLAYER_JOINED_SUBTYPE,
            NAME_CURRENT_PARTY_PLAYER_JOINED_SUBTYPE,
        ):
            guid = _coerce_guid(parameters.get(1))
            name = parameters.get(2)
            if guid is not None and isinstance(name, str) and name:
                self._guid_names[guid] = name
            return

        if subtype not in (227, 229, NAME_PARTY_JOINED_SUBTYPE):
            return

        if subtype == NAME_PARTY_JOINED_SUBTYPE:
            guid_keys = NAME_PARTY_JOINED_GUID_KEYS
            name_keys = NAME_PARTY_JOINED_NAME_KEYS
        elif subtype == 227:
            guid_keys = (12,)
            name_keys = (13,)
        else:
            guid_keys = (5,)
            name_keys = (6,)

        guids, names = _extract_party_roster_lists(
            parameters,
            guid_keys=guid_keys,
            name_keys=name_keys,
        )
        if not guids or not names:
            return
        for guid, name in zip(guids, names):
            if guid is not None and isinstance(name, str) and name:
                self._guid_names[guid] = name

    def _infer_name_from_items(self, entity_id: int) -> None:
        items = self._entity_items.get(entity_id)
        if not items:
            return
        counts: dict[str, int] = {}
        for item_id in items:
            for name in self._item_names.get(item_id, set()):
                if not name:
                    continue
                counts[name] = counts.get(name, 0) + 1
        if not counts:
            return
        sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        best_name, best_count = sorted_counts[0]
        second_count = sorted_counts[1][1] if len(sorted_counts) > 1 else 0
        if best_count < NAME_EQUIPMENT_MIN_MATCHES:
            return
        if second_count > 0 and (best_count / float(second_count)) < NAME_EQUIPMENT_MIN_RATIO:
            return
        current_strong = self._strong_id_names.get(entity_id)
        if current_strong is not None and current_strong != best_name:
            return
        self._store(entity_id, best_name)


def _is_guid(value: object) -> bool:
    return _coerce_guid(value) is not None


def _looks_like_player_name(value: object) -> bool:
    if not isinstance(value, str):
        return False
    name = value.strip()
    if not name or name in NON_PLAYER_NAMES or name.isdigit():
        return False
    upper = name.upper()
    return not any(upper.startswith(prefix) for prefix in NON_PLAYER_NAME_PREFIXES)


def _coerce_guid(value: object) -> bytes | None:
    if isinstance(value, (bytes, bytearray)) and len(value) == 16:
        return bytes(value)
    if isinstance(value, list) and len(value) == 16:
        out = bytearray()
        for item in value:
            if not isinstance(item, int) or item < 0 or item > 255:
                return None
            out.append(item)
        return bytes(out)
    return None


def _coerce_guid_list(value: object) -> list[bytes] | None:
    guid = _coerce_guid(value)
    if guid is not None:
        return [guid]
    if not isinstance(value, list) or not value:
        return None
    if all(isinstance(item, int) and 0 <= item <= 255 for item in value):
        if len(value) % 16 != 0:
            return None
        return [bytes(value[index : index + 16]) for index in range(0, len(value), 16)]
    guids = [_coerce_guid(item) for item in value]
    if any(guid is None for guid in guids):
        return None
    return [guid for guid in guids if guid is not None]


def _extract_party_roster_lists(
    parameters: dict[int, object],
    *,
    guid_keys: tuple[int, ...],
    name_keys: tuple[int, ...],
) -> tuple[list[bytes] | None, list[str] | None]:
    for guid_key in guid_keys:
        guid_values = _coerce_guid_list(parameters.get(guid_key))
        if not guid_values:
            continue
        for name_key in name_keys:
            name_values = parameters.get(name_key)
            if not isinstance(name_values, list) or not name_values:
                continue
            if not all(isinstance(value, str) for value in name_values):
                continue
            if len(name_values) != len(guid_values):
                continue
            return guid_values, name_values
    return None, None
