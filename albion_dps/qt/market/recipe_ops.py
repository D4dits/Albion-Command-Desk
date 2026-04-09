from __future__ import annotations

import re

from albion_dps.market.models import ItemRef, Recipe

_TIER_PREFIX_RE = re.compile(r"^T(?P<tier>\d+)_(?P<rest>.+)$", re.IGNORECASE)
_LEVEL_SUFFIX_RE = re.compile(r"_LEVEL\d+$", re.IGNORECASE)

_ALLOWED_PLAN_STATIONS: set[str] = {
    "axe",
    "arcanestaff",
    "armors",
    "bag",
    "battle mount",
    "basemounts",
    "bow",
    "cape",
    "capes",
    "cloth armor",
    "cloth helmet",
    "cloth shoes",
    "crossbow",
    "cursestaff",
    "dagger",
    "firestaff",
    "food",
    "froststaff",
    "gatherergear",
    "hammer",
    "head",
    "holystaff",
    "hunter",
    "knuckles",
    "leather armor",
    "leather helmet",
    "leather shoes",
    "mace",
    "mounts",
    "naturestaff",
    "offhand",
    "offhands",
    "plate armor",
    "plate helmet",
    "plate shoes",
    "potion",
    "quarterstaff",
    "shapeshifterstaff",
    "shieldtype",
    "shoes",
    "spear",
    "sword",
    "tools",
}
_ITEM_ID_WORD_ALIASES: dict[str, str] = {
    "ARTEFACT": "Artifact",
    "METALBAR": "Metal Bar",
    "OFFHAND": "Off Hand",
    "QUARTERSTAFF": "Quarterstaff",
    "SHAPESHIFTERSTAFF": "Shapeshifter Staff",
    "ARCANESTAFF": "Arcane Staff",
    "CURSEDSTAFF": "Cursed Staff",
    "FIRESTAFF": "Fire Staff",
    "FROSTSTAFF": "Frost Staff",
    "HOLYSTAFF": "Holy Staff",
    "NATURESTAFF": "Nature Staff",
}


def friendly_item_label(display_name: str, item_id: str) -> str:
    name = str(display_name or "").strip()
    if name and name.upper() != str(item_id or "").strip().upper():
        return name
    fallback = humanize_item_id(item_id)
    return fallback or str(item_id or "").strip()


def recipe_identity(recipe: Recipe) -> str:
    identity = str(recipe.recipe_id or "").strip()
    if identity:
        return identity
    return str(recipe.item.unique_name or "").strip()


def recipe_output_item(recipe: Recipe) -> ItemRef:
    if recipe.outputs:
        return recipe.outputs[0].item
    return recipe.item


def recipe_display_label(recipe: Recipe) -> str:
    output_item = recipe_output_item(recipe)
    label = friendly_item_label(output_item.display_name, output_item.unique_name)
    variant_label = str(recipe.variant_label or "").strip()
    if variant_label:
        return f"{label} [{variant_label}]"
    return label


def item_family_key(item_id: str) -> str:
    base = str(item_id or "").strip().upper()
    if not base:
        return ""
    if "@" in base:
        base = base.rsplit("@", 1)[0]
    base = _LEVEL_SUFFIX_RE.sub("", base)
    tier_match = _TIER_PREFIX_RE.match(base)
    if tier_match is not None:
        base = tier_match.group("rest").upper()
    return base


def is_recipe_plan_candidate(recipe: Recipe) -> bool:
    output_item = recipe_output_item(recipe)
    item_id = str(output_item.unique_name or recipe.item.unique_name or "").strip().upper()
    if not item_id:
        return False
    if item_id.startswith("UNIQUE_"):
        return False
    if not recipe.components:
        return False
    if not recipe.outputs:
        return False
    if bool(recipe.uses_crystallized) and "_ARTEFACT_" not in item_id:
        return True
    if "_ARTEFACT_" in item_id or "_TOKEN_" in item_id:
        return False
    station = str(recipe.station or "").strip().lower()
    if not station:
        return False
    if station.startswith("accessoires capes"):
        return True
    return station in _ALLOWED_PLAN_STATIONS


