# Azure Deployment Plan

> **Status:** Validated

Generated: 2026-08-31

---

## 1. Project Overview

**Goal:** Create and publish a runnable SSMA for Oracle-to-Azure SQL Database
migration demo that adds a custom mapping assessment for Oracle `DATE`,
`NUMBER`, and `CHAR` columns.

**Path:** New Project

**Repository:** `salavala/oracle-to-azure-sql-migration-demo` (public)

---

## 2. Requirements

| Attribute | Value |
|-----------|-------|
| Classification | POC |
| Scale | Small |
| Budget | Cost-optimized |
| Subscription | Not applicable in this run; Azure deployment explicitly skipped by the user |
| Location | Not applicable in this run; Azure deployment explicitly skipped by the user |
| Compliance | Synthetic demo data only; no customer or production data |
| Source | Oracle Database Free container for local demonstration |
| Target | Azure SQL Database using Microsoft Entra authentication |

### Mapping scenarios

| Oracle source | Default Azure SQL target | Demonstrated custom behavior |
|---------------|--------------------------|-------------------------------|
| `DATE` | `datetime2(0)` | Post-conversion column edit to `date` only when time is intentionally discarded |
| `NUMBER(p,0)` | `int` or `bigint` | Precision-aware integral mapping |
| `NUMBER(p,s)` | `decimal(p,s)` | Preserve precision and scale; reject unsafe mappings |
| Unconstrained `NUMBER` | `decimal(38,10)` | Configurable fallback with range validation |
| `CHAR(n)` | `char(n)` | Length-bounded object mapping to `varchar(n)` plus padding validation |

---

## 3. Components Detected

The project is greenfield. The following components will be generated:

| Component | Type | Technology | Path |
|-----------|------|------------|------|
| Mapping assessor | Local utility | Python 3.11+, `oracledb` | `src/oracle_azure_migrate/` |
| Mapping rules | Configuration | YAML | `config/type-mappings.yml` |
| Oracle source lab | Database container | Oracle Database Free + SQL bootstrap | `docker-compose.yml`, `oracle/` |
| Azure SQL target | Managed database | Azure SQL Database | `infra/` |
| Migration workbench | Windows desktop | SQL Server Migration Assistant for Oracle | `ssma/` |
| Demo runner | Automation | PowerShell and Bash | `scripts/` |
| Tests | Quality | Pytest | `tests/` |

---

## 4. Recipe Selection

**Selected:** AZD with Bicep

**Rationale:** AZD is the default for a new Azure project and provides a simple
future provisioning path. Bicep will create only an Entra-authenticated logical
SQL server and a low-cost Basic database. The migration utility itself runs
locally so it can connect to both the Oracle source and Azure SQL target.

---

## 5. Architecture

**Stack:** Local container plus local Python migration worker and Azure SQL PaaS

### Data flow

1. Docker Compose starts Oracle Database Free and loads synthetic sales data.
2. SSMA creates its standard HTML schema assessment report.
3. The companion assessor reads Oracle metadata and value profiles, compares
   SSMA defaults with the YAML policy, and flags lossy or ambiguous mappings.
4. The presenter applies approved mappings at project or table scope in SSMA.
5. SSMA converts and synchronizes the schema, then migrates the data.
6. Post-migration checks compare counts and verify date/time, exact numeric,
   and fixed-width character semantics.

### Service mapping

| Component | Azure service / runtime | SKU |
|-----------|-------------------------|-----|
| Target relational database | Azure SQL Database | Basic, 2 GB |
| Migration worker | Local Python process | No Azure compute |
| Oracle source | Local Oracle Database Free container | No Azure resource |

### Security

- Azure SQL logical server uses Entra-only authentication.
- No SQL administrator password or Oracle credentials are committed.
- Oracle demo credentials are supplied through a local ignored `.env` file.
- Azure access uses `DefaultAzureCredential` and an ODBC access token.
- TLS 1.2 is required for Azure SQL.
- Profiler and validation SQL identifiers are validated before query execution.
- Public network access is disabled by default in the optional Bicep. A
  caller-supplied IP firewall rule is required for a local demo connection.

### Research references

- Microsoft Learn: Oracle to Azure SQL Database migration guide
- Microsoft Learn: SSMA for Oracle assessment reports
- Microsoft Learn: SSMA Oracle type-mapping defaults and inheritance
- Azure SQL Database Entra-only Bicep guidance

---

## 6. Provisioning Limit Checklist

Azure deployment was explicitly skipped. No resources will be provisioned in
this run, so quota and capacity checks are not applicable.

| Resource type | Number deployed now | Limit/quota | Notes |
|---------------|---------------------|-------------|-------|
| `Microsoft.Sql/servers` | 0 | Not applicable | Optional Bicep artifact only |
| `Microsoft.Sql/servers/databases` | 0 | Not applicable | Optional Bicep artifact only |
| `Microsoft.Sql/servers/firewallRules` | 0 | Not applicable | Optional, explicit client IP only |

