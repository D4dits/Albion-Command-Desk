# Market Module Backlog (AFM-like)

## Status update (2026-02-09)
- Sprint 1 (A+B): done in branch `market` (scaffold, AO Data client, cache SQLite, service, testy).
- Sprint 2: in progress.
  - Completed now: core kalkulacji dla Setup+Inputs (C1/C2/C4/C5/C6), walidacja Setup (D1/D2), generacja Inputs z manual override (E1/E3), testy.
  - Completed now: UI Market w `Main.qml` dla Setup + Inputs (formularz setup, tabela inputs, live total).
  - Completed now: preview Outputs + Results w `Main.qml` (tabela output + KPI net profit/margin/focus/SPF) podlaczone do `marketSetupState`.

## 1) Cel
Wdrozyc w projekcie nowy modul kalkulatora craftingu (AFM-like) z zakladkami:
- Setup
- Inputs
- Outputs
- Results
- Shopping List
- Selling List

Zakres obejmuje tylko ekonomie craftingu/refiningu, bez zmian w logice DPS metera.

## 2) Zakres MVP vs Full
### MVP (pierwsza dostawa)
- Setup
- Inputs
- Outputs
- Results
- Dane z AO Data API + reczne override cen
- Lokalny cache danych

### Full (druga dostawa)
- Shopping List
- Selling List
- Profile konfiguracji
- Export CSV/JSON
- Zaawansowane filtry i rankingi

## 3) Architektura docelowa
- `albion_dps/market/`:
  - `models.py` (dataclass/pydantic: recipe, price, config, result)
  - `catalog.py` (itemy, recipe, mapowania)
  - `aod_client.py` (klient HTTP do AO Data)
  - `cache.py` (SQLite + TTL)
  - `pricing.py` (wybor cen buy/sell/avg/manual)
  - `engine.py` (obliczenia koszt, output, profit, spf, tax)
  - `planner.py` (agregacje do shopping/selling list)
  - `service.py` (fasada dla UI)
- `albion_dps/qt/market/`:
  - `state.py` (stan i komendy QML)
  - modele list/tablic do QML
- `albion_dps/qt/ui/`:
  - nowy ekran/zakladka `Market` z 6 podzakladkami

## 4) Backlog techniczny (epiki i taski)
## EPIC A - Fundament i dane
- [x] A1. Utworzyc strukture katalogow `albion_dps/market/*`.
- [x] A2. Dodac modele domenowe:
  - `MarketRegion`, `City`, `PriceType`, `Quality`, `ItemRef`.
  - `CraftSetup`, `InputLine`, `OutputLine`, `CraftRun`.
  - `ProfitBreakdown`, `ShoppingEntry`, `SellingEntry`.
- [x] A3. Wczytywanie katalogu itemow/recipe:
  - parser lokalnego katalogu (JSON/yaml) z wersjonowaniem.
  - mapowanie item_id <-> unique_name <-> display_name.
- [ ] A4. Migracja/konwersja danych recipe z obecnych zasobow projektu.
- [ ] A5. Walidacja integralnosci datasetu (brakujace itemy, zle tier/enchant).

Definition of Done:
- testy jednostkowe modeli + walidacji przechodza.
- blad danych nie wywala aplikacji, tylko trafia do loga i UI warning.

## EPIC B - AO Data API + cache
- [x] B1. Klient HTTP AO Data:
  - endpointy `stats/prices` i `stats/charts`.
  - region host: `west/east/europe`.
- [ ] B2. Retry policy + timeout + backoff.
- [x] B3. Cache SQLite:
  - klucz: endpoint + parametry.
  - TTL osobno dla prices i charts.
  - fallback do stale cache przy bledach sieci.
- [x] B4. Normalizacja odpowiedzi API do modelu wewnetrznego.
- [ ] B5. Telemetria techniczna:
  - czas odpowiedzi, source (live/cache), liczba rekordow.

Definition of Done:
- testy integracyjne klienta z mockami API.
- mozna pracowac offline na cache (read-only mode).

## EPIC C - Silnik kalkulacji (core)
- [x] C1. Koszt materialow:
  - buy order / sell order / average / manual.
  - osobna lokalizacja zakupu per material.
- [x] C2. Koszt craftingu:
  - station fee, tax, premium, no-tax toggles.
- [~] C3. Return rate model:
  - city bonus, hideout, daily bonus, quality/zone.
- [x] C4. Focus:
  - focus required, focus saved, SPF (silver per focus).
- [x] C5. Output model:
  - ilosc outputow, net sell value po oplatach.
- [x] C6. Result model:
  - total cost, revenue, gross/net profit, margin %, fame proxy.
- [ ] C7. Batch mode:
  - wiele craftow na raz, wspolny wynik.

Definition of Done:
- zestaw testow porownawczych dla scenariuszy bazowych.
- deterministyczny wynik (ta sama konfiguracja = ten sam wynik).

## EPIC D - Setup tab
- [~] D1. Pola:
  - region, tier/enchant, quality, quantity/runs.
  - craft location, bonus city, hideout level/power.
  - premium, daily bonus, fee, tax.
  - tryb cen (buy/sell/avg/manual).
