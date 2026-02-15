<p align="center">
  <img src="assets/Logo.png" alt="Albion Command Desk" width="620">
</p>

# Albion Command Desk

Passive Albion Online companion app with a Qt desktop UI:
- DPS/HPS meter (live or PCAP replay)
- Party-only combat aggregation (self + party)
- Optional scanner helper tab
- Market crafting workspace (inputs/outputs/results)

No game client hooks, no overlays, no memory editing.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey">
  <img src="https://img.shields.io/badge/Game-Albion%20Online-orange">
</p>

## Support the Project
If Albion Command Desk saves you time or silver, consider supporting future updates and maintenance.

<p align="center">
  <a href="https://www.paypal.com/donate/?business=albiosuperacc%40linuxmail.org&currency_code=USD&amount=20.00"><img src="https://img.shields.io/badge/PayPal-Donate-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal (default $20, editable on PayPal page)"></a>
  <a href="https://buycoffee.to/ao-dps/"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?style=for-the-badge" alt="Buy Me a Coffee"></a>
</p>

Donors can be featured on a public supporters list. If you want to be listed, open a GitHub issue and share the display name you want to use.

## Screenshots
<p align="center">
  <img src="assets/meter.png" alt="Meter tab" width="920">
</p>

<p align="center">
  <img src="assets/market.png" alt="Market tab" width="920">
</p>

<p align="center">
  <img src="assets/scanner.png" alt="Scanner tab" width="920">
</p>

## Before Install (Recommended)
Best setup before installing ACD:
- Python `3.11` or `3.12` (64-bit) with `pip` available in terminal.
- `git` installed (if you install from source checkout).
- Windows live capture: Npcap Runtime (`https://npcap.com/#download`).
- Linux/macOS live capture: system packet-capture libs (`libpcap`).
- Permissions to create a local virtual environment (`venv` folder in repo).

## Install (Step by Step)

### Windows (clean machine, detailed)
Use this exact sequence in **PowerShell as Administrator**.

Video tutorial:
- https://youtu.be/26Ul7UEx194

1) Allow scripts for this session only:
```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
```

2) Install required tools:
```powershell
winget source update
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements
winget install -e --id Microsoft.DotNet.SDK.10 --accept-package-agreements --accept-source-agreements
winget install -e --id Microsoft.VisualStudio.2022.BuildTools --accept-package-agreements --accept-source-agreements --override "--wait --passive --norestart --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows11SDK.22621 --includeRecommended"
```

3) Install packet-capture prerequisites:
- Install **Npcap Runtime** from `https://npcap.com/#download`.
- During setup, enable **WinPcap API-compatible mode**.
- Download and extract **Npcap SDK** to `C:\npcap-sdk` (or another known folder).

4) Verify toolchain:
```powershell
python --version
git --version
dotnet --list-sdks
Get-ChildItem C:\npcap-sdk -Recurse -Filter pcap.h
```

5) Clone repository and enter project directory:
```powershell
cd "$HOME\Downloads"
git clone https://github.com/D4dits/Albion-Command-Desk.git
cd ".\Albion-Command-Desk"
```

6) Export Npcap SDK paths for current terminal session:
```powershell
$env:WPCAPDIR="C:\npcap-sdk"
$env:INCLUDE="$env:WPCAPDIR\Include\pcap;$env:WPCAPDIR\Include;$env:INCLUDE"
$env:LIB="$env:WPCAPDIR\Lib\x64;$env:LIB"
```

7) Run bootstrap installer:
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -ForceRecreateVenv -SkipRun
```

8) Generate item/map databases (required for full market + map labels):
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\extract_items\run_extract_items.ps1 -GameRoot "C:\Program Files\Albion Online"
```
For Steam install:
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\extract_items\run_extract_items.ps1 -GameRoot "C:\Program Files (x86)\Steam\steamapps\common\Albion Online"
```

9) Start app:
```powershell
.\venv\Scripts\albion-command-desk.exe live
```

10) Fallback if capture build still fails:
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -SkipCaptureExtras -ForceRecreateVenv -SkipRun
```
This installs UI/core without packet-capture extension.

