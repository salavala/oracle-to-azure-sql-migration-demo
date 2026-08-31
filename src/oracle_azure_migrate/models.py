from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OracleColumn:
    name: str
    data_type: str
    precision: int | None = None
    scale: int | None = None
    length: int | None = None
    nullable: bool = True

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> OracleColumn:
        return cls(
            name=str(value["name"]).upper(),
            data_type=str(value["data_type"]).upper(),
            precision=_optional_int(value.get("precision")),
            scale=_optional_int(value.get("scale")),
            length=_optional_int(value.get("length")),
            nullable=bool(value.get("nullable", True)),
        )


@dataclass(frozen=True)
class MappingDecision:
    source: OracleColumn
    target_type: str
    transform: str
    reason: str
    overridden: bool = False


@dataclass(frozen=True)
class ColumnProfile:
    non_null_count: int = 0
    min_value: str | None = None
    max_value: str | None = None
    fractional_count: int = 0
    time_value_count: int = 0
    padded_value_count: int = 0
    max_trimmed_length: int | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ColumnProfile:
        return cls(
            non_null_count=int(value.get("non_null_count", 0)),
            min_value=_optional_str(value.get("min_value")),
            max_value=_optional_str(value.get("max_value")),
            fractional_count=int(value.get("fractional_count", 0)),
            time_value_count=int(value.get("time_value_count", 0)),
            padded_value_count=int(value.get("padded_value_count", 0)),
            max_trimmed_length=_optional_int(value.get("max_trimmed_length")),
        )


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)
