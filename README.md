<p align="center">
  <img src="assets/Logo.png" alt="Albion Command Desk" width="620">
</p>

# Albion Command Desk

Albion Command Desk is a passive Albion Online desktop companion app built with PySide6/QML.

Current workspace:
- DPS/HPS meter for live capture and PCAP replay.
- Party-scoped combat filtering and fight history.
- Loot logger for party item pickups, corpse/container source context, log import/export, and item/category filters.
- Scanner helper tab for Albion Data Client workflow and diagnostics.
- Market craft planner with setup, inputs, outputs, results, AO Data prices, CSV export, and crystallized recipe variants.
- Settings and Help tabs for runtime status, game-data paths, update checks, and diagnostics bundle export.

No client hooks, no overlays, no memory editing, no gameplay automation.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey">
  <img src="https://img.shields.io/badge/Game-Albion%20Online-orange">
</p>

## Support the Project

<p align="center">
  <a href="https://www.paypal.com/donate/?business=albiosuperacc%40linuxmail.org&currency_code=USD&amount=20.00"><img src="https://img.shields.io/badge/PayPal-Donate-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
  <a href="https://buycoffee.to/ao-dps/"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?style=for-the-badge" alt="Buy Me a Coffee"></a>
</p>

## Key Features

### Meter
- Live and replay combat scoreboard.
- Battle, zone, and manual session modes.
- Party/self filtering to avoid attributing nearby unrelated players.
- DPS, HPS, damage, heal, session history, fame/silver session gains, and map activity trail.
- Replay regression coverage for current PCAP fixtures.

### Loot
- Native loot observer integrated into the same Photon pipeline as the meter.
- Tracks party item pickups from player corpses, mobs, loot chests, and system/container flows.
- Separates source types with UI colors:
  - red: looted from player corpse,
  - yellow: mob/container/system source,
  - neutral: unknown source.
- Silver pickup tracking is intentionally disabled in the live UI; the tab focuses on item loot.
- Import/export uses a stable text format with `source_kind`, so imported logs preserve whether an item came from a player corpse, mob, container, or system flow.
- Filters cover looter, source type, item search, and item categories such as weapons, armor, bags, capes, mounts, consumables, resources, artifacts, and other.

### Market
- Recipe setup, city/region settings, premium/tax/fee assumptions, daily bonus, run count, and focus-aware profit calculations.
- Inputs, outputs, and result rows stay aligned with top-level investment/revenue/profit math.
- AO Data price refresh with SQLite cache, stale-cache fallback, diagnostics, and manual overrides.
- Shopping/selling/results CSV copy/export.
- Crystallized recipe variants are available in craft search and setup and are marked with a dedicated badge. Their crystallized components are treated as non-returnable one-time inputs, not RRR materials.

### Operations
- Start dashboard exposes capture runtime, Git, game data, and update readiness.
- Settings centralizes app paths, log retention, scanner/game-data setup, runtime checks, and update preferences.
- Help exposes version, links, dependency guidance, troubleshooting, and diagnostics export.

## Install

### Windows (recommended, no Git required)

Requires Python 3.10+ installed first. Git is not required for the release installer path.

1. Open latest release: `https://github.com/D4dits/Albion-Command-Desk/releases/latest`
2. Download `AlbionCommandDesk-Setup-vX.Y.Z-x86_64.exe`
3. Run installer

Installer creates:
- runtime: `%LOCALAPPDATA%\AlbionCommandDesk\runtime\vX.Y.Z`
- venv: `%LOCALAPPDATA%\AlbionCommandDesk\venv`
- shortcuts: Desktop + Start Menu

### Source install (Windows/Linux/macOS)

Windows:
```powershell
git clone https://github.com/D4dits/Albion-Command-Desk.git
cd Albion-Command-Desk
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1
```

Linux:
```bash
git clone https://github.com/D4dits/Albion-Command-Desk.git
cd Albion-Command-Desk
bash ./tools/install/linux/install.sh
```

macOS:
```bash
git clone https://github.com/D4dits/Albion-Command-Desk.git
cd Albion-Command-Desk
bash ./tools/install/macos/install.sh
```

## Run

Windows:
```powershell
.\venv\Scripts\albion-command-desk core
# live capture:
# .\venv\Scripts\albion-command-desk live
```

Linux/macOS:
```bash
./venv/bin/albion-command-desk core
# live capture:
# ./venv/bin/albion-command-desk live
```

Release-EXE install path (Windows):
```powershell
& "$env:LOCALAPPDATA\AlbionCommandDesk\venv\Scripts\albion-command-desk.exe" core
```

Replay mode:
```powershell
albion-command-desk replay .\path\to\capture.pcap
```

## Requirements

- Python 3.10+ (3.11/3.12 recommended for release builds).
- For `live` mode:
  - Windows: Npcap Runtime (`https://npcap.com/#download`).
  - Linux/macOS: libpcap/system capture libs.
- Git is required only for scanner repo sync/update actions.
- Local game-data extraction is recommended for best item/map labels.

Npcap SDK is not required for normal end users.

## Optional: Game Data Extraction

For better item/map coverage:

Windows:
```powershell
.\tools\extract_items\run_extract_items.ps1 -GameRoot "C:\Program Files\Albion Online"
```

Linux/macOS:
```bash
./tools/extract_items/run_extract_items.sh --game-root "/path/to/Albion Online"
```

## Screenshots

<p align="center">
  <img src="assets/ux-baseline/ph2-meter.png" alt="Meter tab" width="920">
</p>
<p align="center">
  <img src="assets/ux-baseline/ph2-market.png" alt="Market tab" width="920">
</p>

The GitHub Pages site contains the current public feature summary and screenshot gallery:
`https://d4dits.github.io/Albion-Command-Desk/`

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/TROUBLESHOOTING.md`
- `docs/LOOT_LOGGER_PLAN.md`
- `docs/MARKET_ARCHITECTURE.md`
- `docs/MARKET_TROUBLESHOOTING.md`
- `docs/MARKET_DATASET_UPDATE.md`
- `docs/qa/QA_REGRESSION_PASS.md`
- `docs/release/RELEASE_CHECKLIST.md`
- `docs/release/RELEASE_RUNBOOK.md`
- `CHANGELOG.md`

## Tests

Default:
```powershell
python -m pytest -q
```

Targeted checks before a release:
```powershell
python -m pytest -q tests/test_loot_tracker.py tests/test_loot_tracker_pcaps.py tests/test_qt_loot_state.py tests/test_market_catalog.py tests/test_market_qt_state.py
python .\tools\qa\run_release_readiness.py
```
