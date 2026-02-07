Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$rootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$rawDir = Join-Path $rootDir "artifacts/raw"
$unknownDir = Join-Path $rootDir "artifacts/unknown"
$artifactsDir = Join-Path $rootDir "artifacts"

if (Test-Path $rawDir) {
  Remove-Item -Recurse -Force $rawDir
}
if (Test-Path $unknownDir) {
  Remove-Item -Recurse -Force $unknownDir
}
if (-not (Test-Path $artifactsDir)) {
  New-Item -ItemType Directory -Path $artifactsDir | Out-Null
}
