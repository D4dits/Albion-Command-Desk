[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [string]$VenvPath = "",
    [switch]$SkipRun,
    [switch]$ForceRecreateVenv
)

$ErrorActionPreference = "Stop"

function Write-InstallInfo {
    param([string]$Message)
    Write-Host "[ACD install] $Message" -ForegroundColor Cyan
}

function Write-InstallWarn {
    param([string]$Message)
    Write-Host "[ACD install] $Message" -ForegroundColor Yellow
}

function Throw-InstallError {
    param([string]$Message)
    throw "[ACD install] $Message"
}

function Resolve-PythonLauncher {
    $candidates = @(
        @("py", "-3.12"),
        @("py", "-3.11"),
        @("py", "-3.10"),
        @("python")
    )

    foreach ($candidate in $candidates) {
        $exe = $candidate[0]
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
            continue
        }
        try {
            $args = @()
            if ($candidate.Count -gt 1) {
                $args += $candidate[1..($candidate.Count - 1)]
            }
            $args += @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            $versionString = (& $exe @args).Trim()
            if ($LASTEXITCODE -ne 0) {
                continue
            }
            $parts = $versionString.Split(".")
            if ($parts.Count -lt 2) {
                continue
            }
            $major = [int]$parts[0]
            $minor = [int]$parts[1]
            if ($major -eq 3 -and $minor -ge 10) {
                return @{
                    Command = $candidate
                    Version = $versionString
                }
            }
        } catch {
            continue
        }
    }

    return $null
}

function Invoke-WithLauncher {
    param(
        [array]$Launcher,
        [string[]]$Args,
        [string]$Description
    )
    $exe = $Launcher[0]
    $baseArgs = @()
    if ($Launcher.Count -gt 1) {
        $baseArgs = $Launcher[1..($Launcher.Count - 1)]
    }
    Write-InstallInfo $Description
    & $exe @baseArgs @Args
    if ($LASTEXITCODE -ne 0) {
        Throw-InstallError "$Description failed with exit code $LASTEXITCODE."
    }
}

if (-not $ProjectRoot) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}
if (-not $VenvPath) {
    $VenvPath = Join-Path $ProjectRoot "venv"
}

$pyprojectPath = Join-Path $ProjectRoot "pyproject.toml"
if (-not (Test-Path $pyprojectPath)) {
    Throw-InstallError "pyproject.toml not found under '$ProjectRoot'. Run this from the repository."
}

$launcher = Resolve-PythonLauncher
if (-not $launcher) {
    Throw-InstallError "Python 3.10+ not found. Install Python, then rerun this script."
}

$launcherCmd = ($launcher.Command -join " ")
Write-InstallInfo "Using Python launcher: $launcherCmd (version $($launcher.Version))"
if ($launcher.Version.StartsWith("3.13")) {
    Write-InstallWarn "Python 3.13 may fail to install capture extras on some systems. Prefer Python 3.11/3.12."
}

if ($ForceRecreateVenv -and (Test-Path $VenvPath)) {
    Write-InstallInfo "Removing existing virtual environment: $VenvPath"
    Remove-Item -Recurse -Force $VenvPath
}

if (-not (Test-Path $VenvPath)) {
    Invoke-WithLauncher -Launcher $launcher.Command -Args @("-m", "venv", $VenvPath) -Description "Creating virtual environment"
} else {
    Write-InstallInfo "Using existing virtual environment: $VenvPath"
}

$venvPython = Join-Path $VenvPath "Scripts\python.exe"
$venvCli = Join-Path $VenvPath "Scripts\albion-command-desk.exe"
$smokeScript = Join-Path $ProjectRoot "tools\install\common\smoke_check.py"

if (-not (Test-Path $venvPython)) {
    Throw-InstallError "Virtual environment is missing python.exe: $venvPython"
}

Write-InstallInfo "Upgrading pip"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Throw-InstallError "pip upgrade failed."
}

Write-InstallInfo "Installing Albion Command Desk with capture extras"
Push-Location $ProjectRoot
try {
    & $venvPython -m pip install -e ".[capture]"
    if ($LASTEXITCODE -ne 0) {
        Throw-InstallError "Package install failed. Verify build tools and packet capture prerequisites."
    }
} finally {
    Pop-Location
}

Write-InstallInfo "Verifying CLI entrypoint"
if (Test-Path $venvCli) {
    & $venvCli --version
    if ($LASTEXITCODE -ne 0) {
        Throw-InstallError "CLI smoke check failed."
    }
} else {
    & $venvPython -m albion_dps.cli --version
    if ($LASTEXITCODE -ne 0) {
        Throw-InstallError "Module smoke check failed."
    }
}

if (-not (Test-Path $smokeScript)) {
    Throw-InstallError "Shared smoke check script not found: $smokeScript"
}

Write-InstallInfo "Running shared install smoke checks"
& $venvPython $smokeScript --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    Throw-InstallError "Shared smoke checks failed."
}

if ($SkipRun) {
    Write-InstallInfo "Installation complete. Launch manually with:"
    Write-Host "  $venvCli live"
    exit 0
}

Write-InstallInfo "Starting Albion Command Desk (live mode)"
if (Test-Path $venvCli) {
    & $venvCli live
    exit $LASTEXITCODE
}

& $venvPython -m albion_dps.cli live
exit $LASTEXITCODE
