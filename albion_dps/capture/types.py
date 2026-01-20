from __future__ import annotations

from typing import Iterable, Protocol

from albion_dps.models import RawPacket


class RawPacketSource(Protocol):
    def __iter__(self) -> Iterable[RawPacket]:
        ...