**Status:** No provisioning requested

---

## 7. Execution Checklist

### Phase 1: Planning

- [x] Analyze workspace
- [x] Gather requirements
- [x] Record that subscription and location are deferred
- [x] Record that quota validation is not applicable without provisioning
- [x] Scan codebase
- [x] Select recipe
- [x] Plan architecture
- [x] User approved this plan

### Phase 2: Execution

- [x] Research required Azure SQL and identity implementation details
- [x] Generate SSMA companion assessment, mapping configuration, and sample data
- [x] Generate Entra-only Azure SQL infrastructure
- [x] Generate local demo scripts and step-by-step documentation
- [x] Add automated unit and integration-contract tests
- [x] Run local functional verification
- [x] Update status to `Ready for Validation`

### Phase 3: Validation

- [x] Invoke `azure-validate`
- [x] Validate Python tests and package
- [x] Validate Bicep and AZD configuration
- [x] Confirm no secrets or SQL authentication properties are present
- [x] Update status to `Validated`

#### AZD validation steps

- [x] AZD installation: version 1.23.15 detected
- [x] Schema validation: `azd package --no-prompt` parsed the project
- [x] Environment setup: isolated `validation` environment created
- [x] Authentication check: checked; interactive login deferred with deployment
- [x] Subscription/location check: not applicable because deployment was skipped
- [x] Aspire pre-provisioning checks: not an Aspire project
- [x] Provision preview: not applicable without an approved deployment target
- [x] Build verification: Python wheel and Bicep compiled
- [x] Docker build-context validation: no deployable Docker service
- [x] Package validation: AZD packaging succeeded
- [x] Azure Policy validation: not applicable without a selected subscription
- [x] Aspire post-provisioning checks: not an Aspire project

### Phase 4: Deployment

- [ ] Deferred by user; do not provision Azure resources

---

## 8. Validation Proof

This section will be populated by `azure-validate`.

| Check | Command run | Result | Timestamp |
|-------|-------------|--------|-----------|
| Python lint | `python -m ruff check .` | Pass | 2026-08-31 |
| Python tests | `python -m pytest` | 19 passed | 2026-08-31 |
| Offline assessment | `oracle-azure-migrate demo-assess` | Pass | 2026-08-31 |
| Compose model | `docker compose config --quiet` | Pass | 2026-08-31 |
| Bicep compile | `az bicep build --file infra/main.bicep --stdout` | Pass | 2026-08-31 |
| Python package | `python -m pip wheel --no-deps --wheel-dir dist .` | Pass | 2026-08-31 |
| AZD package | `azd package --no-prompt` | Pass | 2026-08-31 |
| Secret/property scan | `rg` over source and Bicep | Pass | 2026-08-31 |
| Static role review | Review `infra/` for role assignments | Pass; no workload identity or RBAC assignment required | 2026-08-31 |
| Oracle runtime | `docker compose up -d --wait` | Blocked: Docker Desktop engine inactive | 2026-08-31 |

**Validated by:** azure-validate skill
**Validation scope:** Source, package, Compose model, AZD configuration, and
Bicep static validation. Live Azure policy and provisioning checks were excluded
because the user explicitly skipped deployment.

---

## 9. Files to Generate

| File | Purpose | Status |
|------|---------|--------|
| `.azure/deployment-plan.md` | Source-of-truth implementation plan | Complete |
| `README.md` | Setup, architecture, walkthrough, and cleanup | Complete |
| `pyproject.toml` | Python package and test configuration | Complete |
| `src/oracle_azure_migrate/` | Mapping assessment and validation logic | Complete |
| `config/type-mappings.yml` | Default and column-level mapping rules | Complete |
| `oracle/01_create_demo.sql` | Oracle schema and edge-case sample data | Complete |
| `ssma/README.md` | SSMA assessment, mapping, conversion, and migration procedure | Complete |
| `sql/` | Post-migration semantic validation and optional remediation | Complete |
| `docker-compose.yml` | Local Oracle Database Free source | Complete |
| `azure.yaml` | Optional AZD provisioning entry point | Complete |
| `infra/main.bicep` | Optional Entra-only Azure SQL resources | Complete |
| `scripts/` | Demo automation | Complete |
| `tests/` | Mapping and assessment coverage | Complete |
| `.github/workflows/test.yml` | CI validation | Complete |

---

## 10. Functional Verification

- **Status:** Partially verified
- **Assessment utility:** Tested locally
- **SSMA desktop flow:** Documented; requires interactive SSMA installation
- **Oracle source runtime:** Blocked because Docker Desktop was not running
- **Azure SQL target:** Not deployed at user request

## 11. Next Step

Run the `azure-validate` skill, then publish the validated repository.
