from __future__ import annotations

import json
import re
from pathlib import Path


def test_last_known_good_pointer_shape() -> None:
    pointer_path = Path("tools/release/manifest/last_known_good.json")
    payload = json.loads(pointer_path.read_text(encoding="utf-8"))

    assert isinstance(payload, dict)
    assert isinstance(payload.get("tag"), str)
    assert re.match(r"^v\d+\.\d+\.\d+([\-+].+)?$", payload["tag"])
    assert payload.get("asset_name") == "manifest.json"
    assert isinstance(payload.get("updated_at_utc"), str)
