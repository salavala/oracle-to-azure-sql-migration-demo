from __future__ import annotations

import re
from collections.abc import Sequence

from .models import MappingDecision

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_$#]{0,127}$")


def quote_identifier(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"Unsafe SQL identifier: {value!r}")
    return f"[{value}]"


def create_table_sql(
    schema: str,
    table: str,
    decisions: Sequence[MappingDecision],
) -> str:
    if not decisions:
        raise ValueError("At least one column is required")
    columns = []
    for decision in decisions:
        nullability = "NULL" if decision.source.nullable else "NOT NULL"
        columns.append(
            f"    {quote_identifier(decision.source.name)} "
            f"{decision.target_type} {nullability}"
        )
    qualified_table = f"{quote_identifier(schema)}.{quote_identifier(table)}"
    return f"CREATE TABLE {qualified_table} (\n" + ",\n".join(columns) + "\n);"


def insert_sql(schema: str, table: str, decisions: Sequence[MappingDecision]) -> str:
    qualified_table = f"{quote_identifier(schema)}.{quote_identifier(table)}"
    columns = ", ".join(quote_identifier(item.source.name) for item in decisions)
    placeholders = ", ".join("?" for _ in decisions)
    return f"INSERT INTO {qualified_table} ({columns}) VALUES ({placeholders})"

