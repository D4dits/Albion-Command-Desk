# Albion Command Desk v0.1.26

Use this as the GitHub Release body after final tag and artifact build.

## Highlights

- Meter party filtering is stricter and safer for solo, active-party, and nearby-player situations.
- Session gains now reports personal silver instead of party-wide silver.
- Loot keeps tracking party item pickups, but no longer accepts arbitrary nearby loot events before self/party context is known.
- Market price refresh is faster, more resilient to partial AO Data/cache coverage, and now fetches enchanted refined material aliases such as `*_LEVEL2@2`.
- Scanner sync rebuilds the local Albion Data Client binary after repo updates.
- Protocol decoding is more tolerant of current Protocol18 payload shapes.

## Meter

- Fixed access-rights packets being misread as party rosters.
- Fixed active-party join/current-party GUID mapping so members can appear after joining an already active group.
- Fixed solo captures where unrelated nearby players could appear in stats.
- Kept battle history generation active while other tabs are open; replay checks for `albion_combat_62_full_yz.pcap` produced 7 battle history entries.
- Session gains silver now uses local player loot/fame data, not the sum of party silver pickups.
- Compact history comparison panel no longer covers the session gains card.

## Loot

- Party loot is still collected for known party members.
- Unknown pre-bootstrap party-member loot events are ignored until self/party context exists, preventing nearby-player noise.
- Inventory move filtering was tightened.
- Missing/trash loot icon handling was hardened.

## Market

- Large craft-plan operations defer expensive preview rebuilds instead of recalculating after every added row.
- Live price refresh runs through a background worker queue and updates Qt state on the GUI thread.
- Cache/stale-cache rows are shown immediately when possible while live refresh runs.
- AO Data `429` handling now cools down quickly without blocking the UI in a long retry loop.
- Partial cached price subsets can satisfy current Market rows when the exact full request is not cached.
- Crafts with missing fresh component prices are not ranked as profitable candidates.
- Inputs use full upfront shopping quantities while selected cost/profit math uses net/economic material quantities after expected returns.
- Enchanted refined materials are fetched with all required AO Data aliases. Example: `T6_METALBAR_LEVEL2` and `T6_PLANKS_LEVEL2` also fetch `T6_METALBAR_LEVEL2@2` and `T6_PLANKS_LEVEL2@2`, fixing `price age n/a` for scanned Martlock materials.
- ADP/price-age wording was clarified.

## Scanner

- Scanner sync rebuilds the local scanner binary after repository updates, so a source update does not leave an old executable behind.

## Protocol / Runtime

- Protocol18 operation response decoding now accepts list-like dictionary keys without terminating the snapshot stream.
- Linux GUI smoke CI installs the Qt runtime libraries required by PySide6.

## QA

- Local validation used for this draft:
  - `python -m pytest tests --basetemp=artifacts/tmp/pytest_tmp_market_fix -q`
  - result: `407 passed, 3 skipped`
- GitHub Actions after latest push:
  - `pytest (ubuntu-latest, 3.12)`: passing
  - `pytest (windows-latest, 3.12)`: passing
  - `pytest-gui-qt`: passing

## Notes

- Live capture still requires Npcap Runtime on Windows.
- Market price freshness depends on AO Data receiving scanner traffic for the selected region/city/item.
- For best item names and map labels, keep local game-data extraction current.

## Download

- Windows: `AlbionCommandDesk-Setup-v0.1.26-x86_64.exe`
- Latest release page: `https://github.com/D4dits/Albion-Command-Desk/releases/latest`
