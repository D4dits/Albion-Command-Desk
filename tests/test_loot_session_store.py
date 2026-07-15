from __future__ import annotations

from albion_dps.domain.loot_session_store import LootSessionStore
from albion_dps.domain.loot_types import LootEvent, LootItemRef, LootPlayer


def _event(
    event_id: str,
    *,
    timestamp: float = 950.0,
    quantity: int = 3,
    reason: str = "party",
) -> LootEvent:
    return LootEvent(
        timestamp=timestamp,
        looted_by=LootPlayer("Alice", "Guild A", "Alliance A"),
        looted_from=LootPlayer("Enemy"),
        source_name="Enemy",
        source_kind="player",
        item=LootItemRef(123, "T6_MAIN_SWORD@1", "Master's Broadsword", quality=None),
        quantity=quantity,
        is_silver=False,
        raw_event_code=1,
        raw_subtype=277,
        event_id=event_id,
        eligibility_reason=reason,
    )


def test_session_store_assigns_lookback_and_persists_rows(tmp_path) -> None:
    path = tmp_path / "loot.sqlite3"
    store = LootSessionStore(path)
    store.sync_observations([_event("one")])

    session = store.start_session(started_at=1000.0, lookback_seconds=120.0)
    rows = store.loot_rows(session_id=session.session_id)

    assert len(rows) == 1
    assert rows[0]["event_id"] == "one"
    assert rows[0]["outstanding_quantity"] == 3
    store.stop_session(ended_at=1100.0)
    store.close()

    reopened = LootSessionStore(path)
    assert reopened.list_sessions()[0].status == "closed"
    assert reopened.loot_rows(session_id=session.session_id)[0]["event_id"] == "one"
    reopened.close()


def test_session_store_supports_partial_settlement_and_reset(tmp_path) -> None:
    store = LootSessionStore(tmp_path / "loot.sqlite3")
    store.sync_observations([_event("one", quantity=5)])
    session = store.start_session(started_at=1000.0, lookback_seconds=120.0)

    assert store.add_settlement("one", action="returned", quantity=2)
    assert store.add_settlement("one", action="sold", quantity=1, actual_value=50_000)
    row = store.loot_rows(session_id=session.session_id)[0]
    assert row["settlement_status"] == "partial"
    assert row["outstanding_quantity"] == 2

    assert store.reset_settlements("one")
    reset = store.loot_rows(session_id=session.session_id)[0]
    assert reset["settlement_status"] == "pending"
    assert reset["outstanding_quantity"] == 5
    store.close()


def test_session_store_keeps_unknown_affiliation_outside_session_until_promoted(tmp_path) -> None:
    store = LootSessionStore(tmp_path / "loot.sqlite3")
    store.sync_observations([_event("one", reason="unknown")])
    session = store.start_session(started_at=1000.0, lookback_seconds=120.0)
    assert store.loot_rows(session_id=session.session_id) == []
    assert store.pending_scope_count() == 1

    store.sync_observations([_event("one", reason="guild")])
    rows = store.loot_rows(session_id=session.session_id)
    assert len(rows) == 1
    assert rows[0]["eligibility_reason"] == "guild"
    store.close()


def test_session_store_persists_market_and_liquidation_values(tmp_path) -> None:
    store = LootSessionStore(tmp_path / "loot.sqlite3")
    store.sync_observations([_event("one", quantity=2)])
    session = store.start_session(started_at=1000.0, lookback_seconds=120.0)
    store.upsert_valuation(
        "one",
        region="europe",
        city="Bridgewatch",
        pricing_quality=1,
        market_unit=100_000,
        liquidation_unit=80_000,
        source="local_db+aodata",
        estimated=True,
    )

    row = store.loot_rows(session_id=session.session_id)[0]
    assert row["market_unit"] == 100_000
    assert row["liquidation_unit"] == 80_000
    assert row["estimated"] == 1
    store.close()


def test_session_store_can_settle_all_outstanding_loot_for_player(tmp_path) -> None:
    store = LootSessionStore(tmp_path / "loot.sqlite3")
    store.sync_observations([_event("one"), _event("two", timestamp=960.0, quantity=2)])
    session = store.start_session(started_at=1000.0, lookback_seconds=120.0)

    assert store.settle_player(session.session_id, "Alice", action="returned") == 2
    rows = store.loot_rows(session_id=session.session_id)
    assert {row["settlement_status"] for row in rows} == {"returned"}
    assert {row["outstanding_quantity"] for row in rows} == {0}
    store.close()


def test_session_store_imports_legacy_events_as_closed_editable_session(tmp_path) -> None:
    store = LootSessionStore(tmp_path / "loot.sqlite3")
    session = store.import_session("Old run", [_event("", timestamp=100.0)])

    assert session.status == "closed"
    rows = store.loot_rows(session_id=session.session_id)
    assert len(rows) == 1
    assert rows[0]["event_id"].startswith("import:")
    assert store.add_settlement(rows[0]["event_id"], action="returned")
    store.close()
