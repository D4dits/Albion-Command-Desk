param(
  [Parameter(Mandatory = $true)]
  [string]$GameRoot,
  [string]$OutputDir = "",
  [ValidateSet("live","staging","playground")]
  [string]$Server = "live"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\\..")
$toolProject = Join-Path $PSScriptRoot "ExtractItems.csproj"
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
  $OutputDir = Join-Path $repoRoot "data"
}

$env:DOTNET_CLI_HOME = Join-Path $repoRoot "artifacts\\dotnet"
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = "1"
$env:NUGET_PACKAGES = Join-Path $repoRoot "artifacts\\nuget"

dotnet build $toolProject -c Release | Out-Host
dotnet run --project $toolProject -c Release -- --game-root "$GameRoot" --output "$OutputDir" --server "$Server"
