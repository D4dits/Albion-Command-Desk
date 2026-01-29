# TASKS - Albion DPS Meter

## Milestone M0 - Skeleton
- [x] pyproject + entrypoint `albion-dps`
- [x] moduly i puste kontrakty typow
- [x] logger + konfiguracja

## Milestone M1 - Capture (live + replay)
- [x] replay PCAP: iteracja pakietow + timestamp
- [x] live capture: BPF UDP + konfiguracja interfejsu
- [x] zapis surowych payloadow (debug)

## Milestone M2 - Photon decode (minimum)
- [x] parser ramki -> message (event/op)
- [x] registry kodow + tryb unknown dump
- [x] test: dekodowanie przykladowych payloadow

## Milestone M3 - Combat events
- [x] mapowanie na CombatEvent: damage/heal
- [x] podstawowe pola: source, target, amount, time

## Milestone M4 - Meter
- [x] agregacja per player
- [x] rolling DPS window
- [x] combat session reset

## Milestone M5 - CLI UI
- [x] tabela odswiezana w terminalu
- [x] sort/top/snapshot
- [x] tryb `--debug` (unknown)

## Milestone M6 - Wireshark playbook + test goldens
- [x] workflow dokumentacja
- [x] 2-3 PCAP + expected outputs

## Milestone M7 - Party filtering
- [x] registry list party (event 252) + map do nazw
- [x] filtracja metera tylko do gracza + party
- [x] auto-detekcja self z eventow party (subtype 228/238)

## Milestone M8 - TUI history + modes + fame
- [x] session history (battle/zone/manual)
- [x] copy history entry to clipboard (1-9)
- [x] zone sessions keyed by server endpoint
- [x] fame total + fame per hour + reset

## Milestone M9 - GUI (Textual TUI)
- [x] GUI subcommand `albion-dps gui` (live/replay)
- [x] Textual app with table, bars, and history panel
- [x] role coloring + fallback palette
- [x] headless smoke test

## Milestone M10 - Item DBs + weapon colors
- [x] per-weapon color palette
- [x] item resolver reads indexedItems/items
- [x] local extractor tool to generate JSON from game files
