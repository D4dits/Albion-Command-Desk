# Troubleshooting

## `albion-dps` is not recognized
You need both:
1) an activated virtualenv
2) the project installed (so the console script exists)

Windows / PowerShell:
```
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -e ".[capture]"
albion-dps --help
```

Alternative (no install): run from the repo checkout
```
python -m albion_dps --help
python -m albion_dps live
```

## Live mode shows "no data"
Common causes:
- You are on the wrong interface: run `albion-dps live --list-interfaces` and pick the one that carries game traffic.
- No packets yet: start the game and generate traffic (zone change / combat).
- Capture dependencies missing: install `pcapy-ng` via `python -m pip install -e ".[capture]"`.
- Windows: Npcap not installed (or installed without WinPcap API compatibility).

## I see empty results while fighting
Strict "self + party only" filtering means the meter will not aggregate anything until it can resolve "self".
If you want deterministic startup, seed self:
```
albion-dps live --self-name "YourName"
```
or
```
albion-dps live --self-id 123456
```

## Party members missing (only 1-2 players show)
The meter needs at least one party roster update to learn party membership.
If you started capture after the party was already formed, the roster might never arrive.
Workarounds:
- Leave and re-join the party after starting the capture.
- Start capture before forming the party.
- For PCAPs, avoid port-only filters and capture all UDP so roster events are included.

## Cross-platform setup pitfalls (Windows/Linux/macOS)
Common issues when running on a different OS or machine:

- **.NET SDK version (extractor):** the item/map extractor targets .NET 10. Make sure `dotnet --info` shows SDK `10.x`.
- **`dotnet` on PATH:** if multiple SDKs exist (system vs user), ensure `DOTNET_ROOT` and `PATH` point to the SDK you want.
- **NuGet restore blocked:** extractor build needs access to `https://api.nuget.org`. If you're offline or blocked, restore/build will fail.
- **Permissions on build/artifacts:** if `tools/extract_items/obj` or `artifacts/` were created as root, `dotnet` may fail to write. Fix with:
  ```
  sudo chown -R "$USER:$USER" tools/extract_items/obj tools/extract_items/bin artifacts
  ```
- **Game root path differs:** on Linux installs (including custom paths), the actual data is often under `game_x64/Albion-Online_Data/...`. The extractor accepts either the base install folder or the specific `game_x64` folder.
- **Missing `items.json`:** if you see `Items catalog loaded but produced no entries`, re-run the extractor and confirm it generated `data/items.json`.

## Too many "unknown payload" files
Unknown payloads are saved to `artifacts/unknown/` to support protocol updates.
Log lines for unknown payloads are printed only in `--debug`, but files are still written.

## Weapon colors do not match equipped weapons
Per-weapon colors require local item databases:
- `data/indexedItems.json` (required)
- `data/items.json` (recommended)
If those files are missing, the UI falls back to role/heuristic colors.
Generate them with:
```
.\tools\extract_items\run_extract_items.ps1 -GameRoot "C:\Program Files\Albion Online"
```
Alternatively set `ALBION_DPS_GAME_ROOT` and launch the GUI to be prompted.
On Linux/macOS use:
```
./tools/extract_items/run_extract_items.sh --game-root "/path/to/Albion Online"
```
If you run the GUI from a terminal and no game root is set, it will prompt for a path.
Default Steam/Application install paths are auto-detected when possible.

## Zone label shows only numbers
If you see `2000`, the map index database is missing.
Generate it with the same extractor (creates `data/map_index.json`), or set `ALBION_DPS_MAP_INDEX`.

## Permission issues (Windows)
Npcap capture can require elevated permissions depending on configuration.
If capture fails, try running the terminal as Administrator and ensure Npcap is installed correctly.

## Pytest fails with PermissionError in TEMP (Windows)
If pytest crashes with errors like `PermissionError` under `C:\\Users\\...\\AppData\\Local\\Temp`,
set a writable temp dir before running tests:
```
$env:TEMP="$PWD\\artifacts\\tmp"
$env:TMP=$env:TEMP
python -m pytest -q -rs
```
If you still see errors, try running the terminal as Administrator.

## `python` points to Windows Store Python
If `python --version` fails or shows a Windows Store path (`WindowsApps`),
install Python from python.org and recreate the venv:
```
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

## Qt GUI fails to load (qtquick2plugin.dll missing)
This usually means Qt's DLLs are not found:
- Ensure the venv is active and PySide6 is installed: `python -m pip install -e ".[gui-qt]"`
- Restart the terminal after install so PATH updates are picked up.
- If it still fails, install the Microsoft VC++ Redistributable (x64).
