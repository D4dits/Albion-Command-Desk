from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Any, Iterable


ENV_INDEXED_ITEMS = "ALBION_DPS_INDEXED_ITEMS"
ENV_ITEMS_JSON = "ALBION_DPS_ITEMS_JSON"
ENV_CATEGORY_MAPPING = "ALBION_DPS_ITEM_CATEGORY_MAPPING"
ENV_ICON_BASE = "ALBION_DPS_ICON_BASE"

DEFAULT_INDEXED_PATHS = (
    Path("data/indexedItems.json"),
    Path("data/indexed_items.json"),
    Path("indexedItems.json"),
)
DEFAULT_ITEMS_PATHS = (
    Path("data/items.json"),
    Path("items.json"),
)
DEFAULT_CATEGORY_PATHS = (
    Path("data/item_category_mapping.json"),
    Path("data/item_category_mapping.py"),
    Path("item_category_mapping.json"),
    Path("item_category_mapping.py"),
)
DEFAULT_ICON_BASE = "https://render.albiononline.com/v1/item"
DEFAULT_ICON_SIZE = 64

ROLE_BY_SUBCATEGORY = {
    "holystaff": "heal",
    "naturestaff": "heal",
    "mace": "tank",
    "hammer": "tank",
    "quarterstaff": "tank",
    "arcanestaff": "tank",
}

SUBCATEGORY_PATTERNS = [
    ("HOLYSTAFF", "holystaff"),
    ("NATURESTAFF", "naturestaff"),
    ("ARCANESTAFF", "arcanestaff"),
    ("MACE", "mace"),
    ("HAMMER", "hammer"),
    ("QUARTERSTAFF", "quarterstaff"),
    ("SPEAR", "spear"),
    ("SWORD", "sword"),
    ("BOW", "bow"),
    ("CROSSBOW", "crossbow"),
    ("FIRESTAFF", "firestaff"),
    ("FROSTSTAFF", "froststaff"),
    ("CURSESTAFF", "cursestaff"),
    ("DAGGER", "dagger"),
    ("AXE", "axe"),
    ("KNUCKLES", "knuckles"),
    ("SHAPESHIFTERSTAFF", "shapeshifterstaff"),
]
WEAPON_CATEGORIES = {subcategory for _, subcategory in SUBCATEGORY_PATTERNS} | set(
    ROLE_BY_SUBCATEGORY.keys()
)


@dataclass
class ItemResolver:
    index_to_unique: dict[int, str] = field(default_factory=dict)
    index_to_name: dict[int, str] = field(default_factory=dict)
    unique_to_subcategory: dict[str, str] = field(default_factory=dict)
    unique_to_category: dict[str, str] = field(default_factory=dict)

    def role_for_items(self, item_ids: Iterable[int]) -> str | None:
        unique = self._mainhand_unique(item_ids)
        if not unique:
            return None
        subcategory = self.unique_to_subcategory.get(unique)
        if not subcategory:
            subcategory = self.unique_to_category.get(unique)
        if not subcategory:
            subcategory = _infer_subcategory_from_unique(unique)
        if not subcategory:
            return None
        subcategory = subcategory.lower()
        if subcategory in ROLE_BY_SUBCATEGORY:
            return ROLE_BY_SUBCATEGORY[subcategory]
        if subcategory in WEAPON_CATEGORIES:
            return "dps"
        return None

    def subcategory_for_items(self, item_ids: Iterable[int]) -> str | None:
        unique = self._mainhand_unique(item_ids)
        if not unique:
            return None
        subcategory = self.unique_to_subcategory.get(unique)
        if not subcategory:
            subcategory = self.unique_to_category.get(unique)
        if not subcategory:
            subcategory = _infer_subcategory_from_unique(unique)
        if not subcategory:
            return None
        return subcategory.lower()

    def weapon_category_for_items(self, item_ids: Iterable[int]) -> str | None:
        subcategory = self.subcategory_for_items(item_ids)
        if not subcategory:
            return None
        if subcategory in WEAPON_CATEGORIES:
            return subcategory
        return None

    def weapon_info_for_items(self, item_ids: Iterable[int]) -> "WeaponInfo | None":
        for item_id in item_ids:
            if not isinstance(item_id, int) or item_id <= 0:
                continue
            unique = self.index_to_unique.get(item_id)
            if not unique:
                continue
            name = self.index_to_name.get(item_id)
            tier, enchant = _parse_tier_enchant(unique)
            icon = _build_icon_url(unique)
            return WeaponInfo(
                unique=unique,
                name=name,
                tier=tier,
                enchant=enchant,
                icon_url=icon,
            )
        return None

    def _mainhand_unique(self, item_ids: Iterable[int]) -> str | None:
        for item_id in item_ids:
            if not isinstance(item_id, int) or item_id <= 0:
                continue
            unique = self.index_to_unique.get(item_id)
            if unique:
                return unique
        return None


def load_item_resolver(
    *,
    indexed_path: str | Path | None = None,
    items_path: str | Path | None = None,
    category_path: str | Path | None = None,
    logger: logging.Logger | None = None,
) -> ItemResolver:
    resolver = ItemResolver()
    logger = logger or logging.getLogger(__name__)

    indexed = _resolve_path(indexed_path, ENV_INDEXED_ITEMS, DEFAULT_INDEXED_PATHS)
    if indexed:
        index_map, name_map = _load_indexed_items(indexed, logger=logger)
        resolver.index_to_unique = index_map
        resolver.index_to_name = name_map
    else:
        logger.debug("No indexed items database found (indexedItems.json).")

    items = _resolve_path(items_path, ENV_ITEMS_JSON, DEFAULT_ITEMS_PATHS)
    if items:
        resolver.unique_to_subcategory = _load_items(items, logger=logger)
    else:
        logger.debug("No items catalog found (items.json). Using name heuristics.")

    category = _resolve_path(category_path, ENV_CATEGORY_MAPPING, DEFAULT_CATEGORY_PATHS)
    if category:
        resolver.unique_to_category = _load_category_mapping(category, logger=logger)
    else:
        logger.debug("No item category mapping found (item_category_mapping).")

    return resolver


