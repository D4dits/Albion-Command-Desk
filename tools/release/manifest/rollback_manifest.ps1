param(
    [string]$TargetTag = "",
    [string]$PointerPath = "tools/release/manifest/last_known_good.json"
)

$ErrorActionPreference = "Stop"

function Invoke-Gh {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )
    $output = & gh @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "gh $($Args -join ' ') failed: $output"
    }
    return $output
}

$pointerFullPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $PointerPath))
if (-not (Test-Path -LiteralPath $pointerFullPath)) {
    throw "LKG pointer missing: $pointerFullPath"
}

$pointerRaw = Get-Content -Raw -Encoding utf8 -Path $pointerFullPath
$pointer = $pointerRaw | ConvertFrom-Json
$sourceTag = [string]$pointer.tag
$sourceAsset = [string]$pointer.asset_name
if ([string]::IsNullOrWhiteSpace($sourceTag) -or [string]::IsNullOrWhiteSpace($sourceAsset)) {
    throw "Invalid LKG pointer. Required keys: tag, asset_name"
}

if ([string]::IsNullOrWhiteSpace($TargetTag)) {
    $TargetTag = (Invoke-Gh -Args @("release", "view", "--json", "tagName", "--jq", ".tagName")).Trim()
}
if ([string]::IsNullOrWhiteSpace($TargetTag)) {
    throw "Unable to resolve target release tag."
}

$tempDir = Join-Path $env:TEMP ("acd-manifest-rollback-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

try {
    Invoke-Gh -Args @("release", "download", $sourceTag, "-p", $sourceAsset, "-D", $tempDir, "--clobber") | Out-Null
    $sourcePath = Join-Path $tempDir $sourceAsset
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        throw "Downloaded source manifest asset not found: $sourcePath"
    }

    $uploadArg = "$sourcePath#manifest.json"
    Invoke-Gh -Args @("release", "upload", $TargetTag, $uploadArg, "--clobber") | Out-Null
} finally {
    Remove-Item -Recurse -Force -Path $tempDir -ErrorAction SilentlyContinue
}

Write-Host "[rollback] Restored manifest.json on release $TargetTag from $sourceTag/$sourceAsset"
