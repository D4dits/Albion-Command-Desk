from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.migration import convert_legacy_recipe_rows


@dataclass(frozen=True)
class RecipeBuildReport:
    inputs: list[str]
    total_rows_in: int
    normalized_rows: int
    legacy_rows: int
    skipped_rows: int
    output_rows: int
    issues_count: int
    issues: list[dict[str, str]]


def discover_input_paths(*, inputs: list[Path], globs: list[str]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for path in inputs:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    for pattern in globs:
        for path in sorted(Path().glob(pattern)):
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            out.append(path)
    return out


def build_recipes_dataset(
    *,
    input_paths: list[Path],
    output_path: Path,
    strict: bool = False,
    min_recipes: int = 1,
) -> RecipeBuildReport:
    raw_rows: list[dict[str, object]] = []
    normalized_rows: list[dict[str, object]] = []
    legacy_rows: list[dict[str, object]] = []
    skipped_rows = 0

    for path in input_paths:
        loaded_rows = _load_recipe_rows(path)
        for row in loaded_rows:
            raw_rows.append(row)
            if _is_normalized_row(row):
                normalized_rows.append(row)
            elif _looks_like_legacy_row(row):
                legacy_rows.append(row)
            else:
                skipped_rows += 1

    normalized_rows.extend(convert_legacy_recipe_rows(legacy_rows))
    merged = _dedupe_by_item(normalized_rows)
    merged.sort(key=lambda row: str(_item_id(row)).lower())

    if len(merged) < min_recipes:
        raise ValueError(f"recipes build produced {len(merged)} rows, expected at least {min_recipes}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    issues = _validate_output(output_path)
    report = RecipeBuildReport(
        inputs=[str(path) for path in input_paths],
        total_rows_in=len(raw_rows),
        normalized_rows=len(normalized_rows),
        legacy_rows=len(legacy_rows),
        skipped_rows=skipped_rows,
        output_rows=len(merged),
        issues_count=len(issues),
        issues=[asdict(issue) for issue in issues],
    )
    if strict and report.issues_count > 0:
        raise ValueError(f"recipes build failed integrity check with {report.issues_count} issues")
    return report


def write_build_report(*, report: RecipeBuildReport, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")


def _load_recipe_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[object]
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("recipes"), list):
        rows = payload.get("recipes") or []
    else:
        raise ValueError(f"unsupported recipe payload format: {path}")
    return [row for row in rows if isinstance(row, dict)]


def _is_normalized_row(row: dict[str, object]) -> bool:
    return (
        isinstance(row.get("item"), dict)
        and isinstance(row.get("components"), list)
        and isinstance(row.get("outputs"), list)
    )


def _looks_like_legacy_row(row: dict[str, object]) -> bool:
    return bool(row.get("item_unique_name") or row.get("item_id") or row.get("unique_name"))


def _item_id(row: dict[str, object]) -> str:
    payload = row.get("item")
    if isinstance(payload, dict):
        return str(payload.get("unique_name") or "").strip()
    return ""


def _dedupe_by_item(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_id: dict[str, dict[str, object]] = {}
    for row in rows:
        item_id = _item_id(row)
        if not item_id:
            continue
        by_id[item_id] = row
    return list(by_id.values())


def _validate_output(output_path: Path):
    validate_path = output_path.parent / f".recipes_validate_{uuid.uuid4().hex}.json"
    try:
        validate_path.write_text(output_path.read_text(encoding="utf-8"), encoding="utf-8")
        catalog = RecipeCatalog.from_json(validate_path)
        return catalog.validate_integrity()
    finally:
        try:
            validate_path.unlink(missing_ok=True)
        except Exception:
            pass
