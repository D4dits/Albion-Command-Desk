[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [string]$VenvPath = "",
    [string]$Python = "",
    [ValidateSet("core", "capture")]
    [string]$Profile = "core",
    [string]$ReleaseVersion = "local-dev",
    [switch]$SkipRun,
    [switch]$NonInteractive,
    [switch]$ForceRecreateVenv,
    [switch]$SkipCaptureExtras,
    [switch]$StrictCapture
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

function Write-InstallHint {
    param([string]$Message)
    Write-Host "[ACD install] hint: $Message" -ForegroundColor DarkGray
}

function Throw-InstallError {
    param([string]$Message)
    throw "[ACD install] $Message"
}

function Test-NpcapRuntime {
    $dllCandidates = @(
        "$env:WINDIR\\System32\\Npcap\\wpcap.dll",
        "$env:WINDIR\\System32\\Npcap\\Packet.dll",
        "$env:WINDIR\\SysWOW64\\Npcap\\wpcap.dll",
        "$env:WINDIR\\SysWOW64\\Npcap\\Packet.dll"
    )
    foreach ($candidate in $dllCandidates) {
        if (Test-Path $candidate) {
            return @{
                Available = $true
                Detail = "Detected runtime DLL: $candidate"
            }
        }
    }
    return @{
        Available = $false
        Detail = "Npcap Runtime not detected in standard locations."
    }
}

function Test-NpcapSdk {
    $includeCandidates = @(
        "C:\\WpdPack\\Include\\pcap.h",
        "$env:ProgramFiles\\Npcap SDK\\Include\\pcap.h",
        "${env:ProgramFiles(x86)}\\Npcap SDK\\Include\\pcap.h"
    )
    foreach ($candidate in $includeCandidates) {
        if (Test-Path $candidate) {
            return @{
                Available = $true
                Detail = "Detected SDK header: $candidate"
            }
        }
    }
    return @{
        Available = $false
        Detail = "Npcap SDK header (pcap.h) not found."
    }
}

function Show-InstallDiagnostics {
    param(
        [string]$ProjectRootPath,
        [string]$VirtualEnvPath,
        [string]$InstallProfile,
        [hashtable]$LauncherInfo,
        [string]$PrimaryArtifactName
    )
    Write-InstallInfo "Diagnostic summary:"
    Write-InstallInfo "  project_root: $ProjectRootPath"
    Write-InstallInfo "  venv_path: $VirtualEnvPath"
    Write-InstallInfo "  profile: $InstallProfile"
    Write-InstallInfo "  expected_primary_artifact: $PrimaryArtifactName"
    Write-InstallInfo "  python: $($LauncherInfo.Command -join ' ') (version $($LauncherInfo.Version))"
    $vcTools = Get-Command "cl.exe" -ErrorAction SilentlyContinue
    if ($vcTools) {
        Write-InstallInfo "  c_compiler: available ($($vcTools.Source))"
    } else {
        Write-InstallWarn "  c_compiler: not detected (capture profile may fail to build pcap backend)"
        Write-InstallHint "For core mode this is expected and safe."
    }
    if ($InstallProfile -eq "capture") {
        $npcap = Test-NpcapRuntime
        if ($npcap.Available) {
            Write-InstallInfo "  npcap_runtime: available ($($npcap.Detail))"
        } else {
            Write-InstallWarn "  npcap_runtime: missing ($($npcap.Detail))"
            Write-InstallHint "Install Npcap Runtime from https://npcap.com/#download before running live mode."
        }
        $sdk = Test-NpcapSdk
        if ($sdk.Available) {
            Write-InstallInfo "  npcap_sdk: available ($($sdk.Detail))"
        } else {
            Write-InstallWarn "  npcap_sdk: missing ($($sdk.Detail))"
            Write-InstallHint "Capture profile will fall back to core mode unless -StrictCapture is used."
        }
    } else {
        Write-InstallInfo "  npcap_runtime: optional (core mode selected)"
    }
}

function Get-WindowsPrimaryArtifactName {
    param([string]$Version = "local-dev")
    return "AlbionCommandDesk-Setup-v$Version-x86_64.exe"
}

function Resolve-PythonLauncher {
    param(
        [string]$RequestedPython = ""
    )
    if ($RequestedPython) {
        if (-not (Test-Path $RequestedPython)) {
            Throw-InstallError "Requested Python path does not exist: $RequestedPython"
        }
        $versionString = ""
        try {
            $versionString = (& $RequestedPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
        } catch {
            Throw-InstallError "Failed to execute requested Python: $RequestedPython"
        }
        $parts = $versionString.Split(".")
        if ($parts.Count -lt 2) {
            Throw-InstallError "Could not parse requested Python version from: $RequestedPython"
        }
        $major = [int]$parts[0]
        $minor = [int]$parts[1]
        if (-not ($major -eq 3 -and $minor -ge 10)) {
            Throw-InstallError "Requested Python must be 3.10+ (detected: $versionString)"
        }
        return @{
            Command = @($RequestedPython)
            Version = $versionString
        }
    }

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
        [string[]]$Launcher,
        [string[]]$CommandArgs,
        [string]$Description
    )
    if (-not $Launcher -or $Launcher.Count -eq 0) {
        Throw-InstallError "Python launcher command is empty for step: $Description"
    }
    $exe = $Launcher[0]
    $baseArgs = @()
    if ($Launcher.Count -gt 1) {
        $baseArgs = $Launcher[1..($Launcher.Count - 1)]
    }
    Write-InstallInfo $Description
    $rendered = @($exe) + $baseArgs + $CommandArgs
    Write-InstallInfo ("Command: " + ($rendered -join " "))
    & $exe @baseArgs @CommandArgs
    Write-InstallInfo "Exit code: $LASTEXITCODE"
    if ($LASTEXITCODE -ne 0) {
        Throw-InstallError "$Description failed with exit code $LASTEXITCODE."
    }
}

function Resolve-VenvPython {
    param(
        [string]$VenvRoot
    )
    if ([string]::IsNullOrWhiteSpace($VenvRoot)) {
        return $null
    }
    $scriptsPath = Join-Path $VenvRoot "Scripts"
    if (-not (Test-Path $scriptsPath)) {
        return $null
    }

    $preferred = @(
        "python.exe",
        "python3.exe",
        "python3.12.exe",
        "python3.11.exe",
        "python3.10.exe"
    )
    foreach ($name in $preferred) {
        $candidate = Join-Path $scriptsPath $name
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $fallback = Get-ChildItem -Path $scriptsPath -Filter "python*.exe" -File -ErrorAction SilentlyContinue |
        Sort-Object Name |
        Select-Object -First 1
    if ($fallback) {
        return $fallback.FullName
    }

    return $null
}

if (-not $ProjectRoot) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}
if (-not $VenvPath) {
    $VenvPath = Join-Path $ProjectRoot "venv"
}
if ([string]::IsNullOrWhiteSpace($VenvPath)) {
    Throw-InstallError "VenvPath is empty after parameter resolution."
}
Write-InstallInfo "Resolved virtual environment path: $VenvPath"

$pyprojectPath = Join-Path $ProjectRoot "pyproject.toml"
if (-not (Test-Path $pyprojectPath)) {
    Throw-InstallError "pyproject.toml not found under '$ProjectRoot'. Run this from the repository."
}

$launcher = Resolve-PythonLauncher -RequestedPython $Python
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
    Invoke-WithLauncher -Launcher $launcher.Command -CommandArgs @("-m", "venv", $VenvPath) -Description "Creating virtual environment"
} else {
    Write-InstallInfo "Using existing virtual environment: $VenvPath"
}

