from __future__ import annotations

import os
import re
from typing import Any

from .models import ColumnProfile, OracleColumn

_ORACLE_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_$#]{0,127}$")


class OracleSource:
    def __init__(self, dsn: str, user: str, password: str) -> None:
        try:
            import oracledb
        except ImportError as exc:
            raise RuntimeError("Install the project dependencies to use Oracle") from exc
        self._connection = oracledb.connect(user=user, password=password, dsn=dsn)

    @classmethod
    def from_environment(cls) -> OracleSource:
        return cls(
            dsn=_required_environment("ORACLE_DSN"),
            user=_required_environment("ORACLE_USER"),
            password=_required_environment("ORACLE_PASSWORD"),
        )

    def close(self) -> None:
        self._connection.close()

    def columns(self, owner: str, table: str) -> list[OracleColumn]:
        owner = _oracle_identifier(owner)
        table = _oracle_identifier(table)
        query = """
            SELECT column_name, data_type, data_precision, data_scale,
                   char_length, nullable
            FROM all_tab_columns
            WHERE owner = :owner AND table_name = :table_name
            ORDER BY column_id
        """
        with self._connection.cursor() as cursor:
            rows = cursor.execute(query, owner=owner, table_name=table).fetchall()
        if not rows:
            raise RuntimeError(f"Oracle table {owner}.{table} was not found")
        return [
            OracleColumn(
                name=row[0],
                data_type=row[1],
                precision=row[2],
                scale=row[3],
                length=row[4],
                nullable=row[5] == "Y",
            )
            for row in rows
        ]

    def profiles(
        self, owner: str, table: str, columns: list[OracleColumn]
    ) -> dict[str, ColumnProfile]:
        owner = _oracle_identifier(owner)
        table = _oracle_identifier(table)
        profiles: dict[str, ColumnProfile] = {}
        with self._connection.cursor() as cursor:
            for column in columns:
                name = _oracle_identifier(column.name)
                profiles[name] = self._profile_column(cursor, owner, table, column)
        return profiles

    def count(self, owner: str, table: str) -> int:
        owner = _oracle_identifier(owner)
        table = _oracle_identifier(table)
        query = f'SELECT COUNT(*) FROM "{owner}"."{table}"'  # noqa: S608
        with self._connection.cursor() as cursor:
            return int(cursor.execute(query).fetchone()[0])

    @staticmethod
    def _profile_column(
        cursor: Any,
        owner: str,
        table: str,
        column: OracleColumn,
    ) -> ColumnProfile:
        name = _oracle_identifier(column.name)
        qualified = f'"{owner}"."{table}"'
        quoted = f'"{name}"'
        if column.data_type == "DATE":
            expressions = (
                f"COUNT({quoted}), "
                f"TO_CHAR(MIN({quoted}), 'YYYY-MM-DD HH24:MI:SS'), "
                f"TO_CHAR(MAX({quoted}), 'YYYY-MM-DD HH24:MI:SS'), "
                f"SUM(CASE WHEN {quoted} <> TRUNC({quoted}) THEN 1 ELSE 0 END)"
            )
            row = cursor.execute(f"SELECT {expressions} FROM {qualified}").fetchone()
            return ColumnProfile(
                non_null_count=int(row[0]),
                min_value=row[1],
                max_value=row[2],
                time_value_count=int(row[3] or 0),
            )
        if column.data_type == "NUMBER":
            expressions = (
                f"COUNT({quoted}), TO_CHAR(MIN({quoted}), 'TM9', "
                "'NLS_NUMERIC_CHARACTERS=''.,'''), "
                f"TO_CHAR(MAX({quoted}), 'TM9', 'NLS_NUMERIC_CHARACTERS=''.,'''), "
                f"SUM(CASE WHEN {quoted} <> TRUNC({quoted}) THEN 1 ELSE 0 END)"
            )
            row = cursor.execute(f"SELECT {expressions} FROM {qualified}").fetchone()
            return ColumnProfile(
                non_null_count=int(row[0]),
                min_value=row[1],
                max_value=row[2],
                fractional_count=int(row[3] or 0),
            )
        if column.data_type in {"CHAR", "VARCHAR2"}:
            expressions = (
                f"COUNT({quoted}), "
                f"SUM(CASE WHEN LENGTH({quoted}) > LENGTH(RTRIM({quoted})) "
                "THEN 1 ELSE 0 END), "
                f"MAX(LENGTH(RTRIM({quoted})))"
            )
            row = cursor.execute(f"SELECT {expressions} FROM {qualified}").fetchone()
            return ColumnProfile(
                non_null_count=int(row[0]),
                padded_value_count=int(row[1] or 0),
                max_trimmed_length=int(row[2]) if row[2] is not None else None,
            )
        return ColumnProfile()


def _oracle_identifier(value: str) -> str:
    normalized = value.upper()
    if not _ORACLE_IDENTIFIER.fullmatch(normalized):
        raise ValueError(f"Unsafe Oracle identifier: {value!r}")
    return normalized


def _required_environment(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Set the required {name} environment variable")
    return value
