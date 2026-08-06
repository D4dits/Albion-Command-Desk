from __future__ import annotations

import os
import queue
import threading
import time
from datetime import datetime, timezone

from PySide6.QtCore import QCoreApplication


def refresh_prices(state) -> None:
    if not state.canRefreshPrices:
        state._set_list_action_text(f"Refresh available in {state.refreshCooldownSeconds}s.")
        return
    state._append_diag("Manual price refresh requested.", level="INFO")
    state._set_next_live_fetch_cooldown(state._manual_refresh_cooldown_seconds)
    if not state._should_defer_price_refresh():
        state._rebuild_preview(force_price_refresh=True)
        return
    state._prices_source = "loading"
    state._prices_status_text = "Queued live refresh..."
    state.pricesChanged.emit()
    state._schedule_deferred_price_refresh(0.01, force=True)


def current_price_index(
    state,
    setup,
    *,
    force_refresh: bool,
    allow_live: bool,
):
    if force_refresh:
        return state._refresh_price_index(setup, force=True)
    context_key = state._price_key(setup)
    if (
        state._price_index
        and context_key == state._price_context_key
        and str(getattr(state, "_prices_source", "")) == "live"
    ):
        return state._price_index
    if not allow_live:
        if state._service is not None:
            try:
                item_ids = state._collect_pricing_item_ids()
                locations = state._collect_locations(setup)
                if item_ids and locations:
                    local_index = state._service.get_price_index(
                        region=setup.region,
                        item_ids=item_ids,
                        locations=locations,
                        qualities=list(state._price_qualities(setup)),
                        ttl_seconds=120.0,
                        allow_stale=True,
                        allow_cache=True,
                        allow_live=False,
                    )
                    if local_index:
                        state._price_index = local_index
                        state._price_context_key = state._price_key(setup)
                        meta = state._service.last_prices_meta
                        state._prices_source = meta.source
                        state._prices_status_text = f"{meta.source}: {meta.record_count} cached rows"
                        state.pricesChanged.emit()
                        return state._price_index
            except Exception as exc:
                state._log.debug("Local/cache price lookup failed, using fallback prices: %s", exc)
        fallback_index = state._build_fallback_price_index(setup)
        if state._price_index:
            fallback_index.update(state._price_index)
        state._price_index = fallback_index
        return state._price_index
    if state._price_index and context_key == state._price_context_key:
        if str(getattr(state, "_prices_source", "")) == "live":
            return state._price_index
        state._price_context_key = None
    return state._refresh_price_index(setup, force=False)


