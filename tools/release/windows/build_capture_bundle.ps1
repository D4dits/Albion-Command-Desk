[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReleaseTag,
    [string[]]$WheelPaths = @(),
    [string]$WheelDirectory = "",
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

function Write-BuildInfo {
    param([string]$Message)
    Write-Host "[ACD capture bundle] $Message" -ForegroundColor Cyan
}

function Get-WindowsCaptureBundleName {
    param([string]$Tag)
    return "AlbionCommandDesk-WindowsCapture-$Tag.zip"
}

function Resolve-WheelFiles {
    param(
        [string[]]$ExplicitWheelPaths,
        [string]$ExplicitWheelDirectory
    )
    $resolved = New-Object System.Collections.Generic.List[string]

    foreach ($candidate in ($ExplicitWheelPaths | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
        if (-not (Test-Path $candidate)) {
            throw "Wheel path not found: $candidate"
        }
        $item = Resolve-Path $candidate
        $resolved.Add($item.Path)
    }

    if (-not [string]::IsNullOrWhiteSpace($ExplicitWheelDirectory)) {
        if (-not (Test-Path $ExplicitWheelDirectory)) {
            throw "Wheel directory not found: $ExplicitWheelDirectory"
        }
        Get-ChildItem -Path $ExplicitWheelDirectory -Filter "*.whl" -File |
            Sort-Object Name |
            ForEach-Object { $resolved.Add($_.FullName) }
    }

    return $resolved | Select-Object -Unique
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
if (-not $OutputPath) {
    $OutputPath = Join-Path $projectRoot ("dist\windows-capture\" + (Get-WindowsCaptureBundleName -Tag $ReleaseTag))
}
$outputDir = Split-Path -Parent $OutputPath
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}

$wheelFiles = Resolve-WheelFiles -ExplicitWheelPaths $WheelPaths -ExplicitWheelDirectory $WheelDirectory
if (-not $wheelFiles -or $wheelFiles.Count -eq 0) {
    throw "No wheel files found. Use -WheelPaths or -WheelDirectory."
}

$stagingDir = Join-Path $env:TEMP ("acd-windows-capture-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null

try {
    $bundleManifest = [ordered]@{
        schema_version = 1
        release_tag = $ReleaseTag
        generated_at = (Get-Date).ToUniversalTime().ToString("s") + "Z"
        files = @()
    }

    foreach ($wheel in $wheelFiles) {
        $fileName = Split-Path $wheel -Leaf
        Copy-Item $wheel (Join-Path $stagingDir $fileName) -Force
        $bundleManifest.files += [ordered]@{
            name = $fileName
            size = (Get-Item $wheel).Length
        }
    }

    $manifestPath = Join-Path $stagingDir "bundle-manifest.json"
    $bundleManifest | ConvertTo-Json -Depth 4 | Set-Content -Path $manifestPath -Encoding UTF8

    if (Test-Path $OutputPath) {
        Remove-Item -Force $OutputPath
    }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($stagingDir, $OutputPath)
    Write-BuildInfo "Created Windows capture bundle: $OutputPath"
} finally {
    Remove-Item -Recurse -Force $stagingDir -ErrorAction SilentlyContinue
}
