from __future__ import annotations

from typing import Protocol

from albion_dps.models import CombatEvent, MeterSnapshot


class Meter(Protocol):
    def push(self, event: CombatEvent) -> None:
        ...

    def snapshot(self) -> MeterSnapshot:
        ...