def _resolve_path(
    provided: str | Path | None,
    env_key: str,
    defaults: Iterable[Path],
) -> Path | None:
    if provided:
        path = Path(provided)
        return path if path.exists() else None
    env_val = os.environ.get(env_key)
    if env_val:
        path = Path(env_val)
        return path if path.exists() else None
    for candidate in defaults:
        if candidate.exists():
            return candidate
    return None


def _load_indexed_items(
    path: Path, *, logger: logging.Logger
) -> tuple[dict[int, str], dict[int, str]]:
    data = _load_json(path, logger=logger)
    index_map: dict[int, str] = {}
    name_map: dict[int, str] = {}
    for record in _iter_records(data):
        if not isinstance(record, dict):
            continue
        lower = {str(k).lower(): v for k, v in record.items()}
        unique = lower.get("uniquename")
        index = lower.get("index")
        name = _pick_localized_name(lower.get("localizednames") or lower.get("localizedname"))
        if isinstance(unique, str) and unique and index is not None:
            try:
                index_value = int(index)
            except (TypeError, ValueError):
                continue
            index_map[index_value] = unique
            if isinstance(name, str) and name:
                name_map[index_value] = name
    if not index_map:
        logger.warning("Indexed items file loaded but produced no entries: %s", path)
    return index_map, name_map


def _load_items(path: Path, *, logger: logging.Logger) -> dict[str, str]:
    data = _load_json(path, logger=logger)
    mapping: dict[str, str] = {}
    for record in _iter_records(data):
        if not isinstance(record, dict):
            continue
        lower = {str(k).lower(): v for k, v in record.items()}
        unique = lower.get("uniquename")
        if not isinstance(unique, str) or not unique:
            continue
        subcategory = None
        for key in ("shopsubcategory1", "shopsubcategory_1", "shopsubcategory"):
            value = lower.get(key)
            if isinstance(value, str) and value:
                subcategory = value
                break
        if isinstance(subcategory, str) and subcategory:
            mapping[unique] = subcategory.lower()
    if not mapping:
        logger.warning("Items catalog loaded but produced no entries: %s", path)
    return mapping


def _load_category_mapping(path: Path, *, logger: logging.Logger) -> dict[str, str]:
    if path.suffix.lower() == ".py":
        return _load_python_mapping(path, logger=logger)
    data = _load_json(path, logger=logger)
    mapping: dict[str, str] = {}
    if isinstance(data, dict):
        for unique, category in data.items():
            if isinstance(unique, str) and isinstance(category, str) and category:
                mapping[unique] = category.lower()
    return mapping


def _iter_records(data: Any) -> Iterable[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        items = data.get("items") or data.get("Items")
        if isinstance(items, list):
            return items
        # If dict is keyed by UniqueName, convert to records.
        records: list[dict[str, Any]] = []
        for key, value in data.items():
            if isinstance(value, dict):
                record = dict(value)
                record.setdefault("UniqueName", key)
                records.append(record)
        return records
    return []


def _load_json(path: Path, *, logger: logging.Logger) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed to load JSON: %s", path)
        return []


def _load_python_mapping(path: Path, *, logger: logging.Logger) -> dict[str, str]:
    import ast

    try:
        source = path.read_text(encoding="utf-8")
        module = ast.parse(source)
    except Exception:
        logger.exception("Failed to parse Python mapping: %s", path)
        return {}
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "mapping":
                    try:
                        mapping_obj = ast.literal_eval(node.value)
                    except Exception:
                        logger.exception("Failed to eval mapping literal: %s", path)
                        return {}
                    if isinstance(mapping_obj, dict):
                        return {
                            unique: category.lower()
                            for unique, category in mapping_obj.items()
                            if isinstance(unique, str)
                            and isinstance(category, str)
                            and category
                        }
    logger.warning("Python mapping does not define `mapping`: %s", path)
    return {}


def _pick_localized_name(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, dict):
        for key in ("en-us", "en-gb", "en"):
            entry = value.get(key) or value.get(key.upper())
            if isinstance(entry, str) and entry:
                return entry
        for entry in value.values():
            if isinstance(entry, str) and entry:
                return entry
    return None


_TIER_RE = re.compile(r"^T(\d+)_")


def _parse_tier_enchant(unique: str) -> tuple[int | None, int | None]:
    if not unique:
        return None, None
    base = unique
    enchant = 0
    if "@" in unique:
        base, suffix = unique.split("@", 1)
        try:
            enchant = int(suffix)
        except ValueError:
            enchant = 0
    match = _TIER_RE.match(base)
    if not match:
        return None, enchant
    try:
        tier = int(match.group(1))
    except ValueError:
        return None, enchant
    return tier, enchant


def _build_icon_url(unique: str) -> str | None:
    if not unique:
        return None
    base = os.environ.get(ENV_ICON_BASE, DEFAULT_ICON_BASE).strip()
    if not base:
        return None
    base = base.rstrip("/")
    return f"{base}/{unique}?size={DEFAULT_ICON_SIZE}"


@dataclass(frozen=True)
class WeaponInfo:
    unique: str
    name: str | None
    tier: int | None
    enchant: int | None
    icon_url: str | None


def _infer_subcategory_from_unique(unique: str) -> str | None:
    if not unique:
        return None
    upper = unique.upper()
    for needle, subcategory in SUBCATEGORY_PATTERNS:
        if needle in upper:
            return subcategory
    return None
