from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LootPlayer:
    player_name: str
    guild_name: str | None = None
    alliance_name: str | None = None


@dataclass(frozen=True)
class LootItemRef:
    item_num_id: int | None
    unique_name: str | None
    display_name: str


@dataclass(frozen=True)
class LootEvent:
    timestamp: float
    looted_by: LootPlayer
    looted_from: LootPlayer | None
    source_name: str | None
    source_kind: str
    item: LootItemRef | None
    quantity: int
    is_silver: bool
    raw_event_code: int
    raw_subtype: int


@dataclass
class LootObject:
    object_id: int
    item_num_id: int
    quantity: int
    item: LootItemRef
    owner_name: str | None = None


@dataclass
class LootContainer:
    container_id: int
    container_uuid: str | None = None
    owner_name: str | None = None
    owner_kind: str = "unknown"
    items: dict[int, LootObject] = field(default_factory=dict)
    slot_items: dict[int, LootObject] = field(default_factory=dict)
    index_items: dict[int, LootObject] = field(default_factory=dict)
