[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReleaseTag,
    [string]$OutputPath = "",
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

$escapedTag = $ReleaseTag.Replace("\", "\\").Replace('"', '\"')
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
                string owner = "$escapedOwner";
                string repo = "$escapedRepo";

                string tempRoot = Path.Combine(Path.GetTempPath(), "acd-bootstrap-" + DateTime.UtcNow.ToString("yyyyMMddHHmmss"));
                Directory.CreateDirectory(tempRoot);
                string zipPath = Path.Combine(tempRoot, "acd-source.zip");
                string extractRoot = Path.Combine(tempRoot, "repo");
                Directory.CreateDirectory(extractRoot);
                string appRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AlbionCommandDesk");
                Directory.CreateDirectory(appRoot);
                string safeTag = SanitizePathSegment(releaseTag);
                string installRoot = Path.Combine(appRoot, "runtime", safeTag);
                string venvPath = Path.Combine(appRoot, "venv");

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
                if (Directory.Exists(installRoot))
                {
                    Directory.Delete(installRoot, true);
                }
                Directory.CreateDirectory(Path.GetDirectoryName(installRoot));
                CopyDirectory(repoRoot, installRoot);

                string installScript = Path.Combine(installRoot, "tools", "install", "windows", "install.ps1");
                if (!File.Exists(installScript))
                {
                    throw new FileNotFoundException("install.ps1 not found in extracted repository.", installScript);
                }

                string psArgs = "-NoProfile -ExecutionPolicy Bypass -File " + Quote(installScript)
                    + " -ProjectRoot " + Quote(installRoot)
                    + " -VenvPath " + Quote(venvPath)
                    + " -SkipCaptureExtras"
                    + " -SkipRun";

                Console.WriteLine("[ACD bootstrap] Starting installer...");
                int exitCode = RunProcess("powershell.exe", psArgs);
                if (exitCode != 0)
                {
                    Console.Error.WriteLine("[ACD bootstrap] Installer failed with exit code " + exitCode + ".");
                    Console.Error.WriteLine("[ACD bootstrap] Press Enter to close this window.");
                    Console.ReadLine();
                    return exitCode;
                }

                string cliPath = Path.Combine(venvPath, "Scripts", "albion-command-desk.exe");
                Console.WriteLine("[ACD bootstrap] Install complete.");
                Console.WriteLine("[ACD bootstrap] Runtime root: " + installRoot);
                Console.WriteLine("[ACD bootstrap] Virtual environment: " + venvPath);
                if (File.Exists(cliPath))
                {
                    TryCreateShortcuts(cliPath, installRoot);
                    Console.WriteLine("[ACD bootstrap] Start app with:");
                    Console.WriteLine("  " + cliPath + " core");
                    Console.WriteLine("  " + cliPath + " live   # requires Npcap Runtime");
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

        private static void TryCreateShortcuts(string cliPath, string installRoot)
        {
            try
            {
                string workDir = Path.GetDirectoryName(cliPath) ?? "";
                string iconPath = Path.Combine(installRoot, "albion_dps", "qt", "ui", "command_desk_icon.ico");
                string desktopLink = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
                    "Albion Command Desk.lnk");
                string startMenuDir = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "Microsoft",
                    "Windows",
                    "Start Menu",
                    "Programs",
                    "Albion Command Desk");
                Directory.CreateDirectory(startMenuDir);
                string startMenuLink = Path.Combine(startMenuDir, "Albion Command Desk.lnk");

                CreateShortcut(desktopLink, cliPath, "core", workDir, iconPath);
                CreateShortcut(startMenuLink, cliPath, "core", workDir, iconPath);
                Console.WriteLine("[ACD bootstrap] Shortcuts created:");
                Console.WriteLine("  Desktop: " + desktopLink);
                Console.WriteLine("  Start Menu: " + startMenuLink);
            }
            catch (Exception shortcutError)
            {
                Console.WriteLine("[ACD bootstrap] WARNING: unable to create shortcuts: " + shortcutError.Message);
            }
        }

        private static void CreateShortcut(string shortcutPath, string targetPath, string args, string workDir, string iconPath)
        {
            string command = "`$ws=New-Object -ComObject WScript.Shell; "
                + "`$lnk=`$ws.CreateShortcut('" + EscapeForSingleQuotedPowershell(shortcutPath) + "'); "
                + "`$lnk.TargetPath='" + EscapeForSingleQuotedPowershell(targetPath) + "'; "
                + "`$lnk.Arguments='" + EscapeForSingleQuotedPowershell(args) + "'; "
                + "`$lnk.WorkingDirectory='" + EscapeForSingleQuotedPowershell(workDir) + "'; "
                + "if (Test-Path '" + EscapeForSingleQuotedPowershell(iconPath) + "') { "
                + "  `$lnk.IconLocation='" + EscapeForSingleQuotedPowershell(iconPath) + "' "
                + "}; "
                + "`$lnk.Save()";

            int exitCode = RunProcess(
                "powershell.exe",
                "-NoProfile -ExecutionPolicy Bypass -Command " + Quote(command)
            );
            if (exitCode != 0)
            {
                throw new InvalidOperationException("shortcut command failed with exit code " + exitCode + " for: " + shortcutPath);
            }
        }

        private static string EscapeForSingleQuotedPowershell(string value)
        {
            if (value == null)
            {
                return "";
            }
            return value.Replace("'", "''");
        }

        private static string SanitizePathSegment(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return "latest";
            }
            foreach (char c in Path.GetInvalidFileNameChars())
            {
                value = value.Replace(c, '_');
            }
            value = value.Replace("/", "_").Replace("\\", "_");
            return value.Trim();
        }

        private static void CopyDirectory(string source, string destination)
        {
            Directory.CreateDirectory(destination);
            foreach (string file in Directory.GetFiles(source))
            {
                string targetFile = Path.Combine(destination, Path.GetFileName(file));
                File.Copy(file, targetFile, true);
            }
            foreach (string dir in Directory.GetDirectories(source))
            {
                string targetDir = Path.Combine(destination, Path.GetFileName(dir));
                CopyDirectory(dir, targetDir);
            }
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
