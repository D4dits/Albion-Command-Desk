<p align="center">
  <img src="assets/branding/albion-command-desk-logo-wide-3200.png" alt="Albion Command Desk" width="980">
</p>

# Albion Command Desk

Passive Albion Online companion app with a Qt desktop UI:
- DPS/HPS meter (live or PCAP replay)
- Party-only combat aggregation (self + party)
- Optional scanner helper tab
- Market crafting workspace (inputs/outputs/results)

No game client hooks, no overlays, no memory editing.
Brand assets use a stylized `Ablion` wordmark (custom project branding).

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey">
  <img src="https://img.shields.io/badge/Game-Albion%20Online-orange">
</p>

## Support the Project
If Albion Command Desk saves you time or silver, consider supporting future updates and maintenance.

<p align="center">
  <a href="https://www.paypal.com/donate/?business=zlotyjacek%40gmail.com&currency_code=USD&amount=20.00"><img src="https://img.shields.io/badge/PayPal-Donate-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal (default $20, editable on PayPal page)"></a>
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

## Brand Assets
- Square logo (high-res): `assets/branding/albion-command-desk-logo-2048.png`
- Wide logo (README/media): `assets/branding/albion-command-desk-logo-wide-3200.png`
- Source art input: `assets/logo.png`
- Branding render script: `tools/branding/render_brand_from_logo.ps1`
- App icon assets: `albion_dps/qt/ui/command_desk_icon.png` and `albion_dps/qt/ui/command_desk_icon.ico`

Regenerate logo/icon from source art:
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\branding\render_brand_from_logo.ps1
```

## Install
### Support Matrix

| OS | Bootstrap script | Status |
|---|---|---|
| Windows | `tools/install/windows/install.ps1` | Supported |
| Linux | `tools/install/linux/install.sh` | Supported |
| macOS | `tools/install/macos/install.sh` | Supported |

Windows quick bootstrap (recommended):
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1
```

Linux quick bootstrap (recommended):
```bash
bash ./tools/install/linux/install.sh
```

macOS quick bootstrap (recommended):
```bash
bash ./tools/install/macos/install.sh
```

Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[capture]"
```

Linux/macOS:
```bash
python -m venv venv
source venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[capture]"
```

That single install command covers both:
- `replay` (PCAP files)
- `live` capture (with packet dependency set)

Windows `live` startup now verifies Npcap Runtime:
- if detected, app logs the install path and continues
- if missing, app shows the download link: `https://npcap.com/#download`

Testing tools:
```powershell
python -m pip install -e ".[all]"
```

Bootstrap installers run shared post-install smoke checks (CLI import + Qt startup probe).

Windows installer script docs:
- `tools/install/windows/README.md`
- `tools/install/linux/README.md`
- `tools/install/macos/README.md`

## Run
Live capture:
```powershell
albion-command-desk live
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
