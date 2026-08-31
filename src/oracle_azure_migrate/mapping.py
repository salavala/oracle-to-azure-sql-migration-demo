from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml

from .models import MappingDecision, OracleColumn

_TARGET_TYPE_PATTERN = re.compile(
    r"^(?:date|datetime2\([0-7]\)|int|bigint|decimal\((?:[1-9]|[12]\d|3[0-8]),"
    r"(?:\d|[12]\d|3[0-8])\)|char\([1-9]\d{0,3}\)|varchar\([1-9]\d{0,3}\)|"
    r"nvarchar\([1-9]\d{0,3}\))$",
    re.IGNORECASE,
)
_TRANSFORMS = {"preserve", "date_only", "trim_right", "decimal"}


class MappingError(ValueError):
    """Raised when a mapping cannot preserve source data safely."""


class TypeMapper:
    def __init__(self, config: dict[str, Any]) -> None:
        if config.get("version") != 1:
            raise MappingError("Mapping configuration must declare version: 1")
        self.defaults = config.get("defaults", {})
        self.overrides = {
            str(key).upper(): value for key, value in config.get("overrides", {}).items()
        }

    @classmethod
    def from_file(cls, path: str | Path) -> TypeMapper:
        with Path(path).open(encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
        if not isinstance(config, dict):
            raise MappingError("Mapping configuration must be a YAML object")
        return cls(config)

    def resolve(self, owner: str, table: str, column: OracleColumn) -> MappingDecision:
        qualified_name = f"{owner}.{table}.{column.name}".upper()
        override = self.overrides.get(qualified_name)
        if override is not None:
            return self._override_decision(column, override)

        match column.data_type:
            case "DATE":
                rule = self._default_rule("date")
                return self._decision(column, rule, "Oracle DATE preserves date and time")
            case "NUMBER":
                return self._map_number(column)
            case "CHAR":
                if column.length is None or column.length < 1:
                    raise MappingError(f"{column.name}: CHAR requires a positive length")
                rule = self._default_rule("char")
                target_type = str(rule["target_type"]).format(length=column.length)
                return self._decision(
                    column,
                    {**rule, "target_type": target_type},
                    "Preserve fixed-width Oracle CHAR semantics",
                )
            case "VARCHAR2":
                if column.length is None or column.length < 1:
                    raise MappingError(f"{column.name}: VARCHAR2 requires a positive length")
                return self._decision(
                    column,
                    {"target_type": f"varchar({column.length})", "transform": "preserve"},
                    "Map Oracle VARCHAR2 to Azure SQL varchar",
                )
            case _:
                raise MappingError(
                    f"{column.name}: unsupported Oracle type {column.data_type}; "
                    "add an explicit mapping before migration"
                )

    def transform_value(self, value: Any, decision: MappingDecision) -> Any:
        if value is None:
            return None
        match decision.transform:
            case "preserve":
                return value
            case "date_only":
                if isinstance(value, datetime):
                    return value.date()
                if isinstance(value, date):
                    return value
                raise MappingError(f"{decision.source.name}: expected date/time value")
            case "trim_right":
                if not isinstance(value, str):
                    raise MappingError(f"{decision.source.name}: expected character value")
                return value.rstrip()
            case "decimal":
                try:
                    return value if isinstance(value, Decimal) else Decimal(str(value))
                except (InvalidOperation, ValueError) as exc:
                    raise MappingError(
                        f"{decision.source.name}: value {value!r} is not a decimal"
                    ) from exc
            case _:
                raise MappingError(
                    f"{decision.source.name}: unsupported transform {decision.transform}"
                )

    def _map_number(self, column: OracleColumn) -> MappingDecision:
        if column.precision is None:
            rule = self._default_rule("unconstrained_number")
            return self._decision(
                column,
                rule,
                "Use the configured fallback for unconstrained Oracle NUMBER",
            )

        scale = column.scale or 0
        if not 1 <= column.precision <= 38:
            raise MappingError(f"{column.name}: NUMBER precision must be between 1 and 38")

        if scale < 0:
            target_precision = column.precision - scale
            if target_precision > 38:
                raise MappingError(
                    f"{column.name}: NUMBER({column.precision},{scale}) exceeds Azure SQL "
                    "decimal precision; profile and override this column"
                )
            target_type = f"decimal({target_precision},0)"
            reason = "Expand precision for an Oracle NUMBER with negative scale"
        elif scale == 0 and column.precision <= 9:
            target_type = "int"
            reason = "Precision fits Azure SQL int"
        elif scale == 0 and column.precision <= 18:
            target_type = "bigint"
            reason = "Precision fits Azure SQL bigint"
        elif scale <= column.precision:
            target_type = f"decimal({column.precision},{scale})"
            reason = "Preserve Oracle NUMBER precision and scale"
        else:
            raise MappingError(
                f"{column.name}: NUMBER({column.precision},{scale}) requires an explicit "
                "mapping because Azure SQL decimal scale cannot exceed precision"
            )

        return self._decision(
            column,
            {"target_type": target_type, "transform": "decimal"},
            reason,
        )

    def _default_rule(self, name: str) -> dict[str, Any]:
        rule = self.defaults.get(name)
        if not isinstance(rule, dict):
            raise MappingError(f"Missing defaults.{name} mapping")
        return rule

    def _override_decision(
        self, column: OracleColumn, override: dict[str, Any]
    ) -> MappingDecision:
        if not isinstance(override, dict):
            raise MappingError(f"{column.name}: mapping override must be an object")
        reason = str(override.get("reason", "Explicit column-level override"))
        return self._decision(column, override, reason, overridden=True)

    def _decision(
        self,
        column: OracleColumn,
        rule: dict[str, Any],
        reason: str,
        *,
        overridden: bool = False,
    ) -> MappingDecision:
        target_type = str(rule.get("target_type", ""))
        transform = str(rule.get("transform", "preserve"))
        if not _TARGET_TYPE_PATTERN.fullmatch(target_type):
            raise MappingError(f"{column.name}: unsafe target type {target_type!r}")
        if transform not in _TRANSFORMS:
            raise MappingError(f"{column.name}: unsupported transform {transform!r}")
        _validate_decimal(target_type, column.name)
        return MappingDecision(
            source=column,
            target_type=target_type.lower(),
            transform=transform,
            reason=reason,
            overridden=overridden,
        )


def _validate_decimal(target_type: str, column_name: str) -> None:
    match = re.fullmatch(r"decimal\((\d+),(\d+)\)", target_type, re.IGNORECASE)
    if match and int(match.group(2)) > int(match.group(1)):
        raise MappingError(f"{column_name}: decimal scale cannot exceed precision")

