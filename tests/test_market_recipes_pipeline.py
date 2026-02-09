from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from albion_dps.market.recipes_pipeline import build_recipes_dataset


def test_build_recipes_dataset_merges_legacy_and_normalized() -> None:
    tmp_dir = Path(f"tmp_market_recipes_pipeline_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        legacy_path = tmp_dir / "legacy.json"
        normalized_path = tmp_dir / "normalized.json"
        output_path = tmp_dir / "out.json"

        legacy_payload = [
            {
                "item_unique_name": "T4_MAIN_SWORD",
                "display_name": "Broadsword",
                "tier": 4,
                "enchantment": 0,
                "station": "Warrior Forge",
                "components": [
                    {"item_unique_name": "T4_METALBAR", "quantity": 16},
                    {"item_unique_name": "T4_PLANKS", "quantity": 8},
                ],
                "outputs": [{"item_unique_name": "T4_MAIN_SWORD", "quantity": 1}],
            }
        ]
        normalized_payload = [
            {
                "item": {
                    "unique_name": "T4_BAG",
                    "display_name": "Bag",
                    "tier": 4,
                    "enchantment": 0,
                },
                "station": "Toolmaker",
                "city_bonus": "Fort Sterling",
                "focus_per_craft": 180,
                "components": [
                    {"item": {"unique_name": "T4_LEATHER", "display_name": "Leather", "tier": 4, "enchantment": 0}, "quantity": 16.0},
                    {"item": {"unique_name": "T4_CLOTH", "display_name": "Cloth", "tier": 4, "enchantment": 0}, "quantity": 8.0},
                ],
                "outputs": [
                    {"item": {"unique_name": "T4_BAG", "display_name": "Bag", "tier": 4, "enchantment": 0}, "quantity": 1.0}
                ],
            }
        ]

        legacy_path.write_text(json.dumps(legacy_payload), encoding="utf-8")
        normalized_path.write_text(json.dumps(normalized_payload), encoding="utf-8")

        report = build_recipes_dataset(
            input_paths=[legacy_path, normalized_path],
            output_path=output_path,
            strict=True,
            min_recipes=2,
        )
        assert report.output_rows == 2
        assert report.issues_count == 0

        out = json.loads(output_path.read_text(encoding="utf-8"))
        ids = {row["item"]["unique_name"] for row in out}
        assert ids == {"T4_MAIN_SWORD", "T4_BAG"}
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

