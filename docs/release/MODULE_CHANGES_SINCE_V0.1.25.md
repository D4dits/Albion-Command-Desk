# Module Changes Since v0.1.25

This file summarizes the release-relevant changes after `v0.1.25`.
Use it as the review source before final tag and GitHub Release publication.

## Meter

Changed files and areas:
- `albion_dps/domain/party_registry.py`
- `albion_dps/pipeline.py`
- `albion_dps/meter/session_meter.py`
- `albion_dps/qt/runner.py`
- `albion_dps/qt/models.py`

Behavior changes:
- Access-rights payload subtype `210` is explicitly excluded from party-roster fallback parsing.
- Current-party GUID mapping is handled more reliably after joining an already active party.
- Party rows are constrained to confirmed self/party context and recent local observations where available.
- Solo captures stay self-scoped instead of admitting unrelated nearby players.
- Battle history continues to be produced independently of which tab is visible.
- Session gains silver is personal, not party-wide.
- History comparison UI is compact enough to avoid covering the session gains panel.

Validation:
- PCAP replay checks for `albion_combat_62_full_yz.pcap` confirmed 7 battle history entries.
- Party/meter regressions cover solo filtering, active-party joins, GUID mapping, and current history labels.

## Loot

Changed files and areas:
- `albion_dps/domain/loot_tracker.py`
- `albion_dps/qt/loot_state.py`
- loot import/export tests and PCAP expectations

Behavior changes:
- Known party members are still tracked in the Loot tab.
- Loot from arbitrary nearby players is ignored until self or party context is known.
- Silver can still be tracked by the domain layer when configured, but session gains no longer uses party-wide silver.
- Inventory move handling is stricter.
- Missing/trash loot icon cases are skipped instead of creating noisy item rows.

Validation:
- Loot unit tests and PCAP regressions were updated for the stricter party bootstrap behavior.
- Party member loot still appears when party context exists.

## Market

Changed files and areas:
- `albion_dps/qt/market/preview_state_ops.py`
- `albion_dps/qt/market/price_refresh_ops.py`
- `albion_dps/qt/market/common_ops.py`
- `albion_dps/qt/market/quote_ops.py`
- `albion_dps/market/service.py`
- `albion_dps/market/aod_client.py`
- `albion_dps/market/engine.py`

Behavior changes:
- Large craft-plan additions batch/defer preview rebuilds.
- Live price refresh runs in a background Python worker and returns through a GUI-polled queue.
- Cached and stale cached rows can populate the Market immediately while a live refresh is pending.
- Partial cache subsets can satisfy the current request when the exact full request is absent.
- AO Data `429` responses trigger cooldown instead of long GUI-blocking retry loops.
- Crafts missing fresh component prices are not ranked as valid profit candidates.
- Inputs preserve conservative upfront shopping quantities while cost/profit calculations use expected net returned material quantities.
- Enchanted refined materials now fetch AO Data alias variants, including `*_LEVELN@N`.

Concrete bug fixed:
- `Master's Great Frost Staff T6.2` in Martlock needs `T6_METALBAR_LEVEL2` and `T6_PLANKS_LEVEL2`.
- AO Data returns current prices under `T6_METALBAR_LEVEL2@2` and `T6_PLANKS_LEVEL2@2`.
- Market now requests both base and alias ids, so `price age` no longer shows `n/a` when those market rows were scanned.

Validation:
- Market tests cover Qt state, engine math, AO Data client, cache/service behavior, and enchanted refined material aliases.
- Live AO Data spot check for Martlock returned real prices and timestamps for `T6_METALBAR_LEVEL2@2` and `T6_PLANKS_LEVEL2@2`.

## Scanner

Changed files and areas:
- scanner sync workflow
- scanner sync tests

Behavior changes:
- After scanner repository sync/update, the local Albion Data Client binary is rebuilt when needed.
- This prevents a stale scanner executable from remaining after source changes.

## Protocol / Pipeline

Changed files and areas:
- `albion_dps/protocol/protocol16.py`
- `albion_dps/pipeline.py`

Behavior changes:
- Protocol18 operation-response parsing tolerates list-like dictionary keys.
- Snapshot streaming no longer terminates on that payload shape.
- Pending combat events/states are trimmed more safely when party context changes.

## QA / Release

Changed files and areas:
- `tests/`
- `docs/release/`
- `CHANGELOG.md`

Behavior changes:
- Golden and PCAP expectations were refreshed where parser behavior intentionally became more complete or stricter.
- Release notes now describe module changes since `v0.1.25`.

Known local test note:
- On this Windows workspace, the default pytest basetemp path can retain locked directories from interrupted runs.
- Use an alternate basetemp for full local validation:
  - `python -m pytest tests --basetemp=artifacts/tmp/pytest_tmp_release_docs -q`
