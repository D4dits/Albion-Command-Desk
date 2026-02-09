from __future__ import annotations

import argparse
import sys
from pathlib import Path

from albion_dps.market.recipes_pipeline import (
    RecipeBuildReport,
    build_recipes_dataset,
    discover_input_paths,
    write_build_report,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build normalized market recipes dataset from one or more source files.",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Path to JSON source file (can be repeated).",
    )
    parser.add_argument(
        "--input-glob",
        action="append",
        default=["tools/market/sources/**/*.json"],
        help="Glob pattern for source files (can be repeated).",
    )
    parser.add_argument(
        "--output",
        default="albion_dps/market/data/recipes.json",
        help="Output path for normalized recipes dataset.",
    )
    parser.add_argument(
        "--report",
        default="artifacts/market/recipes_build_report.json",
        help="Output path for build report JSON.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail build if catalog integrity issues are found.",
    )
    parser.add_argument(
        "--min-recipes",
        type=int,
        default=1,
        help="Minimum number of recipes required after merge/dedupe.",
    )
    return parser.parse_args(argv)


def _print_report(report: RecipeBuildReport) -> None:
    print(f"inputs: {len(report.inputs)}")
    print(f"rows_in: {report.total_rows_in}")
    print(f"normalized_rows: {report.normalized_rows}")
    print(f"legacy_rows: {report.legacy_rows}")
    print(f"skipped_rows: {report.skipped_rows}")
    print(f"output_rows: {report.output_rows}")
    print(f"issues: {report.issues_count}")
    if report.issues:
        for issue in report.issues[:10]:
            print(f"- [{issue['recipe_id']}] {issue['message']}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    explicit_inputs = [Path(x) for x in args.input]
    paths = discover_input_paths(inputs=explicit_inputs, globs=list(args.input_glob))
    if not paths:
        print("No recipe sources found. Provide --input or --input-glob.", file=sys.stderr)
        return 2
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        print("Missing input paths:", file=sys.stderr)
        for path in missing:
            print(f"- {path}", file=sys.stderr)
        return 2
    report = build_recipes_dataset(
        input_paths=paths,
        output_path=Path(args.output),
        strict=bool(args.strict),
        min_recipes=max(1, int(args.min_recipes)),
    )
    write_build_report(report=report, report_path=Path(args.report))
    _print_report(report)
    print(f"output: {args.output}")
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

