from __future__ import annotations

import os
import struct
from typing import Any

from .ddl import quote_identifier

_SQL_COPT_SS_ACCESS_TOKEN = 1256
_AZURE_SQL_SCOPE = "https://database.windows.net/.default"


class AzureSqlTarget:
    def __init__(self, server: str, database: str) -> None:
        try:
            import pyodbc
            from azure.identity import DefaultAzureCredential
        except ImportError as exc:
            raise RuntimeError("Install the project dependencies to use Azure SQL") from exc

        token = DefaultAzureCredential().get_token(_AZURE_SQL_SCOPE).token
        token_bytes = token.encode("utf-16-le")
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        connection_string = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server=tcp:{server},1433;"
            f"Database={database};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        self._connection = pyodbc.connect(
            connection_string,
            attrs_before={_SQL_COPT_SS_ACCESS_TOKEN: token_struct},
            autocommit=False,
        )

    @classmethod
    def from_environment(cls) -> AzureSqlTarget:
        return cls(
            server=_required_environment("AZURE_SQL_SERVER"),
            database=_required_environment("AZURE_SQL_DATABASE"),
        )

    def close(self) -> None:
        self._connection.close()

    def count(self, schema: str, table: str) -> int:
        qualified = f"{quote_identifier(schema)}.{quote_identifier(table)}"
        with self._connection.cursor() as cursor:
            return int(cursor.execute(f"SELECT COUNT_BIG(*) FROM {qualified}").fetchone()[0])

    def sample(self, schema: str, table: str, limit: int = 10) -> list[tuple[Any, ...]]:
        if not 1 <= limit <= 100:
            raise ValueError("Sample limit must be between 1 and 100")
        qualified = f"{quote_identifier(schema)}.{quote_identifier(table)}"
        with self._connection.cursor() as cursor:
            return list(cursor.execute(f"SELECT TOP ({limit}) * FROM {qualified}").fetchall())


def _required_environment(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Set the required {name} environment variable")
    return value