$venvPython = Resolve-VenvPython -VenvRoot $VenvPath
if (-not $venvPython) {
    Write-InstallWarn "No Python executable found in venv after first creation attempt. Retrying with --copies."
    Invoke-WithLauncher -Launcher $launcher.Command -CommandArgs @("-m", "venv", "--copies", $VenvPath) -Description "Recreating virtual environment with --copies"
    $venvPython = Resolve-VenvPython -VenvRoot $VenvPath
}
if (-not $venvPython) {
    Write-InstallWarn "venv module did not create a usable interpreter. Falling back to virtualenv."
    if (Test-Path $VenvPath) {
        Remove-Item -Recurse -Force $VenvPath
    }
    Invoke-WithLauncher -Launcher $launcher.Command -CommandArgs @("-m", "pip", "install", "--upgrade", "virtualenv") -Description "Installing virtualenv fallback"
    Invoke-WithLauncher -Launcher $launcher.Command -CommandArgs @("-m", "virtualenv", $VenvPath) -Description "Creating virtual environment with virtualenv"
    $venvPython = Resolve-VenvPython -VenvRoot $VenvPath
}

$venvCli = Join-Path $VenvPath "Scripts\albion-command-desk.exe"
$smokeScript = Join-Path $ProjectRoot "tools\install\common\smoke_check.py"

