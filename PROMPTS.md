# PROMPTS for Codex (CLI)

## Ogolna zasada
Zawsze pracuj w malych PR-ach: jedna funkcja -> test -> integracja.
Jesli brakuje danych (np. brak PCAP), dodaj instrumentation i artefakty debug.

---

## Prompt 1 - scaffolding
"Utworz strukture projektu wg TASKS M0. Dodaj pyproject.toml z entrypointem `albion-dps`.
Dodaj minimalne modele danych: RawPacket, PhotonMessage, CombatEvent, MeterSnapshot (dataclasses).
Dodaj pytest i jeden test sanity."

## Prompt 2 - replay PCAP
"Zaimplementuj `replay_pcap.py`: wczytaj PCAP i emituj RawPacket (timestamp, src/dst, payload).
Dodaj test: dla przykladowego PCAP policz liczbe pakietow i sprawdz deterministycznosc iteracji."

## Prompt 3 - unknown dump
"Dodaj mechanizm: jesli parser nie rozpoznaje payloadu, zapisz go do artifacts/unknown/{ts}_{hash}.bin
oraz linie logu z metadanymi. Dodaj test: zasymuluj unknown payload."

## Prompt 4 - minimal photon framing
"Zaimplementuj minimalny decoder Photona (tylko tyle, by wyciagnac event/opcode i payload).
Dodaj registry kodow i debug print w trybie --debug.
Dodaj testy na hex fixture (male sample payloady)."

## Prompt 5 - meter aggregation
"Zaimplementuj agregacje dmg/heal per source. Dodaj rolling DPS window.
Dodaj testy: seria CombatEvent -> oczekiwane sumy + dps."

## Prompt 6 - CLI table
"Zaimplementuj CLI render tabeli (odswiezanie co 1s) dla snapshotow z metera.
Dodaj flagi: --sort, --top, --snapshot."

---

## Wireshark playbook (M6)
- Capture filter: udp && (udp.port == 5055 || udp.port == 5056 || udp.port == 5058)
- Open PCAP, use "Follow UDP Stream" to isolate payloads.
- Identify Photon header (peerId, flags, commandCount, timestamp, challenge).
- For each new event/op code, save a hex sample and add a regression test.
- Update registry entries and parsers; unknown -> artifacts/unknown/{ts}_{hash}.bin.

---

## Item DB generation (colors)
If per-weapon colors are needed, generate local item databases:
```
.\tools\extract_items\run_extract_items.ps1 -GameRoot "C:\Program Files\Albion Online"
```
Outputs: `data/indexedItems.json` and `data/items.json` (local-only).

Map names:
```
./tools/extract_items/run_extract_items.sh --game-root "/path/to/Albion Online"
```
Outputs `data/map_index.json` (local-only).
