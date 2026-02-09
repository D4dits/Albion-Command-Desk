from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from albion_dps.market.migration import convert_legacy_recipe_rows, migrate_recipe_file


def test_convert_legacy_recipe_rows_normalizes_shape() -> None:
    rows = [
        {
            "item_unique_name": "T4_MAIN_SWORD",
            "display_name": "Broadsword",
            "tier": 4,
            "station": "Warrior Forge",
            "inputs": [
                {
                    "item_unique_name": "T4_METALBAR",
                    "display_name": "Metal Bar",
                    "quantity": 16,
                    "tier": 4,
                }
            ],
        }
    ]
    converted = convert_legacy_recipe_rows(rows)
    assert len(converted) == 1
    assert converted[0]["item"]["unique_name"] == "T4_MAIN_SWORD"
    assert converted[0]["components"][0]["item"]["unique_name"] == "T4_METALBAR"
    assert converted[0]["outputs"][0]["item"]["unique_name"] == "T4_MAIN_SWORD"


def test_migrate_recipe_file_writes_converted_json() -> None:
    tmp_dir = Path(f"tmp_market_migration_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        src = tmp_dir / "legacy.json"
        dst = tmp_dir / "converted.json"
        src.write_text(
            json.dumps(
                [
                    {
                        "item_unique_name": "T4_BAG",
                        "display_name": "Bag",
                        "tier": 4,
                        "inputs": [
                            {"item_unique_name": "T4_CLOTH", "quantity": 8},
                            {"item_unique_name": "T4_LEATHER", "quantity": 16},
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )
        count = migrate_recipe_file(src, dst)
        payload = json.loads(dst.read_text(encoding="utf-8"))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert count == 1
    assert isinstance(payload, list)
    assert payload[0]["item"]["unique_name"] == "T4_BAG"
