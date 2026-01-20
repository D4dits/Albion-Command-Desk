from __future__ import annotations

from typing import Protocol

from albion_dps.models import RawPacket, PhotonMessage


class PhotonParser(Protocol):
    def decode(self, packet: RawPacket) -> PhotonMessage | None:
        ...
