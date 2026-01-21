# GUI plan (branch: gui)

Goal: nowoczesne, pasywne UI pokazujące DPS/HPS w czasie rzeczywistym, działające na Windows/Linux/macOS bez hooków/overlay na kliencie gry.

## Wybrany stack
- **Textual (Python TUI)**: czysty Python, brak natywnych binariów, działa w terminalu na wszystkich OS, pozwala na nowoczesny wygląd (kolory, animacje, panele, bary), dobrze współgra z istniejącym CLI i pipeline’em.
- Dlaczego nie Electron/Qt/GTK: cięższe zależności, trudniejsze wsparcie 3-OS, brak potrzeby wbudowanego renderera HTML; terminalowa TUI spełnia wymagania i minimalizuje ryzyko instalacyjne.
- Dodatkowe biblioteki: `rich` (już dependency Textual) — zapewnia progress bary i kolory.

## Założenia UI
- Ekran główny: nagłówek (tryb, strefa, czas, fame/h), tabela z DPS/HPS, **poziome bary** skalowane wg sortu (dmg/dps/heal/hps), kolorowanie per rola (tank/dps/heal; fallback: cykliczna paleta).
- Panel historii: lista ostatnich walk (battle/zone/manual), możliwość wyboru do podglądu.
- Auto-odświeżanie z aktualnych snapshotów metera (1s lub zgodnie z `snapshot_interval`).
- Sterowanie klawiaturą (Textual: komendy / klawisze), bez interferencji z grą.

## Integracja z istniejącym pipeline
- Wykorzystać `live_snapshots`/`replay_snapshots` (albion_dps/pipeline.py) jako źródło.
- Adapter async: wątkiem/korutyną pchać `MeterSnapshot` do asyncio.Queue, Textual konsumuje kolejkę i aktualizuje stan widoku.
- Brak zmian w parserze/capture; GUI jest czysto wyświetlające.

## Plan implementacji (zadania)
1) Dodać opcjonalną zależność `textual` w `pyproject.toml` (np. extra `gui`) i prostą komendę CLI `albion-dps gui` (lub flagę `--ui textual` dla live/replay).
2) Utworzyć moduł `albion_dps/gui/textual_app.py`:
   - model stanu: ostatni `MeterSnapshot`, historia (reuse z SessionMeter).
   - layout: Header + Scoreboard (tabela + bary) + History panel.
   - kolory: paleta ról (tank/dps/heal) + fallback sekwencyjna.
3) Dodać adapter kolejki: funkcja `run_textual_ui(snapshots: Iterable[MeterSnapshot], names: NameRegistry)` uruchamia app i przekazuje snapshoty.
4) Spiąć z CLI: nowe subpolecenie `gui live` / `gui replay` lub flaga `--ui textual` dla istniejących trybów (do decyzji przy implementacji).
5) Testy:
   - smoke test: uruchomienie Textual app z kilkoma sztucznymi snapshotami (bez realnego terminala, np. `App.run(headless=True)` jeśli wspierane).
   - regresje na PCAP replay: sprawdzić, że `gui replay <pcap>` nie rzuca wyjątków i render loop kończy się.
6) Dokumentacja: README sekcja GUI (instalacja extra `gui`, uruchomienie komendy).

## Proponowane prompty do kolejnych kroków
1) „Dodaj dependency Textual (extra gui), wprowadź subkomendę `gui` w CLI (live/replay) bez implementacji widoku (stub).”
2) „Zaimplementuj adapter kolejki i Textual app, która pokazuje nagłówek + tabelę z DPS/HPS + bary.”
3) „Dodaj kolorowanie per rola (tank/dps/heal) i fallback paletę, plus panel historii.”
4) „Napraw testy/CI i dodaj smoke test dla GUI (headless).”
5) „Uzupełnij README o sekcję GUI (instalacja, uruchomienie, klawisze).”

## Notatki kompatybilności
- Textual wymaga terminala z TrueColor dla pełnej palety, ale działa degradacyjnie na gorszych terminalach.
- Na Windows należy używać nowego Windows Terminal lub PowerShell Core dla najlepszego renderingu.
- GUI pozostaje pasywne: nie hookuje gry, nie pokazuje overlay na ekranie gry; to osobne okno/terminal.

