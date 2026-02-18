param(
    [Parameter(Mandatory = $true)]
    [string]$Tag,
    [string]$AssetName = "manifest.json",
    [string]$PointerPath = "tools/release/manifest/last_known_good.json"
)

$ErrorActionPreference = "Stop"

if (-not ($Tag -match "^v\d+\.\d+\.\d+([\-+].+)?$")) {
    throw "Tag must look like vX.Y.Z (received: $Tag)"
}

$pointer = [ordered]@{
    tag = $Tag
    asset_name = $AssetName
    updated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    notes = "Update this pointer after each validated release."
}

$targetPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $PointerPath))
$targetDir = Split-Path -Path $targetPath -Parent
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
$json = ($pointer | ConvertTo-Json -Depth 4) + [Environment]::NewLine
[System.IO.File]::WriteAllText($targetPath, $json, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "[lkg] Updated pointer: $targetPath"
Write-Host "[lkg] tag=$Tag asset=$AssetName"
