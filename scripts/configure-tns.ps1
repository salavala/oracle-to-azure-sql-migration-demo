[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$tnsAdmin = Join-Path $repositoryRoot "oracle"
$tnsNames = Join-Path $tnsAdmin "tnsnames.ora"

if (-not (Test-Path $tnsNames)) {
    throw "Oracle network configuration was not found at $tnsNames."
}

[Environment]::SetEnvironmentVariable("TNS_ADMIN", $tnsAdmin, "User")
$env:TNS_ADMIN = $tnsAdmin

Write-Host "TNS_ADMIN=$tnsAdmin"
Write-Host "Configured alias FREEPDB1_DEMO for service freepdb1."
Write-Host "Fully close and reopen SSMA before connecting in TNSNAME mode."

