[CmdletBinding()]
param(
    [string] $EnvironmentFile = ".env"
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Python environment not found. Run Step 2 from $repositoryRoot, then rerun this script."
}

if (-not [System.IO.Path]::IsPathRooted($EnvironmentFile)) {
    $EnvironmentFile = Join-Path $repositoryRoot $EnvironmentFile
}

& "$PSScriptRoot\import-env.ps1" -Path $EnvironmentFile

Push-Location $repositoryRoot
try {
    & $python -m oracle_azure_migrate.cli assess `
        --owner MIGRATION_DEMO `
        --source-table SALES_ORDERS `
        --target-schema dbo `
        --target-table sales_orders `
        --output reports/custom-mapping-assessment.md

    if ($LASTEXITCODE -ne 0) {
        throw "Custom mapping assessment failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
