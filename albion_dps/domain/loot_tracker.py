from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace

from albion_dps.domain.item_resolver import ItemResolver
from albion_dps.domain.party_registry import PartyRegistry
from albion_dps.domain.loot_types import (
    LootContainer,
    LootEvent,
    LootItemRef,
    LootObject,
    LootPlayer,
)
from albion_dps.models import PhotonMessage, RawPacket
from albion_dps.protocol.protocol16 import (
    Protocol16Error,
    decode_event_data,
    decode_operation_request,
)

SILVER_FIXPOINT_FACTOR = 10000.0
LOOT_EVENT_CODE = 1
LOOT_SUBTYPE_KEY = 252

EV_NEW_CHARACTER = 29
EV_NEW_EQUIPMENT_ITEM = 30
EV_NEW_SIEGE_BANNER_ITEM = 31
EV_NEW_SIMPLE_ITEM = 32
EV_NEW_LOOT = 98
EV_ATTACH_ITEM_CONTAINER = 99
EV_DETACH_ITEM_CONTAINER = 100
EV_CHARACTER_STATS = 143
EV_OTHER_GRABBED_LOOT = 275
EV_PARTY_MEMBER_GRABBED_LOOT = 277
OP_INVENTORY_MOVE_ITEM = 30
OP_INVENTORY_MOVE_ITEMS = 39

LOOT_OBJECT_SUBTYPES = {
    EV_NEW_SIMPLE_ITEM,
    EV_NEW_EQUIPMENT_ITEM,
    EV_NEW_SIEGE_BANNER_ITEM,
}