- [x] D2. Walidacje i wartosci domyslne.
- [ ] D3. Presety (np. city profile).
- [x] D4. Powiazanie Setup -> Inputs/Outputs recalculation.

Definition of Done:
- zmiana kazdego parametru triggeruje przeliczenie bez restartu.
- walidacje blokuja niepoprawne konfiguracje.

## EPIC E - Inputs tab
- [x] E1. Generacja listy materialow z recipe.
- [x] E2. Pobieranie cen i fallback:
  - live -> cache -> manual.
- [x] E3. Manual override per material.
- [ ] E4. Leftovers i stock (opcjonalnie MVP+).
- [x] E5. Widok tabelaryczny:
  - material, qty, city, price type, unit cost, line cost.

Definition of Done:
- suma line cost zgadza sie z total input cost w Results.

## EPIC F - Outputs tab
- F1. Lista output itemow (zalezne od run/return).
- F2. Cena sprzedazy:
  - buy/sell/avg/manual.
- F3. Sell location per output.
- F4. Net revenue po tax/fee.

Definition of Done:
- revenue z Outputs jest jedynym zrodlem revenue w Results.

## EPIC G - Results tab
- G1. Kafelki KPI:
  - investment, revenue, net profit, margin, focus, SPF.
- G2. Tabela per-item:
  - cost, revenue, profit, demand proxy.
- G3. Ranking i sortowanie.
- G4. Breakdown:
  - raw mats, artifacts, journals, fee, tax, focus impact.

Definition of Done:
- wszystkie KPI liczone z jednego modelu `ProfitBreakdown`.

## EPIC H - Shopping List tab
- H1. Agregacja materialow do zakupu.
- H2. Grupowanie po miescie i typie ceny.
- H3. Kolumny:
  - item, qty, city, unit, total, weight.
- H4. Copy/export CSV.

Definition of Done:
- shopping list jest spojna z Inputs (po agregacji batch).

## EPIC I - Selling List tab
- I1. Agregacja outputow do sprzedazy.
- I2. Grupowanie po miescie sprzedazy.
- I3. Kolumny:
  - item, qty, city, expected unit, expected total.
- I4. Copy/export CSV.

Definition of Done:
- selling list jest spojna z Outputs (po agregacji batch).

## EPIC J - UI/UX (Qt)
- [x] J1. Dodac glowna zakladke `Market` obok `Meter`/`Scanner`.
- J2. W `Market` dodac 6 podzakladek.
- J3. Wydajny model tabel:
  - sort/filter bez freezowania UI.
- J4. Stany:
  - loading, stale cache, API error, invalid config.
- J5. Czytelny log diagnostyczny market module.

Definition of Done:
- UI responsywne przy batch >= 100 pozycji.

## EPIC K - Testy i jakosc
- K1. Unit tests:
  - pricing, return rate, focus, tax, margin.
- K2. Integration tests:
  - klient AO Data + cache behavior.
- K3. Snapshot tests wynikow (znane konfiguracje).
- [x] K4. Smoke test QML dla nowej zakladki Market.
- K5. Testy regresji po zmianie datasetu recipe.

Definition of Done:
- zielony pipeline testow dla market modu.

## EPIC L - Dokumentacja i operacje
- L1. `README.md` sekcja Market.
- L2. `docs/MARKET_ARCHITECTURE.md` (przeplyw danych).
- L3. `docs/MARKET_TROUBLESHOOTING.md`.
- L4. instrukcja aktualizacji datasetu i cache cleanup.

Definition of Done:
- nowy uzytkownik uruchamia Market bez dodatkowych pytan.

## 5) Kolejnosc realizacji (rekomendowana)
1. A + B + C (backend core)
2. D + E + F + G (MVP UI)
3. K (testy MVP)
4. H + I (listy)
5. J polish + L dokumentacja

## 6) Szacowanie (orientacyjnie)
- Sprint 1 (1-2 tyg): A + B (minimum) + start C
- Sprint 2 (1-2 tyg): C + D + E
- Sprint 3 (1-2 tyg): F + G + testy MVP
- Sprint 4 (1 tydz): H + I + polish + docs

## 7) Ryzyka i decyzje techniczne
- Ryzyko 1: API limity/niestabilnosc -> wymagany cache + retry.
- Ryzyko 2: niespojnosc item IDs i recipe -> walidatory datasetu.
- Ryzyko 3: rozjazd wynikow vs arkusze -> trzymac "nasz model referencyjny", nie emulowac 1:1 DUMMYFUNCTION.
- Ryzyko 4: wydajnosc UI -> lazy loading i paginacja tabel.

## 8) Kryteria akceptacji calego modulu
- Uzytkownik moze ustawic craft scenariusz i dostaje stabilny wynik zysku.
- Uzytkownik moze wygenerowac shopping/selling list dla batch craftu.
- Wyniki sa odtwarzalne, testowalne i dzialaja offline na cache.
- Modul nie psuje obecnych funkcji DPS metera.
