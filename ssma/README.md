# SSMA for Oracle Workbench

SSMA performs the schema conversion and data migration in this demo. The Python
utility does not replace SSMA; it adds data profiling and a decision gate for
the mappings that need business context.

## Mapping scope used by the demo

In SSMA, mapping settings inherit from project to object category to object.
Keep broad, safe defaults at project scope and use table-level overrides for
business-specific decisions.

| Scope | Source | Target | Why |
|---|---|---|---|
| Project | Oracle `DATE` | `datetime2(0)` | Oracle `DATE` contains time to the second |
| Project | `NUMBER(p,s)` | `numeric(p,s)` | Preserve declared precision and scale |
| Converted target column | `SHIP_DATE DATE` | `date` | Only after accepting the assessor's time-loss blocker |
| Table: `SALES_ORDERS` | unconstrained `UNBOUNDED_SCORE NUMBER` | `decimal(20,6)` | Avoid SSMA's `float(53)` default and preserve exact values |
| Table: `SALES_ORDERS`, source length 12 only | `LEGACY_REFERENCE CHAR(12)` | `varchar(12)` | Remove fixed-width semantics without changing shorter CHAR columns |

SSMA mappings operate by source type and selected object scope, not by an
individual column name. Do not add a table-level `DATE -> date` mapping to this
table because it would also change `ORDER_DATE`. For the approved `SHIP_DATE`
exception, edit the converted target column before synchronization.

## SSMA procedure

1. Install [SSMA for Oracle](https://aka.ms/ssmafororacle) and a supported
   Oracle client/provider.
2. Select **File > New Project**, choose **Azure SQL Database** as the target,
   and name the project `OracleAzureSqlTypeMappingDemo`.
3. Select **Connect to Oracle** and connect to
   `localhost:1521/FREEPDB1` with the local demo user.
4. Select `MIGRATION_DEMO` in Oracle Metadata Explorer.
5. Right-click the schema and choose **Create Report**. Save and review the HTML
   assessment, especially warnings for tables and data types.
6. Run `scripts/run-custom-assessment.ps1`. Do not continue while the Markdown
   report contains an unresolved `BLOCKER`.
7. In **Tools > Project Settings > Type Mapping**, confirm the project-level
   `DATE -> datetime2(0)` mapping.
8. Select `MIGRATION_DEMO > Tables > SALES_ORDERS`, open its **Type Mapping**
   tab, and add the approved `NUMBER` and length-bounded `CHAR` mappings above.
9. Connect to Azure SQL Database with Microsoft Entra authentication. Map the
   Oracle `MIGRATION_DEMO` schema to target schema `dbo`.
10. Right-click `MIGRATION_DEMO` and select **Convert Schema**. If the
    `SHIP_DATE -> date` loss was approved, edit that converted target column
    before publishing. Review the target DDL and the SSMA Error List.
11. In Azure SQL Database Metadata Explorer, right-click the database and
    select **Synchronize with Database**. Review the synchronization script.
12. In Oracle Metadata Explorer, select `SALES_ORDERS` and choose
    **Migrate Data**. Review the Data Migration Report and confirm four rows.
13. Run `sql/validate_target.sql` in SSMS or the Azure portal query editor.
14. If the approved `CHAR -> varchar` mapping retained padding, review and run
    `sql/normalize_legacy_reference.sql`, then rerun validation.

## Decision record

Before **Convert Schema**, capture:

- The SSMA HTML assessment report path.
- The generated `reports/custom-mapping-assessment.md`.
- Approval or rejection of the lossy `SHIP_DATE -> date` mapping.
- The observed precision and scale used for unconstrained `NUMBER`.
- Whether right-padding is meaningful for each converted `CHAR` column.

## Authoritative references

- [Oracle to Azure SQL Database migration guide](https://learn.microsoft.com/azure/azure-sql/migration-guides/database/oracle-to-sql-database-guide)
- [Map Oracle and SQL Server data types](https://learn.microsoft.com/sql/ssma/oracle/mapping-oracle-and-sql-server-data-types-oracletosql)
- [SSMA type-mapping project settings](https://learn.microsoft.com/sql/ssma/oracle/project-settings-type-mapping-oracletosql)
- [SSMA assessment report](https://learn.microsoft.com/sql/ssma/oracle/assessment-report-oracletosql)
