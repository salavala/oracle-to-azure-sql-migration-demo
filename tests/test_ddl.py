import pytest

from oracle_azure_migrate.ddl import create_table_sql, insert_sql, quote_identifier
from oracle_azure_migrate.models import MappingDecision, OracleColumn


def _decisions() -> list[MappingDecision]:
    return [
        MappingDecision(
            OracleColumn("ORDER_ID", "NUMBER", precision=12, scale=0, nullable=False),
            "bigint",
            "decimal",
            "Precision fits Azure SQL bigint",
        ),
        MappingDecision(
            OracleColumn("ORDER_DATE", "DATE", nullable=False),
            "datetime2(0)",
            "preserve",
            "Preserve date and time",
        ),
    ]


def test_create_table_sql_has_types_and_nullability() -> None:
    assert create_table_sql("dbo", "sales_orders", _decisions()) == (
        "CREATE TABLE [dbo].[sales_orders] (\n"
        "    [ORDER_ID] bigint NOT NULL,\n"
        "    [ORDER_DATE] datetime2(0) NOT NULL\n"
        ");"
    )


def test_insert_sql_is_parameterized() -> None:
    assert insert_sql("dbo", "sales_orders", _decisions()) == (
        "INSERT INTO [dbo].[sales_orders] ([ORDER_ID], [ORDER_DATE]) VALUES (?, ?)"
    )


def test_identifier_validation_rejects_injection() -> None:
    with pytest.raises(ValueError, match="Unsafe SQL identifier"):
        quote_identifier("sales_orders; DROP TABLE users")

