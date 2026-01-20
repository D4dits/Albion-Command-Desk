# PROMPTS for Codex (CLI)

## Ogólna zasada
Zawsze pracuj w małych PR-ach: jedna funkcja -> test -> integracja.
Jeśli brakuje danych (np. brak PCAP), dodaj instrumentation i artefakty debug.

---

## Prompt 1 — scaffolding
"Utwórz strukturę projektu wg TASKS M0. Dodaj pyproject.toml z entrypointem `albion-dps`.
Dodaj minimalne modele danych: RawPacket, PhotonMessage, CombatEvent, MeterSnapshot (dataclasses).
Dodaj pytest i jeden test sanity."

## Prompt 2 — replay PCAP
"Zaimplementuj `replay_pcap.py`: wczytaj PCAP i emituj RawPacket (timestamp, src/dst, payload).
Dodaj test: dla przykładowego PCAP policz liczbę pakietów i sprawdź deterministyczność iteracji."

## Prompt 3 — unknown dump
"Dodaj mechanizm: jeśli parser nie rozpoznaje payloadu, zapisz go do artifacts/unknown/{ts}_{hash}.bin
oraz linię logu z metadanymi. Dodaj test: zasymuluj unknown payload."

## Prompt 4 — minimal photon framing
"Zaimplementuj minimalny decoder Photona (tylko tyle, by wyciągnąć event/opcode i payload).
Dodaj registry kodów i debug print w trybie --debug.
Dodaj testy na hex fixture (małe sample payloady)."

## Prompt 5 — meter aggregation
"Zaimplementuj agregację dmg/heal per source. Dodaj rolling DPS window.
Dodaj testy: seria CombatEvent -> oczekiwane sumy + dps."

## Prompt 6 — CLI table
"Zaimplementuj CLI render tabeli (odświeżanie co 1s) dla snapshotów z metera.
Dodaj flagi: --sort, --top, --snapshot."

---

## Wireshark playbook (M6)
- Capture filter: udp && (udp.port == 5055 || udp.port == 5056 || udp.port == 5058)
- Open PCAP, use "Follow UDP Stream" to isolate payloads.
- Identify Photon header (peerId, flags, commandCount, timestamp, challenge).
- For each new event/op code, save a hex sample and add a regression test.
- Update registry entries and parsers; unknown -> artifacts/unknown/{ts}_{hash}.bin.
