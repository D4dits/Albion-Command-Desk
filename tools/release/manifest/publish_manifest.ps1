[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Tag,
    [string]$Repo = "D4dits/Albion-Command-Desk",
    [ValidateSet("stable", "beta", "nightly")]
    [string]$Channel = "stable",
    [string]$MinSupportedVersion = "",
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"

function Resolve-Python {
    param([string]$RequestedPython = "")
    if ($RequestedPython) {
        if (-not (Test-Path $RequestedPython)) {
            throw "Requested Python path does not exist: $RequestedPython"
        }
        return $RequestedPython
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py"
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    throw "Python launcher not found. Install Python 3.10+."
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$manifestPath = Join-Path $projectRoot "tools\release\manifest\manifest.json"
$builderPath = Join-Path $projectRoot "tools\release\manifest\build_manifest.py"
$py = Resolve-Python -RequestedPython $Python

Push-Location $projectRoot
try {
    if ($py -eq "py") {
        & py -3.12 $builderPath --repo $Repo --tag $Tag --channel $Channel --output $manifestPath --min-supported-version $MinSupportedVersion
    } else {
        & $py $builderPath --repo $Repo --tag $Tag --channel $Channel --output $manifestPath --min-supported-version $MinSupportedVersion
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Manifest build failed."
    }

    & "C:\Program Files\GitHub CLI\gh.exe" release upload $Tag $manifestPath --repo $Repo --clobber
    if ($LASTEXITCODE -ne 0) {
        throw "gh release upload failed."
    }
    Write-Host "Manifest published: $manifestPath -> release $Tag" -ForegroundColor Green
}
finally {
    Pop-Location
}
