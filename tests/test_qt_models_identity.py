from __future__ import annotations

from albion_dps.qt.models import HistoryModel, HistoryRow, PlayerModel, PlayerRow


def test_history_model_does_not_reset_when_items_are_unchanged() -> None:
    model = HistoryModel()
    counts = {"resets": 0}
    model.modelReset.connect(lambda: counts.__setitem__("resets", counts["resets"] + 1))

    items = [
        HistoryRow(
            label="battle 00:10",
            meta="total dmg 10 heal 0 | players 1",
            players="D4dits dmg 10 dps 1.0",
            copy_text="copy",
            selected=False,
        )
    ]
    model.set_items(items)
    assert counts["resets"] == 1

    model.set_items(list(items))
    assert counts["resets"] == 1


def test_player_model_does_not_reset_when_items_are_unchanged() -> None:
    model = PlayerModel()
    counts = {"resets": 0}
    model.modelReset.connect(lambda: counts.__setitem__("resets", counts["resets"] + 1))

    items = [
        PlayerRow(
            name="D4dits",
            damage=10.0,
            heal=0.0,
            dps=1.0,
            hps=0.0,
            bar_ratio=1.0,
            role="dps",
            color="#ffffff",
            weapon_name="Sword",
            weapon_tier="T4",
            weapon_icon="",
        )
    ]
    model.set_items(items)
    assert counts["resets"] == 1

    model.set_items(list(items))
    assert counts["resets"] == 1