@dataclass
class LootTracker:
    item_resolver: ItemResolver | None = None
    party_registry: PartyRegistry | None = None
    location_provider: Callable[[], str | None] | None = None
    include_silver: bool = False
    history_limit: int = 500
    _players: dict[str, LootPlayer] = field(default_factory=dict)
    _loot_objects: dict[int, LootObject] = field(default_factory=dict)
    _containers_by_id: dict[int, LootContainer] = field(default_factory=dict)
    _containers_by_uuid: dict[str, LootContainer] = field(default_factory=dict)
    _events: list[LootEvent] = field(default_factory=list)

    def observe(self, message: PhotonMessage, packet: RawPacket | None = None) -> None:
        if message.event_code is None:
            self._observe_operation_request(
                message,
                timestamp=packet.timestamp if packet is not None else 0.0,
            )
            return
        if message.event_code != LOOT_EVENT_CODE:
            return
        try:
            event = decode_event_data(message.payload)
        except Protocol16Error:
            return

        subtype = event.parameters.get(LOOT_SUBTYPE_KEY)
        if not isinstance(subtype, int):
            subtype = event.code

        if subtype == EV_NEW_CHARACTER:
            self._observe_new_character(event.parameters)
            return
        if subtype == EV_CHARACTER_STATS:
            self._observe_character_stats(event.parameters)
            return
        if subtype in LOOT_OBJECT_SUBTYPES:
            self._observe_new_item_object(event.parameters)
            return
        if subtype == EV_NEW_LOOT:
            self._observe_new_loot(event.parameters)
            return
        if subtype == EV_ATTACH_ITEM_CONTAINER:
            self._observe_attach_item_container(event.parameters)
            return
        if subtype == EV_DETACH_ITEM_CONTAINER:
            self._observe_detach_item_container(event.parameters)
            return
        if subtype == EV_OTHER_GRABBED_LOOT:
            self._observe_other_grabbed_loot(
                event.parameters,
                timestamp=packet.timestamp if packet is not None else 0.0,
                raw_event_code=event.code,
                raw_subtype=subtype,
                trusted_party_member=False,
            )
            return
        if subtype == EV_PARTY_MEMBER_GRABBED_LOOT:
            self._observe_other_grabbed_loot(
                event.parameters,
                timestamp=packet.timestamp if packet is not None else 0.0,
                raw_event_code=event.code,
                raw_subtype=subtype,
                trusted_party_member=True,
            )

    def _observe_operation_request(
        self, message: PhotonMessage, *, timestamp: float
    ) -> None:
        try:
            request = decode_operation_request(message.payload)
        except Protocol16Error:
            return
        operation_code = request.parameters.get(253, request.code)
        if operation_code == OP_INVENTORY_MOVE_ITEM:
            if self._inventory_move_blocked_by_location():
                return
            self._observe_inventory_move_item(
                request.parameters,
                timestamp=timestamp,
                raw_operation_code=int(operation_code),
            )
            return
        if operation_code == OP_INVENTORY_MOVE_ITEMS:
            if self._inventory_move_blocked_by_location():
                return
            self._observe_inventory_move_items(
                request.parameters,
                timestamp=timestamp,
                raw_operation_code=int(operation_code),
            )

    def events(self, limit: int | None = None) -> list[LootEvent]:
        items = list(reversed(self._events))
        if limit is None:
            return items
        return items[: max(0, int(limit))]

    def player(self, player_name: str) -> LootPlayer | None:
        return self._players.get(player_name)

    def loot_object(self, object_id: int) -> LootObject | None:
        return self._loot_objects.get(int(object_id))

    def container(self, container_id: int) -> LootContainer | None:
        return self._containers_by_id.get(int(container_id))

    def reset(self) -> None:
        self._players.clear()
        self._loot_objects.clear()
        self._containers_by_id.clear()
        self._containers_by_uuid.clear()
        self._events.clear()

    def _observe_new_character(self, parameters: dict[int, object]) -> None:
        player_name = parameters.get(1)
        guild_name = parameters.get(8)
        alliance_name = parameters.get(51)
        if not isinstance(player_name, str) or not player_name:
            return
        self._upsert_player(
            player_name,
            guild_name=guild_name if isinstance(guild_name, str) and guild_name else None,
            alliance_name=alliance_name if isinstance(alliance_name, str) and alliance_name else None,
        )

    def _observe_character_stats(self, parameters: dict[int, object]) -> None:
        player_name = parameters.get(1)
        guild_name = parameters.get(2)
        alliance_name = parameters.get(4)
        if not isinstance(player_name, str) or not player_name:
            return
        self._upsert_player(
            player_name,
            guild_name=guild_name if isinstance(guild_name, str) and guild_name else None,
            alliance_name=alliance_name if isinstance(alliance_name, str) and alliance_name else None,
        )

    def _observe_new_item_object(self, parameters: dict[int, object]) -> None:
        object_id = parameters.get(0)
        item_num_id = parameters.get(1)
        quantity = parameters.get(2)
        if not isinstance(object_id, int) or object_id <= 0:
            return
        if not isinstance(item_num_id, int) or item_num_id <= 0:
            return
        if not isinstance(quantity, int) or quantity < 0:
            return
        item_ref = self._resolve_item(item_num_id)
        loot = self._loot_objects.get(object_id)
        if loot is None:
            self._loot_objects[object_id] = LootObject(
                object_id=object_id,
                item_num_id=item_num_id,
                quantity=quantity,
                item=item_ref,
            )
            return
        loot.item_num_id = item_num_id
        loot.quantity = quantity
        loot.item = item_ref

    def _observe_new_loot(self, parameters: dict[int, object]) -> None:
        container_id = parameters.get(0)
        owner_name = parameters.get(3)
        if not isinstance(container_id, int) or container_id <= 0:
            return
        owner_kind = "monster" if isinstance(owner_name, str) and owner_name.startswith("@MOB") else "player"
        container = self._containers_by_id.get(container_id)
        if container is None:
            container = LootContainer(
                container_id=container_id,
                owner_name=owner_name if isinstance(owner_name, str) and owner_name else None,
                owner_kind=owner_kind,
            )
            self._containers_by_id[container_id] = container
            return
        if isinstance(owner_name, str) and owner_name:
            container.owner_name = owner_name
        container.owner_kind = owner_kind

    def _observe_attach_item_container(self, parameters: dict[int, object]) -> None:
        container_id = parameters.get(0)
        raw_uuid = parameters.get(1)
        inventory = parameters.get(3)
        slot_base = _coerce_slot(parameters.get(4))
        if not isinstance(container_id, int) or container_id <= 0:
            return
        uuid_text = _normalize_uuid(raw_uuid)
        inventory_ids = _coerce_int_list(inventory)
        container = self._containers_by_id.get(container_id)
        if container is None:
            container = LootContainer(container_id=container_id, container_uuid=uuid_text)
            self._containers_by_id[container_id] = container
        if uuid_text:
            container.container_uuid = uuid_text
            self._containers_by_uuid[uuid_text] = container
        next_items: dict[int, LootObject] = {}
        for object_id in inventory_ids:
            loot = self._loot_objects.get(object_id)
            if loot is None:
                continue
            if not loot.owner_name and container.owner_name:
                loot.owner_name = container.owner_name
            next_items[object_id] = loot
        next_slot_items = _map_slot_items(inventory_ids, next_items, slot_base)
        container.items = next_items
        container.slot_items = next_slot_items
        container.index_items = _map_index_items(inventory_ids, next_items)

    def _observe_detach_item_container(self, parameters: dict[int, object]) -> None:
        uuid_text = _normalize_uuid(parameters.get(0))
        if not uuid_text:
            return
        container = self._containers_by_uuid.pop(uuid_text, None)
        if container is None:
            return
        self._containers_by_id.pop(container.container_id, None)

    def _observe_inventory_move_item(
        self,
        parameters: dict[int, object],
        *,
        timestamp: float,
        raw_operation_code: int,
    ) -> None:
        from_uuid = _normalize_uuid(parameters.get(1))
        to_uuid = _normalize_uuid(parameters.get(4))
        if not from_uuid or not to_uuid or from_uuid == to_uuid:
            return
        container = self._containers_by_uuid.get(from_uuid)
        if container is None:
            return
        looted_by_name = self._local_looter_name()

        from_slot = _first_slot(parameters.get(0), parameters.get(2))
        loot = _select_container_loot(container, from_slot)
        if loot is None or loot.quantity <= 0:
            return

        source_name = loot.owner_name or container.owner_name
        source_kind = _classify_source_kind(source_name) if source_name else "unknown"
        looted_from = None
        if source_name and source_kind == "player":
            looted_from = self._upsert_player(source_name)

        self._events.append(
            LootEvent(
                timestamp=float(timestamp),
                looted_by=self._upsert_player(looted_by_name),
                looted_from=looted_from,
                source_name=source_name,
                source_kind=source_kind,
                item=loot.item,
                quantity=int(loot.quantity),
                is_silver=False,
                raw_event_code=int(raw_operation_code),
                raw_subtype=int(raw_operation_code),
            )
        )
        self._remove_loot_from_container(container, loot.object_id)
        if len(self._events) > self.history_limit:
            self._events = self._events[-self.history_limit :]

    def _observe_inventory_move_items(
        self,
        parameters: dict[int, object],
        *,
        timestamp: float,
        raw_operation_code: int,
    ) -> None:
        from_uuid = _normalize_uuid(parameters.get(0))
        to_uuid = _normalize_uuid(parameters.get(2))
        if not from_uuid or not to_uuid or from_uuid == to_uuid:
            return
        container = self._containers_by_uuid.get(from_uuid)
        if container is None:
            return

        object_ids = _coerce_int_list(parameters.get(4))
        quantities = _coerce_int_list(parameters.get(5))
        if not object_ids:
            return

        looted_by = self._upsert_player(self._local_looter_name())
        source_name = container.owner_name or "Loot Chest"
        source_kind = (
            _classify_source_kind(container.owner_name)
            if container.owner_name
            else "system"
        )
        looted_from = None
        if source_kind == "player":
            looted_from = self._upsert_player(source_name)

        moved_ids: list[int] = []
        for index, object_id in enumerate(object_ids):
            loot = container.items.get(object_id) or self._loot_objects.get(object_id)
            if loot is None:
                continue
            quantity = quantities[index] if index < len(quantities) else loot.quantity
            if not isinstance(quantity, int) or quantity <= 0:
                continue
            self._events.append(
                LootEvent(
                    timestamp=float(timestamp),
                    looted_by=looted_by,
                    looted_from=looted_from,
                    source_name=source_name,
                    source_kind=source_kind,
                    item=loot.item,
                    quantity=int(quantity),
                    is_silver=False,
                    raw_event_code=int(raw_operation_code),
                    raw_subtype=int(raw_operation_code),
                )
            )
            moved_ids.append(object_id)

        for object_id in moved_ids:
            self._remove_loot_from_container(container, object_id)
        if len(self._events) > self.history_limit:
            self._events = self._events[-self.history_limit :]

    def _inventory_move_blocked_by_location(self) -> bool:
        if self.location_provider is None:
            return False
        try:
            location = self.location_provider()
        except Exception:
            return False
        return _is_safe_loot_suppressed_location(location)

    def _remove_loot_from_container(self, container: LootContainer, object_id: int) -> None:
        container.items.pop(object_id, None)
        container.slot_items = {
            slot: loot
            for slot, loot in container.slot_items.items()
            if loot.object_id != object_id
        }
        container.index_items = {
            index: loot
            for index, loot in container.index_items.items()
            if loot.object_id != object_id
        }
        self._loot_objects.pop(object_id, None)

    def _observe_other_grabbed_loot(
        self,
        parameters: dict[int, object],
        *,
        timestamp: float,
        raw_event_code: int,
        raw_subtype: int,
        trusted_party_member: bool = False,
    ) -> None:
        is_silver = bool(parameters.get(3))
        looted_from_name = parameters.get(1)
        looted_by_name = parameters.get(2)
        item_num_id = parameters.get(4)
        quantity = parameters.get(5)
        if not isinstance(looted_by_name, str) or not looted_by_name:
            return
        if not self._allows_loot_player_name(looted_by_name):
            return
        if not isinstance(quantity, int) or quantity <= 0:
            return

        looted_by = self._upsert_player(looted_by_name)
        looted_from = None
        source_name = None
        source_kind = "unknown"
        item = None

        if is_silver:
            if not self.include_silver:
                return
            source_kind = "silver"
            quantity = _normalize_silver_quantity(quantity)
            if quantity <= 0:
                return
            item = LootItemRef(
                item_num_id=None,
                unique_name="SILVER",
                display_name="Silver",
            )
        else:
            if not isinstance(looted_from_name, str) or not looted_from_name:
                return
            if not isinstance(item_num_id, int) or item_num_id <= 0:
                return
            source_name = looted_from_name
            source_kind = _classify_source_kind(looted_from_name)
            if source_kind == "player":
                looted_from = self._upsert_player(looted_from_name)
            item = self._resolve_item(item_num_id)

        self._events.append(
            LootEvent(
                timestamp=float(timestamp),
                looted_by=looted_by,
                looted_from=looted_from,
                source_name=source_name,
                source_kind=source_kind,
                item=item,
                quantity=int(quantity),
                is_silver=is_silver,
                raw_event_code=int(raw_event_code),
                raw_subtype=int(raw_subtype),
            )
        )
        if len(self._events) > self.history_limit:
            self._events = self._events[-self.history_limit :]

    def _allows_loot_player_name(self, player_name: str) -> bool:
        if self.party_registry is None:
            return True
        self_name = self.party_registry.self_name()
        if self_name and player_name == self_name:
            return True
        party_names = self.party_registry.snapshot_names()
        if party_names:
            return player_name in party_names
        return False

    def silver_total(self) -> int:
        return sum(int(event.quantity) for event in self._events if event.is_silver)

    def silver_per_hour(self) -> float:
        timestamps = [event.timestamp for event in self._events if event.is_silver]
        if len(timestamps) < 2:
            return 0.0
        elapsed = max(timestamps) - min(timestamps)
        if elapsed <= 0:
            return 0.0
        return self.silver_total() / (elapsed / 3600.0)

    def _resolve_item(self, item_num_id: int) -> LootItemRef:
        unique_name = None
        display_name = None
        if self.item_resolver is not None:
            unique_name = self.item_resolver.index_to_unique.get(item_num_id)
            display_name = self.item_resolver.index_to_name.get(item_num_id)
        if not isinstance(display_name, str) or not display_name:
            display_name = unique_name or f"Unknown item #{item_num_id}"
        return LootItemRef(
            item_num_id=int(item_num_id),
            unique_name=unique_name,
            display_name=display_name,
        )

    def _local_looter_name(self) -> str:
        if self.party_registry is not None:
            self_name = self.party_registry.self_name()
            if self_name:
                self._rename_local_looter(self_name)
                return self_name
        return "You"

    def _rename_local_looter(self, player_name: str) -> None:
        if "You" not in self._players:
            return
        looted_by = self._upsert_player(player_name)
        self._events = [
            replace(event, looted_by=looted_by)
            if event.looted_by.player_name == "You"
            else event
            for event in self._events
        ]
        self._players.pop("You", None)

    def _upsert_player(
        self,
        player_name: str,
        *,
        guild_name: str | None = None,
        alliance_name: str | None = None,
    ) -> LootPlayer:
        current = self._players.get(player_name)
        if current is None:
            current = LootPlayer(
                player_name=player_name,
                guild_name=guild_name,
                alliance_name=alliance_name,
            )
        else:
            current = LootPlayer(
                player_name=player_name,
                guild_name=guild_name or current.guild_name,
                alliance_name=alliance_name or current.alliance_name,
            )
        self._players[player_name] = current
        return current