Notes:
- Run commands from the repo root (`Albion-Command-Desk`), not from `C:\Windows\System32`.
- If `Activate.ps1` opens as text or fails with policy error, use installer commands above and avoid manual activation.
- If Python points to Windows Store alias unexpectedly, disable App Execution Alias for `python.exe` in Windows settings.

### Linux/macOS quick setup
```bash
git clone https://github.com/D4dits/Albion-Command-Desk.git
cd Albion-Command-Desk
bash ./tools/install/linux/install.sh
# macOS: bash ./tools/install/macos/install.sh
```

### What bootstrap installer does
- checks Python and required tools
- creates/reuses local `venv`
- installs ACD (`.[capture]` by default)
- runs smoke checks (CLI import + Qt startup probe)
- starts app in `live` mode (unless skip-run option is used)

## Run
If you used bootstrap installer with `-SkipRun`, start from the repo venv:

Windows:
```powershell
.\venv\Scripts\albion-command-desk live
```

Linux/macOS:
```bash
./venv/bin/albion-command-desk live
```

PCAP replay:
```powershell
albion-command-desk replay .\path\to\capture.pcap
```

Interface selection:
```powershell
albion-command-desk live --list-interfaces
albion-command-desk live --interface "Ethernet"
```

## Key Runtime Flags
- `--sort dmg|dps|heal|hps`
- `--top <N>`
- `--mode battle|zone|manual`
- `--history <N>`
- `--battle-timeout <seconds>`
- `--self-name "<name>"`
- `--self-id <entity_id>`
- `--debug`

## Item/Map Databases (optional but recommended)
For weapon-color mapping and map names (`Lazygrass Plain` etc.) generate local files:
- `data/indexedItems.json`
- `data/items.json`
- `data/map_index.json`

Windows:
```powershell
.\tools\extract_items\run_extract_items.ps1 -GameRoot "C:\Program Files\Albion Online"
```

Linux/macOS:
```bash
./tools/extract_items/run_extract_items.sh --game-root "/path/to/Albion Online"
```

If missing, app falls back gracefully and can prompt for game path.

## Market Dataset Pipeline
Build market recipes from local game files:

Windows:
```powershell
.\tools\market\run_build_recipes_from_items.ps1 -Strict
```

Linux/macOS:
```bash
./tools/market/run_build_recipes_from_items.sh
```

Output:
- `albion_dps/market/data/recipes.json`
- `artifacts/market/recipes_from_items_report.json`
- `artifacts/market/recipes_build_report.json`

## Release Metadata (Update Contract)
Update notifications and installer discovery use a release manifest contract:
- Spec: `docs/release/RELEASE_MANIFEST_SPEC.md`
- Example payload: `tools/release/manifest/manifest.example.json`
- Builder: `tools/release/manifest/build_manifest.py`
- Publisher helper (Windows): `tools/release/manifest/publish_manifest.ps1`
- CI publisher: `.github/workflows/release-manifest.yml`
- Default runtime endpoint: `https://github.com/D4dits/Albion-Command-Desk/releases/latest/download/manifest.json`
- Clean-machine bootstrap smoke CI: `.github/workflows/bootstrap-smoke.yml`
- Runtime override endpoint: set `ALBION_COMMAND_DESK_MANIFEST_URL`
- UI controls: `Auto update` toggle + `Check now` action in the header

## Troubleshooting and Docs
- `docs/DELIVERY_BACKLOG.md` (active ticket queue and implementation order)
- `CHANGELOG.md` (all delivered changes)
- `docs/TROUBLESHOOTING.md`
- `docs/ARCHITECTURE.md`
- `docs/MARKET_ARCHITECTURE.md`
- `docs/MARKET_TROUBLESHOOTING.md`
- `docs/MARKET_DATASET_UPDATE.md`
- `docs/release/RELEASE_CHECKLIST.md`

## Tests
```powershell
python -m pytest -q
```

If Windows temp permissions break pytest, set:
```powershell
$env:TEMP="$PWD\\artifacts\\tmp"
$env:TMP=$env:TEMP
python -m pytest -q
```
