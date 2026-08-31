from __future__ import annotations

from collections.abc import Sequence

from .ddl import create_table_sql
from .models import MappingDecision


def mapping_report(
    owner: str,
    source_table: str,
    target_schema: str,
    target_table: str,
    decisions: Sequence[MappingDecision],
) -> str:
    lines = [
        f"Mapping plan: {owner}.{source_table} -> {target_schema}.{target_table}",
        "",
        f"{'Column':<20} {'Oracle':<18} {'Azure SQL':<20} {'Transform':<12} Rule",
        "-" * 100,
    ]
    for decision in decisions:
        source_type = _source_type(decision)
        rule = "override" if decision.overridden else "default"
        lines.append(
            f"{decision.source.name:<20} {source_type:<18} "
            f"{decision.target_type:<20} {decision.transform:<12} {rule}"
        )
        lines.append(f"  {decision.reason}")
    lines.extend(
        [
            "",
            "Generated target DDL:",
            create_table_sql(target_schema, target_table, decisions),
        ]
    )
    return "\n".join(lines)


def _source_type(decision: MappingDecision) -> str:
    column = decision.source
    if column.data_type == "NUMBER" and column.precision is not None:
        return f"NUMBER({column.precision},{column.scale or 0})"
    if column.data_type in {"CHAR", "VARCHAR2"}:
        return f"{column.data_type}({column.length})"
    return column.data_type