def humanize_item_id(item_id: str) -> str:
    raw = str(item_id or "").strip()
    if not raw:
        return ""

    enchant: int | None = None
    base = raw
    if "@" in base:
        stem, enchant_raw = base.rsplit("@", 1)
        base = stem
        try:
            enchant = int(enchant_raw)
        except ValueError:
            enchant = None

    base = _LEVEL_SUFFIX_RE.sub("", base)
    tier: int | None = None
    tier_match = _TIER_PREFIX_RE.match(base)
    if tier_match is not None:
        tier = int(tier_match.group("tier"))
        base = tier_match.group("rest")

    words: list[str] = []
    for token in base.split("_"):
        cleaned = token.strip()
        if not cleaned:
            continue
        upper = cleaned.upper()
        if upper in {"MAIN", "2H"}:
            continue
        mapped = _ITEM_ID_WORD_ALIASES.get(upper)
        if mapped is not None:
            words.append(mapped)
            continue
        if len(upper) <= 3 and upper.isalpha():
            words.append(upper)
            continue
        words.append(cleaned.replace("-", " ").title())

    item_name = " ".join(words).strip() or raw
    if tier is None:
        return item_name
    if enchant is not None and enchant > 0:
        return f"{item_name} {tier}.{enchant}"
    return f"{item_name} T{tier}"


def item_id_candidates(item_id: str) -> tuple[str, ...]:
    base = str(item_id or "").strip()
    if not base:
        return ()
    out: list[str] = [base]

    core = base
    had_at = "@" in base
    enchant: int | None = None
    if "@" in core:
        maybe_core, maybe_enchant = core.rsplit("@", 1)
        try:
            enchant = int(maybe_enchant)
            core = maybe_core
        except ValueError:
            pass

    stem = core
    level: int | None = None
    level_match = _LEVEL_SUFFIX_RE.search(core)
    had_level = level_match is not None
    if level_match is not None:
        stem = core[: level_match.start()]
        suffix = level_match.group(0)
        try:
            level = int(suffix.rsplit("LEVEL", 1)[1])
        except (IndexError, ValueError):
            level = None

    if enchant is None and level is not None:
        enchant = level
    if level is None and enchant is not None:
        level = enchant

    if level is not None:
        out.append(f"{stem}_LEVEL{level}")
    if enchant is not None and (had_at or not had_level):
        out.append(f"{stem}@{enchant}")
    if level is not None and enchant is not None:
        out.append(f"{stem}_LEVEL{level}@{enchant}")
    if not had_level and enchant is None:
        out.append(stem)
    seen: set[str] = set()
    ordered: list[str] = []
    for value in out:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


def item_id_query_candidates(item_id: str) -> tuple[str, ...]:
    base = str(item_id or "").strip()
    if not base:
        return ()

    out: list[str] = [base]

    core = base
    had_at = "@" in base
    enchant: int | None = None
    if "@" in core:
        maybe_core, maybe_enchant = core.rsplit("@", 1)
        try:
            enchant = int(maybe_enchant)
            core = maybe_core
        except ValueError:
            pass

    stem = core
    level: int | None = None
    level_match = _LEVEL_SUFFIX_RE.search(core)
    had_level = level_match is not None
    if level_match is not None:
        stem = core[: level_match.start()]
        suffix = level_match.group(0)
        try:
            level = int(suffix.rsplit("LEVEL", 1)[1])
        except (IndexError, ValueError):
            level = None

    if enchant is None and level is not None:
        enchant = level
    if level is None and enchant is not None:
        level = enchant

    if level is not None:
        out.append(f"{stem}_LEVEL{level}")
    if enchant is not None and (had_at or not had_level):
        out.append(f"{stem}@{enchant}")
    if level is not None and enchant is not None:
        out.append(f"{stem}_LEVEL{level}@{enchant}")
    if not had_level and enchant is None:
        out.append(stem)

    seen: set[str] = set()
    ordered: list[str] = []
    for value in out:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


__all__ = [
    "friendly_item_label",
    "humanize_item_id",
    "is_recipe_plan_candidate",
    "item_family_key",
    "item_id_candidates",
    "item_id_query_candidates",
    "recipe_display_label",
    "recipe_identity",
    "recipe_output_item",
]
