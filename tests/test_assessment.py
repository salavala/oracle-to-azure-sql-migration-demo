from oracle_azure_migrate.assessment import assess_mapping
from oracle_azure_migrate.mapping import TypeMapper
from oracle_azure_migrate.models import ColumnProfile, OracleColumn


def _mapper() -> TypeMapper:
    return TypeMapper(
        {
            "version": 1,
            "defaults": {
                "date": {"target_type": "datetime2(0)", "transform": "preserve"},
                "unconstrained_number": {
                    "target_type": "decimal(38,10)",
                    "transform": "decimal",
                },
                "char": {"target_type": "char({length})", "transform": "preserve"},
            },
            "overrides": {
                "MIGRATION_DEMO.SALES_ORDERS.SHIP_DATE": {
                    "target_type": "date",
                    "transform": "date_only",
                },
                "MIGRATION_DEMO.SALES_ORDERS.LEGACY_REFERENCE": {
                    "target_type": "varchar(12)",
                    "transform": "trim_right",
                },
            },
        }
    )


def test_date_only_mapping_blocks_when_source_contains_time() -> None:
    decision = _mapper().resolve(
        "MIGRATION_DEMO", "SALES_ORDERS", OracleColumn("SHIP_DATE", "DATE")
    )
    finding = assess_mapping(
        decision, ColumnProfile(non_null_count=3, time_value_count=2)
    )
    assert finding.severity == "BLOCKER"
    assert "business approval" in finding.ssma_action


def test_unconstrained_number_warns_about_ssma_float_default() -> None:
    decision = _mapper().resolve(
        "MIGRATION_DEMO", "OTHER_TABLE", OracleColumn("SCORE", "NUMBER")
    )
    finding = assess_mapping(
        decision,
        ColumnProfile(
            non_null_count=3,
            min_value="-1.25",
            max_value="99.75",
            fractional_count=3,
        ),
    )
    assert finding.severity == "WARNING"
    assert finding.ssma_default == "float(53)"
    assert finding.recommended_target == "decimal(38,10)"


def test_varchar_override_requires_padding_review() -> None:
    decision = _mapper().resolve(
        "MIGRATION_DEMO",
        "SALES_ORDERS",
        OracleColumn("LEGACY_REFERENCE", "CHAR", length=12),
    )
    finding = assess_mapping(
        decision,
        ColumnProfile(
            non_null_count=4,
            padded_value_count=4,
            max_trimmed_length=11,
        ),
    )
    assert finding.severity == "REVIEW"
    assert "trailing-space validation" in finding.ssma_action
