from pathlib import Path

from oracle_azure_migrate.cli import main

ROOT = Path(__file__).parents[1]


def test_offline_demo_assessment(capsys) -> None:
    result = main(
        [
            "--config",
            str(ROOT / "config/type-mappings.yml"),
            "demo-assess",
            "--metadata",
            str(ROOT / "config/demo-metadata.json"),
            "--profiles",
            str(ROOT / "config/demo-profiles.json"),
        ]
    )
    output = capsys.readouterr().out
    assert result == 0
    assert "ORDER_DATE" in output
    assert "datetime2(0)" in output
    assert "SHIP_DATE" in output
    assert "date" in output
    assert "LEGACY_REFERENCE" in output
    assert "varchar(12)" in output
    assert "SSMA default" in output
    assert "BLOCKER" in output
    assert "float(53)" in output
