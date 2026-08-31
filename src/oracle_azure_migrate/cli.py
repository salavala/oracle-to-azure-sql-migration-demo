from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assessment import assessment_report
from .mapping import MappingError, TypeMapper
from .models import ColumnProfile, OracleColumn
from .source import OracleSource
from .target import AzureSqlTarget


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oracle-azure-migrate",
        description="Migrate an Oracle table to Azure SQL with explicit type mappings.",
    )
    parser.add_argument(
        "--config",
        default="config/type-mappings.yml",
        help="YAML mapping configuration",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser(
        "demo-assess",
        help="Run the custom mapping assessment from checked-in profile fixtures",
    )
    demo.add_argument("--metadata", default="config/demo-metadata.json")
    demo.add_argument("--profiles", default="config/demo-profiles.json")
    _add_table_arguments(demo)

    assess = subparsers.add_parser(
        "assess",
        help="Profile live Oracle values and create the custom mapping assessment",
    )
    _add_table_arguments(assess)
    assess.add_argument("--output", default="reports/custom-mapping-assessment.md")

    validate = subparsers.add_parser(
        "validate", help="Compare source and target counts and display target samples"
    )
    _add_table_arguments(validate)
    validate.add_argument("--sample-size", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        mapper = TypeMapper.from_file(args.config)
        if args.command == "demo-assess":
            return _demo_assess(args, mapper)
        if args.command == "assess":
            return _live_assess(args, mapper)
        if args.command == "validate":
            return _validate(args)
    except (MappingError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


def _add_table_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--owner", default="MIGRATION_DEMO")
    parser.add_argument("--source-table", default="SALES_ORDERS")
    parser.add_argument("--target-schema", default="dbo")
    parser.add_argument("--target-table", default="sales_orders")


def _demo_assess(args: argparse.Namespace, mapper: TypeMapper) -> int:
    with Path(args.metadata).open(encoding="utf-8") as stream:
        values = json.load(stream)
    with Path(args.profiles).open(encoding="utf-8") as stream:
        profile_values = json.load(stream)
    columns = [OracleColumn.from_dict(value) for value in values]
    profiles = {
        name.upper(): ColumnProfile.from_dict(value)
        for name, value in profile_values.items()
    }
    decisions = [
        mapper.resolve(args.owner, args.source_table, column) for column in columns
    ]
    print(assessment_report(args.owner, args.source_table, decisions, profiles))
    return 0


def _live_assess(args: argparse.Namespace, mapper: TypeMapper) -> int:
    source = OracleSource.from_environment()
    try:
        columns = source.columns(args.owner, args.source_table)
        profiles = source.profiles(args.owner, args.source_table, columns)
    finally:
        source.close()
    decisions = [
        mapper.resolve(args.owner, args.source_table, column) for column in columns
    ]
    report = assessment_report(args.owner, args.source_table, decisions, profiles)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\nAssessment written to {output}")
    return 0


def _validate(args: argparse.Namespace) -> int:
    source = OracleSource.from_environment()
    target = AzureSqlTarget.from_environment()
    try:
        source_count = source.count(args.owner, args.source_table)
        target_count = target.count(args.target_schema, args.target_table)
        samples = target.sample(args.target_schema, args.target_table, args.sample_size)
    finally:
        target.close()
        source.close()

    print(f"Source rows: {source_count}")
    print(f"Target rows: {target_count}")
    if source_count != target_count:
        raise RuntimeError("Validation failed: source and target row counts differ")
    print("Row-count validation: PASS")
    print("\nAzure SQL samples:")
    for sample in samples:
        print(tuple(sample))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
