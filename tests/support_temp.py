from __future__ import annotations

from pathlib import Path
import uuid


def mk_test_dir(prefix: str) -> Path:
    base = Path("artifacts") / "tmp" / "pytest_runtime" / prefix
    base.mkdir(parents=True, exist_ok=True)
    target = base / uuid.uuid4().hex
    target.mkdir(parents=True, exist_ok=False)
    return target