def refresh_price_index(
    state,
    setup,
    *,
    force: bool,
):
    item_ids = state._collect_pricing_item_ids()
    locations = state._collect_locations(setup)
    context_key = state._price_key(setup)
    if not force and state._price_index and context_key == state._price_context_key:
        return state._price_index
    if not item_ids:
        state._set_fallback_status("No recipe items selected. Prices unavailable.")
        state._price_index = {}
        state._price_context_key = context_key
        return state._price_index

    if state._service is None:
        state._set_fallback_status("AO Data client not configured. Using bundled fallback prices.")
        state._price_index = state._build_fallback_price_index(setup)
        state._price_context_key = context_key
        state._append_diag("AO Data client unavailable, switched to fallback prices.", level="WARN")
        return state._price_index

    now = time.monotonic()
    if not force:
        if state._price_fetch_in_progress:
            state._schedule_deferred_price_refresh(0.35)
            if state._price_index:
                return state._price_index
            state._price_index = state._build_fallback_price_index(setup)
            state._price_context_key = context_key
            return state._price_index
        if now < state._next_live_fetch_not_before:
            remaining = max(0.1, state._next_live_fetch_not_before - now)
            state._schedule_deferred_price_refresh(remaining + 0.05)
            state._set_prices_status(
                "cooldown",
                f"AO Data cooldown active ({remaining:.0f}s). Using cache/fallback prices.",
            )
            fallback_index = state._build_fallback_price_index(setup)
            if state._price_index:
                fallback_index.update(state._price_index)
            state._price_index = fallback_index
            state._price_context_key = context_key
            return state._price_index

    if _can_use_async_price_fetch(state):
        return _start_async_price_fetch(
            state,
            setup,
            item_ids=item_ids,
            locations=locations,
            context_key=context_key,
            force=force,
        )

    state._price_fetch_in_progress = True
    batch_count = _live_batch_count(state, setup, item_ids, locations)
    state._prices_source = "loading"
    state._prices_status_text = (
        f"Fetching live prices ({len(item_ids)} IDs"
        + (f", ~{batch_count} batch(es)" if batch_count > 0 else "")
        + f", {len(locations)} location(s))..."
    )
    state.pricesChanged.emit()
    state._process_ui_events()
    try:
        state._append_diag(
            f"AO Data fetch request: {len(item_ids)} item IDs across {len(locations)} locations.",
            level="INFO",
        )
        if len(item_ids) >= 200:
            state._append_diag(
                "Large refresh in progress. This can take up to ~60s depending on AO Data rate limits.",
                level="INFO",
            )
        state._process_ui_events()
        index = state._service.get_price_index(
            region=setup.region,
            item_ids=item_ids,
            locations=locations,
            qualities=list(state._price_qualities(setup)),
            ttl_seconds=120.0,
            allow_stale=not force,
            allow_cache=not force,
            allow_live=True,
        )
        if index:
            meta = state._service.last_prices_meta
            state._price_index = index
            state._price_context_key = context_key
            if not force and meta.source == "live":
                state._set_next_live_fetch_cooldown(state._min_live_refresh_interval_seconds)
            state._prices_source = meta.source
            state._prices_status_text = f"{meta.source}: {meta.record_count} rows in {meta.elapsed_ms:.0f} ms"
            state.pricesChanged.emit()
            state._append_diag(
                f"Prices loaded from {meta.source} ({meta.record_count} rows, {meta.elapsed_ms:.0f} ms).",
                level="INFO",
            )
            if (
                meta.source in {"stale_cache", "partial_stale_cache"}
                and not force
                and QCoreApplication.instance() is not None
                and state.refreshCooldownSeconds <= 0
                and not state._deferred_price_refresh_timer.isActive()
                and not state._deferred_force_price_refresh
            ):
                state._append_diag(
                    "Stale cache shown first; scheduling background live refresh.",
                    level="INFO",
                )
                state._set_prices_status(
                    "refreshing_cache",
                    f"Showing stale cache ({meta.record_count} rows); background live refresh queued.",
                )
                state._schedule_deferred_price_refresh(0.15, force=True)
            return state._price_index
        state._set_fallback_status("AO Data returned no price rows. Using bundled fallback prices.")
        state._append_diag("AO Data returned no rows; using fallback prices.", level="WARN")
    except Exception as exc:
        state._log.warning("AO Data fetch failed, using fallback prices: %s", exc)
        error_text = str(exc)
        if "429" in error_text or "Too Many Requests" in error_text:
            cooldown = max(
                state._rate_limit_cooldown_seconds,
                state._min_live_refresh_interval_seconds,
            )
            state._set_next_live_fetch_cooldown(cooldown)
            state._set_prices_status(
                "cooldown",
                f"AO Data rate limit (429). Cooling down for {cooldown:.0f}s; using fallback prices.",
            )
        else:
            state._set_fallback_status(f"AO Data fetch failed ({exc}). Using bundled fallback prices.")
        state._append_diag(f"AO Data fetch failed: {exc}", level="ERROR")
    finally:
        state._price_fetch_in_progress = False
        state.pricesChanged.emit()

    state._price_index = state._build_fallback_price_index(setup)
    state._price_context_key = context_key
    return state._price_index


def _can_use_async_price_fetch(state) -> bool:
    if QCoreApplication.instance() is None:
        return False
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    if state._service is None:
        return False
    if state._price_fetch_in_progress:
        return False
    return True


def _start_async_price_fetch(
    state,
    setup,
    *,
    item_ids: list[str],
    locations: list[str],
    context_key,
    force: bool,
):
    state._price_fetch_in_progress = True
    state._pending_price_context_key = context_key
    state._pending_price_force = bool(force)
    batch_count = _live_batch_count(state, setup, item_ids, locations)
    state._prices_source = "loading"
    state._prices_status_text = (
        f"Fetching live prices ({len(item_ids)} IDs"
        + (f", ~{batch_count} batch(es)" if batch_count > 0 else "")
        + f", {len(locations)} location(s))..."
    )
    state.pricesChanged.emit()
    state._append_diag(
        f"AO Data async fetch started: {len(item_ids)} item IDs across {len(locations)} locations.",
        level="INFO",
    )
    if len(item_ids) >= 200:
        state._append_diag(
            "Large refresh is running in the background; the Market tab remains interactive.",
            level="INFO",
        )

    cached_index = _cache_only_price_index(
        state,
        setup,
        item_ids=item_ids,
        locations=locations,
    )

    result_queue: queue.Queue[tuple[object, object, str]] = queue.Queue(maxsize=1)
    thread = threading.Thread(
        target=_run_price_fetch_worker,
        kwargs={
            "service": state._service,
            "region": setup.region,
            "item_ids": list(item_ids),
            "locations": list(locations),
            "qualities": list(state._price_qualities(setup)),
            "force": bool(force),
            "result_queue": result_queue,
        },
        name="AODataPriceFetch",
        daemon=True,
    )
    state._price_fetch_result_queue = result_queue
    state._price_fetch_thread = thread
    thread.start()
    state._price_fetch_result_timer.start()

    if cached_index:
        state._price_index = cached_index
        state._price_context_key = context_key
        meta = state._service.last_prices_meta
        state._prices_source = meta.source
        state._prices_status_text = (
            f"{meta.source}: {meta.record_count} cached rows; live refresh running..."
        )
        state.pricesChanged.emit()
        return state._price_index

    if state._price_index:
        return state._price_index
    state._price_index = state._build_fallback_price_index(setup)
    state._price_context_key = context_key
    return state._price_index


