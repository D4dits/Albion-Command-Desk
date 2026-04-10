from __future__ import annotations

from dataclasses import dataclass, field

from albion_dps.domain.item_resolver import ItemResolver
from albion_dps.domain.loot_types import (
    LootContainer,
    LootEvent,
    LootItemRef,
    LootObject,
    LootPlayer,
)
from albion_dps.models import PhotonMessage, RawPacket
from albion_dps.protocol.protocol16 import Protocol16Error, decode_event_data

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

LOOT_OBJECT_SUBTYPES = {
    EV_NEW_SIMPLE_ITEM,
    EV_NEW_EQUIPMENT_ITEM,
    EV_NEW_SIEGE_BANNER_ITEM,
}


@dataclass
class LootTracker:
    item_resolver: ItemResolver | None = None
    include_silver: bool = False
    history_limit: int = 500
    _players: dict[str, LootPlayer] = field(default_factory=dict)
    _loot_objects: dict[int, LootObject] = field(default_factory=dict)
    _containers_by_id: dict[int, LootContainer] = field(default_factory=dict)
    _containers_by_uuid: dict[str, LootContainer] = field(default_factory=dict)
    _events: list[LootEvent] = field(default_factory=list)

    def observe(self, message: PhotonMessage, packet: RawPacket | None = None) -> None:
        if message.event_code is None or message.event_code != LOOT_EVENT_CODE:
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
        container.items = next_items

    def _observe_detach_item_container(self, parameters: dict[int, object]) -> None:
        uuid_text = _normalize_uuid(parameters.get(0))
        if not uuid_text:
            return
        container = self._containers_by_uuid.pop(uuid_text, None)
        if container is None:
            return
        self._containers_by_id.pop(container.container_id, None)

    def _observe_other_grabbed_loot(
        self,
        parameters: dict[int, object],
        *,
        timestamp: float,
        raw_event_code: int,
        raw_subtype: int,
    ) -> None:
        is_silver = bool(parameters.get(3))
        looted_from_name = parameters.get(1)
        looted_by_name = parameters.get(2)
        item_num_id = parameters.get(4)
        quantity = parameters.get(5)
        if not isinstance(looted_by_name, str) or not looted_by_name:
            return
        if not isinstance(quantity, int) or quantity <= 0:
            return

        looted_by = self._upsert_player(looted_by_name)
        looted_from = None
        item = None

        if is_silver:
            if not self.include_silver:
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
            looted_from = self._upsert_player(looted_from_name)
            item = self._resolve_item(item_num_id)

        self._events.append(
            LootEvent(
                timestamp=float(timestamp),
                looted_by=looted_by,
                looted_from=looted_from,
                item=item,
                quantity=int(quantity),
                is_silver=is_silver,
                raw_event_code=int(raw_event_code),
                raw_subtype=int(raw_subtype),
            )
        )
        if len(self._events) > self.history_limit:
            self._events = self._events[-self.history_limit :]

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
