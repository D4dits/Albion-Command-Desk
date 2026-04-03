from __future__ import annotations

import re
import tomllib
from pathlib import Path


def test_website_software_version_matches_project_version() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    expected_version = str(pyproject["project"]["version"])
    index_html = Path("website/index.html").read_text(encoding="utf-8")

    match = re.search(r'"softwareVersion":\s*"([^"]+)"', index_html)

    assert match is not None
    assert match.group(1) == expected_version
