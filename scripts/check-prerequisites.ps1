[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Test-Command {
    param(
        [Parameter(Mandatory)]
        [string] $Name,
        [Parameter(Mandatory)]
        [string] $InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found. $InstallHint"
    }
    Write-Host "[PASS] $Name"
}

Test-Command -Name "python" -InstallHint "Install Python 3.11 or later."
Test-Command -Name "docker" -InstallHint "Install Docker Desktop."

$ssmaCandidates = @(
    "${env:ProgramFiles}\Microsoft SQL Server Migration Assistant for Oracle\bin\SSMAforOracle.exe",
    "${env:ProgramFiles(x86)}\Microsoft SQL Server Migration Assistant for Oracle\bin\SSMAforOracle.exe"
)
$ssma = $ssmaCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ssma) {
    Write-Warning "SSMA for Oracle was not found. Install it from https://aka.ms/ssmafororacle"
}
else {
    Write-Host "[PASS] SSMA for Oracle: $ssma"
}

$odbc = Get-OdbcDriver -Name "ODBC Driver 18 for SQL Server" -ErrorAction SilentlyContinue
if (-not $odbc) {
    Write-Warning "ODBC Driver 18 for SQL Server was not found. It is needed for validation."
}
else {
    Write-Host "[PASS] ODBC Driver 18 for SQL Server"
}

