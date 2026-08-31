from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from oracle_azure_migrate.mapping import MappingError, TypeMapper
from oracle_azure_migrate.models import OracleColumn

ROOT = Path(__file__).parents[1]


@pytest.fixture
def mapper() -> TypeMapper:
    return TypeMapper.from_file(ROOT / "config/type-mappings.yml")


@pytest.mark.parametrize(
    ("precision", "scale", "expected"),
    [
        (9, 0, "int"),
        (10, 0, "bigint"),
        (18, 0, "bigint"),
        (19, 0, "decimal(19,0)"),
        (15, 2, "decimal(15,2)"),
        (5, -2, "decimal(7,0)"),
    ],
)
def test_number_mapping(
    mapper: TypeMapper, precision: int, scale: int, expected: str
) -> None:
    decision = mapper.resolve(
        "MIGRATION_DEMO",
        "SALES_ORDERS",
        OracleColumn("VALUE", "NUMBER", precision=precision, scale=scale),
    )
    assert decision.target_type == expected
    assert decision.transform == "decimal"


def test_date_preserves_time_by_default(mapper: TypeMapper) -> None:
    decision = mapper.resolve(
        "MIGRATION_DEMO", "SALES_ORDERS", OracleColumn("ORDER_DATE", "DATE")
    )
    value = datetime(2026, 8, 24, 14, 5, 7)
    assert decision.target_type == "datetime2(0)"
    assert mapper.transform_value(value, decision) == value


def test_ship_date_override_discards_time(mapper: TypeMapper) -> None:
    decision = mapper.resolve(
        "MIGRATION_DEMO", "SALES_ORDERS", OracleColumn("SHIP_DATE", "DATE")
    )
    assert decision.overridden
    assert decision.target_type == "date"
    assert mapper.transform_value(datetime(2026, 8, 25, 16, 45), decision) == date(
        2026, 8, 25
    )


def test_char_default_preserves_fixed_width(mapper: TypeMapper) -> None:
    decision = mapper.resolve(
        "MIGRATION_DEMO",
        "SALES_ORDERS",
        OracleColumn("COUNTRY_CODE", "CHAR", length=2),
    )
    assert decision.target_type == "char(2)"
    assert mapper.transform_value("US", decision) == "US"


def test_char_override_trims_padding(mapper: TypeMapper) -> None:
    decision = mapper.resolve(
        "MIGRATION_DEMO",
        "SALES_ORDERS",
        OracleColumn("LEGACY_REFERENCE", "CHAR", length=12),
    )
    assert decision.target_type == "varchar(12)"
    assert mapper.transform_value("PADDED      ", decision) == "PADDED"


def test_unbounded_number_uses_profiled_override(mapper: TypeMapper) -> None:
    decision = mapper.resolve(
        "MIGRATION_DEMO",
        "SALES_ORDERS",
        OracleColumn("UNBOUNDED_SCORE", "NUMBER"),
    )
    assert decision.target_type == "decimal(20,6)"
    assert mapper.transform_value("98.765432", decision) == Decimal("98.765432")


def test_unsupported_type_fails_closed(mapper: TypeMapper) -> None:
    with pytest.raises(MappingError, match="unsupported Oracle type"):
        mapper.resolve(
            "MIGRATION_DEMO", "SALES_ORDERS", OracleColumn("PAYLOAD", "BLOB")
        )

