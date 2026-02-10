from __future__ import annotations

from albion_dps.market.recipes_from_items import extract_recipes_from_items_payload


def test_extract_recipes_from_items_payload_builds_normalized_rows() -> None:
    payload = {
        "items": {
            "weapon": [
                {
                    "@uniquename": "T4_MAIN_SWORD",
                    "@tier": "4",
                    "@enchantmentlevel": "0",
                    "@itemvalue": "3200",
                    "@shopcategory": "weapons",
                    "@shopsubcategory1": "sword",
                    "@craftingcategory": "sword",
                    "@unlockedtocraft": "true",
                    "craftingrequirements": {
                        "@craftingfocus": "200",
                        "@amountcrafted": "1",
                        "craftresource": [
                            {"@uniquename": "T4_METALBAR", "@count": "16", "@itemvalue": "300"},
                            {"@uniquename": "T4_PLANKS", "@count": "8", "@itemvalue": "240"},
                        ],
                    },
                }
            ]
        }
    }

    rows, report = extract_recipes_from_items_payload(
        payload=payload,
        display_names={
            "T4_MAIN_SWORD": "Broadsword",
            "T4_METALBAR": "Metal Bar",
            "T4_PLANKS": "Planks",
        },
        include_locked=True,
    )

    assert report.recipes_out == 1
    assert rows[0]["item"]["unique_name"] == "T4_MAIN_SWORD"
    assert rows[0]["item"]["display_name"] == "Broadsword"
    assert rows[0]["item"]["item_value"] == 3200
    assert rows[0]["focus_per_craft"] == 200
    assert rows[0]["outputs"][0]["quantity"] == 1.0
    assert rows[0]["components"][0]["item"]["item_value"] == 300
    assert rows[0]["components"][1]["item"]["item_value"] == 240
    component_ids = {x["item"]["unique_name"] for x in rows[0]["components"]}
    assert component_ids == {"T4_METALBAR", "T4_PLANKS"}


def test_extract_recipes_from_items_payload_can_exclude_locked_and_pick_better_requirement() -> None:
    payload = {
        "items": {
            "equipmentitem": [
                {
                    "@uniquename": "T4_BAG",
                    "@tier": "4",
                    "@enchantmentlevel": "0",
                    "@shopcategory": "armor",
                    "@shopsubcategory1": "bag",
                    "@unlockedtocraft": "true",
                    "craftingrequirements": [
                        {
                            "@craftingfocus": "200",
                            "@amountcrafted": "1",
                            "craftresource": [
                                {"@uniquename": "T4_LEATHER_LEVEL1", "@count": "10"},
                                {"@uniquename": "T4_CLOTH", "@count": "5"},
                            ],
                        },
                        {
                            "@craftingfocus": "180",
                            "@amountcrafted": "1",
                            "craftresource": [
                                {"@uniquename": "T4_LEATHER", "@count": "8"},
                                {"@uniquename": "T4_CLOTH", "@count": "4"},
                            ],
                        },
                    ],
                },
                {
                    "@uniquename": "T4_DEBUG_LOCKED",
                    "@tier": "4",
                    "@shopcategory": "armor",
                    "@shopsubcategory1": "bag",
                    "@unlockedtocraft": "false",
                    "craftingrequirements": {
                        "@craftingfocus": "0",
                        "craftresource": [
                            {"@uniquename": "T4_CLOTH", "@count": "1"},
                        ],
                    },
                },
            ]
        }
    }

    rows, report = extract_recipes_from_items_payload(
        payload=payload,
        display_names={},
        include_locked=False,
    )

    assert report.recipes_out == 1
    assert rows[0]["item"]["unique_name"] == "T4_BAG"
    assert rows[0]["focus_per_craft"] == 180
    comp = rows[0]["components"]
    assert comp[0]["item"]["unique_name"] == "T4_LEATHER"
    assert comp[1]["item"]["unique_name"] == "T4_CLOTH"


def test_extract_recipes_from_items_payload_adds_enchantment_variants() -> None:
    payload = {
        "items": {
            "weapon": [
                {
                    "@uniquename": "T5_2H_BOW",
                    "@tier": "5",
                    "@enchantmentlevel": "0",
                    "@craftingcategory": "bow",
                    "@unlockedtocraft": "true",
                    "craftingrequirements": {
                        "@craftingfocus": "3000",
                        "@amountcrafted": "1",
                        "craftresource": [
                            {"@uniquename": "T5_PLANKS", "@count": "32"},
                        ],
                    },
                    "enchantments": {
                        "enchantment": [
                            {
                                "@enchantmentlevel": "1",
                                "craftingrequirements": {
                                    "@craftingfocus": "5200",
                                    "@amountcrafted": "1",
                                    "craftresource": [
                                        {"@uniquename": "T5_PLANKS_LEVEL1", "@count": "32"},
                                    ],
                                },
                            },
                            {
                                "@enchantmentlevel": "2",
                                "craftingrequirements": {
                                    "@craftingfocus": "9000",
                                    "@amountcrafted": "1",
                                    "craftresource": [
                                        {"@uniquename": "T5_PLANKS_LEVEL2", "@count": "32"},
                                    ],
                                },
                            },
                        ]
                    },
                }
            ]
        }
    }

    rows, report = extract_recipes_from_items_payload(
        payload=payload,
        display_names={"T5_2H_BOW": "War Bow"},
        include_locked=True,
    )

    assert report.recipes_out == 3
    ids = {row["item"]["unique_name"] for row in rows}
    assert "T5_2H_BOW" in ids
    assert "T5_2H_BOW@1" in ids
    assert "T5_2H_BOW@2" in ids

    row_1 = [row for row in rows if row["item"]["unique_name"] == "T5_2H_BOW@1"][0]
    assert row_1["item"]["enchantment"] == 1
    assert row_1["focus_per_craft"] == 5200


def test_extract_recipes_marks_artifact_components_as_non_returnable() -> None:
    payload = {
        "items": {
            "weapon": [
                {
                    "@uniquename": "T4_MAIN_SWORD",
                    "@tier": "4",
                    "@enchantmentlevel": "0",
                    "@craftingcategory": "sword",
                    "@unlockedtocraft": "true",
                    "craftingrequirements": {
                        "@craftingfocus": "200",
                        "@amountcrafted": "1",
                        "craftresource": [
                            {"@uniquename": "T4_METALBAR", "@count": "16"},
                            {"@uniquename": "T4_ARTEFACT_2H_KEEPER_SWORD", "@count": "1"},
                        ],
                    },
                }
            ]
        }
    }
    rows, report = extract_recipes_from_items_payload(payload=payload, display_names={}, include_locked=True)
    assert report.recipes_out == 1
    components = rows[0]["components"]
    returnable_by_id = {comp["item"]["unique_name"]: bool(comp["returnable"]) for comp in components}
    assert returnable_by_id["T4_METALBAR"] is True
    assert returnable_by_id["T4_ARTEFACT_2H_KEEPER_SWORD"] is False