if ([string]::IsNullOrWhiteSpace($venvPython) -or (-not (Test-Path $venvPython))) {
    if ([string]::IsNullOrWhiteSpace($VenvPath)) {
        Throw-InstallError "VenvPath is empty while validating virtual environment."
    }
    $scriptsPath = Join-Path $VenvPath "Scripts"
    $visible = ""
    if (Test-Path $scriptsPath) {
        $visible = (Get-ChildItem -Path $scriptsPath -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name) -join ", "
    }
    if (-not $visible) {
        $visible = "<none>"
    }
    Throw-InstallError "Virtual environment is missing a Python executable under '$scriptsPath'. Files: $visible"
}

Write-InstallInfo "Upgrading pip"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Throw-InstallError "pip upgrade failed."
}

if ($SkipCaptureExtras) {
    Write-InstallWarn "SkipCaptureExtras is deprecated. Use -Profile core."
    $Profile = "core"
}
if ($NonInteractive) {
    $env:PIP_NO_INPUT = "1"
    $env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
    $SkipRun = $true
    Write-InstallInfo "NonInteractive mode enabled (pip prompts disabled, SkipRun forced)."
}
if ($Profile -eq "core") {
    Write-InstallInfo "Install profile: core (UI + market/scanner/replay, no live capture backend)"
} else {
    Write-InstallInfo "Install profile: capture (includes live capture backend)"
}
$primaryArtifact = Get-WindowsPrimaryArtifactName -Version $ReleaseVersion
Show-InstallDiagnostics -ProjectRootPath $ProjectRoot -VirtualEnvPath $VenvPath -InstallProfile $Profile -LauncherInfo $launcher -PrimaryArtifactName $primaryArtifact
$captureSdkStatus = $null
if ($Profile -eq "capture") {
    $captureSdkStatus = Test-NpcapSdk
    if (-not $captureSdkStatus.Available) {
        if ($StrictCapture) {
            Throw-InstallError "Capture profile requested with -StrictCapture, but Npcap SDK was not found."
        }
        Write-InstallWarn "Capture profile requested, but SDK is unavailable. Falling back to core profile."
        Write-InstallHint "Install Npcap SDK + build tools if you want capture build on Windows."
        $Profile = "core"
    }
}
$installTarget = if ($Profile -eq "capture") { ".[capture]" } else { "." }
Write-InstallInfo "Installing Albion Command Desk ($installTarget)"
Push-Location $ProjectRoot
try {
    & $venvPython -m pip install -e $installTarget
    if ($LASTEXITCODE -ne 0) {
        if ($Profile -eq "core") {
            Throw-InstallError "Package install failed."
        }
        if ($StrictCapture) {
            Throw-InstallError "Capture profile installation failed in strict mode. Verify build tools and packet capture prerequisites."
        }
        Write-InstallWarn "Capture profile installation failed; falling back to core profile."
        Write-InstallHint "Use -StrictCapture if you want this to fail instead of fallback."
        $Profile = "core"
        $installTarget = "."
        & $venvPython -m pip install -e $installTarget
        if ($LASTEXITCODE -ne 0) {
            Throw-InstallError "Core profile fallback install failed."
        }
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
& $venvPython $smokeScript --project-root $ProjectRoot --profile $Profile --artifact-name $primaryArtifact
if ($LASTEXITCODE -ne 0) {
    Throw-InstallError "Shared smoke checks failed."
}

if ($SkipRun) {
    Write-InstallInfo "Installation complete. Launch manually with:"
    if ($Profile -eq "capture") {
        Write-Host "  $venvCli live"
    } else {
        Write-Host "  $venvCli core"
        Write-Host "  $venvCli live   # after reinstall with -Profile capture"
    }
    exit 0
}

if ($Profile -eq "capture") {
    Write-InstallInfo "Starting Albion Command Desk (live mode)"
} else {
    Write-InstallInfo "Starting Albion Command Desk (core mode)"
}
if (Test-Path $venvCli) {
    if ($Profile -eq "capture") {
        & $venvCli live
    } else {
        & $venvCli core
    }
    exit $LASTEXITCODE
}

if ($Profile -eq "capture") {
    & $venvPython -m albion_dps.cli live
} else {
    & $venvPython -m albion_dps.cli core
}
exit $LASTEXITCODE
