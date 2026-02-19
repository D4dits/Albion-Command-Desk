[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReleaseTag,
    [string]$OutputPath = "",
    [ValidateSet("core", "capture")]
    [string]$Profile = "core",
    [string]$RepositoryOwner = "D4dits",
    [string]$RepositoryName = "Albion-Command-Desk"
)

$ErrorActionPreference = "Stop"

function Write-BuildInfo {
    param([string]$Message)
    Write-Host "[ACD bootstrap build] $Message" -ForegroundColor Cyan
}

if (-not $ReleaseTag.StartsWith("v")) {
    Write-BuildInfo "ReleaseTag does not start with 'v'; treating it as a branch name."
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
if (-not $OutputPath) {
    $OutputPath = Join-Path $projectRoot ("dist\installer\AlbionCommandDesk-Setup-$ReleaseTag-x86_64.exe")
}
$outputDir = Split-Path -Parent $OutputPath
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$releaseVersion = $ReleaseTag.TrimStart("v", "V")
$escapedTag = $ReleaseTag.Replace("\", "\\").Replace('"', '\"')
$escapedVersion = $releaseVersion.Replace("\", "\\").Replace('"', '\"')
$escapedProfile = $Profile.Replace("\", "\\").Replace('"', '\"')
$escapedOwner = $RepositoryOwner.Replace("\", "\\").Replace('"', '\"')
$escapedRepo = $RepositoryName.Replace("\", "\\").Replace('"', '\"')

$source = @"
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;

namespace AlbionCommandDeskBootstrap
{
    internal static class Program
    {
        private static int Main(string[] args)
        {
            try
            {
                string releaseTag = "$escapedTag";
                string releaseVersion = "$escapedVersion";
                string profile = "$escapedProfile";
                string owner = "$escapedOwner";
                string repo = "$escapedRepo";

                string tempRoot = Path.Combine(Path.GetTempPath(), "acd-bootstrap-" + DateTime.UtcNow.ToString("yyyyMMddHHmmss"));
                Directory.CreateDirectory(tempRoot);
                string zipPath = Path.Combine(tempRoot, "acd-source.zip");
                string extractRoot = Path.Combine(tempRoot, "repo");
                Directory.CreateDirectory(extractRoot);

                string zipUrl = BuildZipUrl(owner, repo, releaseTag);
                Console.WriteLine("[ACD bootstrap] Downloading source: " + zipUrl);
                ConfigureSecurityProtocols();
                DownloadSource(zipUrl, zipPath);

                Console.WriteLine("[ACD bootstrap] Extracting source...");
                ZipFile.ExtractToDirectory(zipPath, extractRoot);

                string repoRoot = Directory.GetDirectories(extractRoot).FirstOrDefault();
                if (string.IsNullOrWhiteSpace(repoRoot))
                {
                    throw new InvalidOperationException("Repository archive extraction failed.");
                }

                string installScript = Path.Combine(repoRoot, "tools", "install", "windows", "install.ps1");
                if (!File.Exists(installScript))
                {
                    throw new FileNotFoundException("install.ps1 not found in extracted repository.", installScript);
                }

                string psArgs = "-NoProfile -ExecutionPolicy Bypass -File " + Quote(installScript)
                    + " -ProjectRoot " + Quote(repoRoot)
                    + " -Profile " + Quote(profile)
                    + " -ReleaseVersion " + Quote(releaseVersion);

                Console.WriteLine("[ACD bootstrap] Starting installer...");
                int exitCode = RunProcess("powershell.exe", psArgs);
                if (exitCode != 0)
                {
                    Console.Error.WriteLine("[ACD bootstrap] Installer failed with exit code " + exitCode + ".");
                    Console.Error.WriteLine("[ACD bootstrap] Press Enter to close this window.");
                    Console.ReadLine();
                    return exitCode;
                }

                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine("[ACD bootstrap] ERROR: " + ex.Message);
                Console.Error.WriteLine("[ACD bootstrap] Press Enter to close this window.");
                Console.ReadLine();
                return 1;
            }
        }

        private static string BuildZipUrl(string owner, string repo, string releaseTag)
        {
            if (!string.IsNullOrWhiteSpace(releaseTag) && releaseTag.StartsWith("v", StringComparison.OrdinalIgnoreCase))
            {
                return "https://github.com/" + owner + "/" + repo + "/archive/refs/tags/" + releaseTag + ".zip";
            }
            return "https://github.com/" + owner + "/" + repo + "/archive/refs/heads/" + releaseTag + ".zip";
        }

        private static void ConfigureSecurityProtocols()
        {
            const SecurityProtocolType Tls11 = (SecurityProtocolType)768;
            const SecurityProtocolType Tls12 = (SecurityProtocolType)3072;
            SecurityProtocolType enabled = Tls11 | Tls12;
            try
            {
                enabled |= (SecurityProtocolType)12288;
            }
            catch
            {
            }
            ServicePointManager.SecurityProtocol = enabled;
            ServicePointManager.Expect100Continue = false;
        }

        private static void DownloadSource(string sourceUrl, string destinationPath)
        {
            try
            {
                using (var client = new WebClient())
                {
                    client.Headers.Add("User-Agent", "AlbionCommandDeskBootstrap/1.0");
                    client.DownloadFile(sourceUrl, destinationPath);
                    return;
                }
            }
            catch (Exception firstError)
            {
                Console.WriteLine("[ACD bootstrap] WebClient download failed: " + firstError.Message);
            }

            Console.WriteLine("[ACD bootstrap] Retrying download via PowerShell Invoke-WebRequest...");
            string psArgs = "-NoProfile -ExecutionPolicy Bypass -Command "
                + Quote("[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; "
                    + "Invoke-WebRequest -UseBasicParsing -Uri " + Quote(sourceUrl) + " -OutFile " + Quote(destinationPath));
            int fallbackCode = RunProcess("powershell.exe", psArgs);
            if (fallbackCode != 0 || !File.Exists(destinationPath))
            {
                throw new InvalidOperationException("Source download failed via WebClient and PowerShell fallback.");
            }
        }

        private static int RunProcess(string fileName, string arguments)
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = arguments,
                UseShellExecute = false
            };
            using (var process = Process.Start(startInfo))
            {
                process.WaitForExit();
                return process.ExitCode;
            }
        }

        private static string Quote(string value)
        {
            if (value == null)
            {
                return "\"\"";
            }
            return "\"" + value.Replace("\"", "\\\"") + "\"";
        }
    }
}
"@

Write-BuildInfo "Compiling bootstrap setup EXE..."
Add-Type `
    -TypeDefinition $source `
    -Language CSharp `
    -OutputType ConsoleApplication `
    -OutputAssembly $OutputPath `
    -ReferencedAssemblies @("System.dll", "System.Core.dll", "System.IO.Compression.FileSystem.dll")

if (-not (Test-Path $OutputPath)) {
    throw "Build failed: output EXE not found at $OutputPath"
}

$outputItem = Get-Item $OutputPath
Write-BuildInfo "Created: $($outputItem.FullName) ($($outputItem.Length) bytes)"
