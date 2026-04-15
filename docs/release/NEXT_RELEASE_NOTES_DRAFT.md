# Next Release Notes Draft

Use this as the first draft for the next GitHub Release body. Before publishing, replace `vX.Y.Z` with the actual tag and ensure `CHANGELOG.md` has the same content under a dated version section.

## Albion Command Desk vX.Y.Z

### Highlights

- New native Loot tab for party item pickups.
- Loot parser updated for current Albion packet variants, including party-member pickup events.
- Loot import/export now preserves source classification with `source_kind`.
- Market now exposes crystallized craft variants with a dedicated badge.
- Crystallized Market inputs are treated as non-returnable one-time components, outside RRR.
- Loot and Market documentation, troubleshooting, QA notes, and website copy were refreshed.

### Loot

- Review item pickups in a compact feed.
- Filter by looter, source, search text, and item category.
- Distinguish player-corpse loot from mob/container/system loot with clear colors.
- Import older TXT logs for review, with best-effort source inference where `source_kind` is missing.
- Export newer logs with source classification preserved.

### Market

- Search/setup rows show crystallized variants clearly.
- Crystallized components are modeled as non-returnable requirements.
- Standard and crystallized craft paths remain comparable inside the same Market workflow.

### Notes

- Old TXT loot logs cannot recover party events that were not exported at capture time. Replay the original PCAP or record a new log with the current version.
- Live capture still requires Npcap Runtime on Windows.
- Local game-data extraction is recommended for best item names and map labels.

### Download

- Windows: `AlbionCommandDesk-Setup-vX.Y.Z-x86_64.exe`
- Latest release page: `https://github.com/D4dits/Albion-Command-Desk/releases/latest`
