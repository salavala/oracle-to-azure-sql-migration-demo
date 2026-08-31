[CmdletBinding()]
param(
    [string] $EnvironmentFile = ".env"
)

$ErrorActionPreference = "Stop"

& "$PSScriptRoot\import-env.ps1" -Path $EnvironmentFile

python -m oracle_azure_migrate.cli assess `
    --owner MIGRATION_DEMO `
    --source-table SALES_ORDERS `
    --target-schema dbo `
    --target-table sales_orders `
    --output reports/custom-mapping-assessment.md

if ($LASTEXITCODE -ne 0) {
    throw "Custom mapping assessment failed with exit code $LASTEXITCODE."
}