def _run_price_fetch_worker(
    *,
    service,
    region,
    item_ids: list[str],
    locations: list[str],
    qualities: list[int],
    force: bool,
    result_queue: "queue.Queue[tuple[object, object, str]]",
) -> None:
    try:
        index = service.get_price_index(
            region=region,
            item_ids=item_ids,
            locations=locations,
            qualities=qualities,
            ttl_seconds=120.0,
            allow_stale=not force,
            allow_cache=not force,
            allow_live=True,
        )
        result_queue.put((index, service.last_prices_meta, ""))
    except Exception as exc:
        result_queue.put(({}, None, str(exc)))


def _cache_only_price_index(
    state,
    setup,
    *,
    item_ids: list[str],
    locations: list[str],
):
    try:
        return state._service.get_price_index(
            region=setup.region,
            item_ids=item_ids,
            locations=locations,
            qualities=list(state._price_qualities(setup)),
            ttl_seconds=120.0,
            allow_stale=True,
            allow_cache=True,
            allow_live=False,
        )
    except Exception as exc:
        state._log.debug("AO Data cache-only lookup failed: %s", exc)
        return {}


def poll_async_price_fetch(state) -> None:
    result_queue = getattr(state, "_price_fetch_result_queue", None)
    if result_queue is None:
        state._price_fetch_result_timer.stop()
        return
    try:
        index, meta, error = result_queue.get_nowait()
    except queue.Empty:
        thread = getattr(state, "_price_fetch_thread", None)
        if thread is not None and not thread.is_alive():
            state._price_fetch_result_timer.stop()
            state._price_fetch_result_queue = None
            on_async_price_fetch_finished(state, {}, None, "AO Data price worker stopped without a result.")
        return

    state._price_fetch_result_timer.stop()
    thread = getattr(state, "_price_fetch_thread", None)
    if thread is not None:
        thread.join(timeout=0)
    state._price_fetch_result_queue = None
    on_async_price_fetch_finished(state, index, meta, error)


def on_async_price_fetch_finished(state, index: object, meta: object, error: str) -> None:
    state._price_fetch_in_progress = False
    state._price_fetch_thread = None
    context_key = state._pending_price_context_key
    force = bool(state._pending_price_force)
    state._pending_price_context_key = None
    state._pending_price_force = False

    error_text = str(error or "").strip()
    if error_text:
        state._log.warning("AO Data async fetch failed, using fallback prices: %s", error_text)
        if "429" in error_text or "Too Many Requests" in error_text:
            cooldown = max(
                state._rate_limit_cooldown_seconds,
                state._min_live_refresh_interval_seconds,
            )
            state._set_next_live_fetch_cooldown(cooldown)
            state._set_prices_status(
                "cooldown",
                f"AO Data rate limit (429). Cooling down for {cooldown:.0f}s; using fallback prices.",
            )
        else:
            state._set_fallback_status(f"AO Data fetch failed ({error_text}). Using bundled fallback prices.")
        state._append_diag(f"AO Data fetch failed: {error_text}", level="ERROR")
        state._price_index = state._build_fallback_price_index(state.to_setup())
        state._price_context_key = context_key
        state.pricesChanged.emit()
        state._rebuild_preview(force_price_refresh=False)
        return

    price_index = index if isinstance(index, dict) else {}
    if price_index:
        state._price_index = price_index
        state._price_context_key = context_key
        source = str(getattr(meta, "source", "live") or "live")
        record_count = int(getattr(meta, "record_count", len(price_index)) or 0)
        elapsed_ms = float(getattr(meta, "elapsed_ms", 0.0) or 0.0)
        if not force and source == "live":
            state._set_next_live_fetch_cooldown(state._min_live_refresh_interval_seconds)
        state._prices_source = source
        state._prices_status_text = f"{source}: {record_count} rows in {elapsed_ms:.0f} ms"
        state.pricesChanged.emit()
        state._append_diag(
            f"Prices loaded from {source} ({record_count} rows, {elapsed_ms:.0f} ms).",
            level="INFO",
        )
        if (
            source in {"stale_cache", "partial_stale_cache"}
            and not force
            and QCoreApplication.instance() is not None
            and state.refreshCooldownSeconds <= 0
            and not state._deferred_price_refresh_timer.isActive()
            and not state._deferred_force_price_refresh
        ):
            state._append_diag(
                "Stale cache shown first; scheduling background live refresh.",
                level="INFO",
            )
            state._set_prices_status(
                "refreshing_cache",
                f"Showing stale cache ({record_count} rows); background live refresh queued.",
            )
            state._schedule_deferred_price_refresh(0.15, force=True)
    else:
        state._set_fallback_status("AO Data returned no price rows. Using bundled fallback prices.")
        state._append_diag("AO Data returned no rows; using fallback prices.", level="WARN")
        state._price_index = state._build_fallback_price_index(state.to_setup())
        state._price_context_key = context_key

    state._rebuild_preview(force_price_refresh=False)


