param(
    [string] $Path = ".env"
)

if (-not (Test-Path $Path)) {
    throw "$Path does not exist. Copy .env.example to .env and fill in local values."
}

foreach ($line in Get-Content $Path) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) {
        continue
    }
    $name, $value = $trimmed -split "=", 2
    if (-not $name -or $null -eq $value) {
        throw "Invalid environment entry: $line"
    }
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
}