def _coerce_int_list(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    out: list[int] = []
    for item in value:
        if isinstance(item, int) and item > 0:
            out.append(item)
    return out


def _coerce_slot(value: object) -> int | None:
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _first_slot(*values: object) -> int | None:
    for value in values:
        slot = _coerce_slot(value)
        if slot is not None:
            return slot
    return None


def _map_slot_items(
    inventory_ids: list[int],
    items: dict[int, LootObject],
    slot_base: int | None,
) -> dict[int, LootObject]:
    slot_items: dict[int, LootObject] = {}
    for index, object_id in enumerate(inventory_ids):
        loot = items.get(object_id)
        if loot is None:
            continue
        if slot_base is not None:
            slot_items[slot_base + index] = loot
        else:
            slot_items[index] = loot
    return slot_items


def _map_index_items(
    inventory_ids: list[int],
    items: dict[int, LootObject],
) -> dict[int, LootObject]:
    index_items: dict[int, LootObject] = {}
    for index, object_id in enumerate(inventory_ids):
        loot = items.get(object_id)
        if loot is not None:
            index_items[index] = loot
    return index_items


def _select_container_loot(
    container: LootContainer, slot: int | None
) -> LootObject | None:
    if slot is not None:
        loot = container.slot_items.get(slot)
        if loot is not None:
            return loot
        loot = container.index_items.get(slot)
        if loot is not None:
            return loot
    if len(container.items) == 1:
        return next(iter(container.items.values()))
    return None


def _normalize_uuid(value: object) -> str | None:
    raw = _coerce_uuid_bytes(value)
    if raw is None or len(raw) != 16:
        return None
    hex_value = raw.hex()
    return (
        f"{hex_value[0:8]}-"
        f"{hex_value[8:12]}-"
        f"{hex_value[12:16]}-"
        f"{hex_value[16:20]}-"
        f"{hex_value[20:32]}"
    )


def _coerce_uuid_bytes(value: object) -> bytes | None:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, list) and len(value) == 16:
        out = bytearray()
        for item in value:
            if not isinstance(item, int) or item < 0 or item > 255:
                return None
            out.append(item)
        return bytes(out)
    return None


def _classify_source_kind(source_name: str) -> str:
    if source_name.startswith("@MOB"):
        return "mob"
    if source_name.startswith("@"):
        return "system"
    return "player"


def _normalize_silver_quantity(quantity: int) -> int:
    if quantity >= SILVER_FIXPOINT_FACTOR:
        return int(quantity / SILVER_FIXPOINT_FACTOR)
    return int(quantity)


def _is_safe_loot_suppressed_location(location: str | None) -> bool:
    normalized = str(location or "").strip().lower()
    if not normalized:
        return False
    safe_fragments = {
        "thetford",
        "lymhurst",
        "bridgewatch",
        "martlock",
        "fort sterling",
        "caerleon",
        "brecilien",
        "market",
        "hideout",
        "smuggler",
        "island",
        "bank",
        "city",
    }
    return any(fragment in normalized for fragment in safe_fragments)
