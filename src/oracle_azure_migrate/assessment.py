from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .models import ColumnProfile, MappingDecision

Severity = Literal["BLOCKER", "WARNING", "REVIEW", "OK"]


@dataclass(frozen=True)
class AssessmentFinding:
    column: str
    source_type: str
    ssma_default: str
    recommended_target: str
    severity: Severity
    evidence: str
    ssma_action: str


def assess_mapping(
    decision: MappingDecision,
    profile: ColumnProfile,
) -> AssessmentFinding:
    source_type = _source_type(decision)
    ssma_default = _ssma_default(decision)
    severity: Severity = "OK"
    evidence = f"{profile.non_null_count} non-null values profiled"
    action = "Keep the inherited SSMA mapping."

    if decision.source.data_type == "DATE":
        evidence = (
            f"{profile.time_value_count} of {profile.non_null_count} non-null values "
            "contain a time component"
        )
        if decision.target_type == "date" and profile.time_value_count:
            severity = "BLOCKER"
            action = (
                "Keep the project DATE mapping as datetime2(0). Only after business "
                "approval, edit this converted target column to date before synchronization; "
                "a table-level DATE rule would also affect other DATE columns."
            )
        elif decision.target_type != ssma_default:
            severity = "REVIEW"
            action = (
                f"Use an SSMA scope that contains no conflicting DATE semantics, or edit "
                f"the converted target column to {decision.target_type} before synchronization."
            )
    elif decision.source.data_type == "NUMBER":
        evidence = (
            f"range {profile.min_value or 'n/a'} to {profile.max_value or 'n/a'}; "
            f"{profile.fractional_count} values contain a fractional component"
        )
        if decision.source.precision is None:
            severity = "WARNING"
            action = (
                f"Override SSMA's float(53) default with {decision.target_type} after "
                "confirming the profiled range and scale."
            )
        elif decision.target_type != ssma_default:
            severity = "REVIEW"
            action = (
                f"Optionally set the object-level SSMA target to {decision.target_type}; "
                f"the inherited mapping is {ssma_default}."
            )
    elif decision.source.data_type == "CHAR":
        evidence = (
            f"{profile.padded_value_count} padded values; maximum trimmed length "
            f"{profile.max_trimmed_length or 0}"
        )
        if decision.target_type.startswith("varchar"):
            severity = "REVIEW"
            action = (
                f"Set the table-level SSMA mapping to {decision.target_type}, then run "
                "the supplied trailing-space validation."
            )

    return AssessmentFinding(
        column=decision.source.name,
        source_type=source_type,
        ssma_default=ssma_default,
        recommended_target=decision.target_type,
        severity=severity,
        evidence=evidence,
        ssma_action=action,
    )


def assessment_report(
    owner: str,
    table: str,
    decisions: list[MappingDecision],
    profiles: dict[str, ColumnProfile],
) -> str:
    findings = [
        assess_mapping(decision, profiles.get(decision.source.name, ColumnProfile()))
        for decision in decisions
    ]
    lines = [
        f"# Custom Type Mapping Assessment: {owner}.{table}",
        "",
        "Run this after SSMA **Create Report** and before **Convert Schema**.",
        "",
        "| Severity | Column | Oracle | SSMA default | Recommended | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for finding in findings:
        lines.append(
            f"| {finding.severity} | `{finding.column}` | `{finding.source_type}` | "
            f"`{finding.ssma_default}` | `{finding.recommended_target}` | "
            f"{finding.evidence} |"
        )
    lines.extend(["", "## SSMA actions", ""])
    for finding in findings:
        lines.append(f"- **{finding.column}:** {finding.ssma_action}")
    lines.extend(
        [
            "",
            "## Decision gate",
            "",
            "Do not convert the schema while any `BLOCKER` is unresolved. Record the "
            "business decision for every `REVIEW` or `WARNING` in the SSMA project notes.",
        ]
    )
    return "\n".join(lines)


def _source_type(decision: MappingDecision) -> str:
    column = decision.source
    if column.data_type == "NUMBER" and column.precision is not None:
        return f"NUMBER({column.precision},{column.scale or 0})"
    if column.data_type in {"CHAR", "VARCHAR2"} and column.length:
        return f"{column.data_type}({column.length})"
    return column.data_type


def _ssma_default(decision: MappingDecision) -> str:
    column = decision.source
    if column.data_type == "DATE":
        return "datetime2(0)"
    if column.data_type == "NUMBER":
        if column.precision is None:
            return "float(53)"
        return f"numeric({column.precision},{column.scale or 0})"
    if column.data_type == "CHAR":
        return f"char({column.length})"
    if column.data_type == "VARCHAR2":
        return f"varchar({column.length})"
    return "unsupported"