def shutdown_async_price_fetch(state) -> bool:
    thread = getattr(state, "_price_fetch_thread", None)
    if thread is None:
        return True
    state._price_fetch_result_timer.stop()
    if thread.is_alive():
        return False
    state._price_fetch_thread = None
    state._price_fetch_result_queue = None
    return True


def process_ui_events() -> None:
    app = QCoreApplication.instance()
    if app is None:
        return
    try:
        app.processEvents()
    except Exception:
        return


def should_defer_price_refresh(state) -> bool:
    app = QCoreApplication.instance()
    if app is None:
        return False
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    return len(state._craft_plan_rows) >= 8


def set_prices_status(state, source: str, message: str) -> None:
    state._prices_source = str(source or "fallback")
    state._prices_status_text = message
    state.pricesChanged.emit()


def set_fallback_status(state, message: str) -> None:
    set_prices_status(state, "fallback", message)


def append_diag(state, message: str, *, level: str = "INFO") -> None:
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{now}] {level}: {message}"
    state._diagnostics_lines.append(line)
    if len(state._diagnostics_lines) > 200:
        state._diagnostics_lines = state._diagnostics_lines[-200:]
    state.diagnosticsChanged.emit()


def schedule_deferred_price_refresh(state, delay_seconds: float, *, force: bool = False) -> None:
    if force:
        state._deferred_force_price_refresh = True
    delay_ms = max(50, int(delay_seconds * 1000))
    if state._deferred_price_refresh_timer.isActive():
        remaining = state._deferred_price_refresh_timer.remainingTime()
        if remaining >= 0 and remaining <= delay_ms:
            return
    state._deferred_price_refresh_timer.start(delay_ms)
    state.pricesChanged.emit()


def on_deferred_price_refresh_timeout(state) -> None:
    state.pricesChanged.emit()
    if state._price_fetch_in_progress:
        state._schedule_deferred_price_refresh(
            0.35,
            force=state._deferred_force_price_refresh,
        )
        return
    force_refresh = bool(state._deferred_force_price_refresh)
    state._deferred_force_price_refresh = False
    state._rebuild_preview(force_price_refresh=force_refresh)


def set_next_live_fetch_cooldown(state, seconds: float) -> None:
    target = time.monotonic() + max(0.0, float(seconds))
    state._next_live_fetch_not_before = max(state._next_live_fetch_not_before, target)
    if state.refreshCooldownSeconds > 0:
        if not state._refresh_cooldown_tick_timer.isActive():
            state._refresh_cooldown_tick_timer.start()
    else:
        state._refresh_cooldown_tick_timer.stop()
    state.pricesChanged.emit()


def on_refresh_cooldown_tick(state) -> None:
    if state.refreshCooldownSeconds <= 0:
        state._refresh_cooldown_tick_timer.stop()
    state.pricesChanged.emit()


def _live_batch_count(state, setup, item_ids: list[str], locations: list[str]) -> int:
    batch_count = 0
    try:
        client = getattr(state._service, "client", None)
        if client is not None and hasattr(client, "_split_price_batches") and hasattr(client, "_base_url"):
            base = client._base_url(setup.region)
            params = {
                "locations": ",".join(locations),
                "qualities": ",".join(str(x) for x in state._price_qualities(setup)),
            }
            batch_count = len(client._split_price_batches(base=base, item_ids=item_ids, params=params))
    except Exception:
        batch_count = 0
    return batch_count
