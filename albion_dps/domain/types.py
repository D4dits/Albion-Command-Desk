from __future__ import annotations

from typing import Protocol

from albion_dps.models import CombatEvent


class DomainState(Protocol):
    def apply(self, event: CombatEvent) -> CombatEvent:
        ...
