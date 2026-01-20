from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawPacket:
    timestamp: float
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    payload: bytes


@dataclass(frozen=True)
class PhotonMessage:
    opcode: int
    event_code: int | None
    payload: bytes


@dataclass(frozen=True)
class CombatEvent:
    timestamp: float
    source_id: int
    target_id: int
    amount: int
    kind: str


@dataclass(frozen=True)
class MeterSnapshot:
    timestamp: float
    totals: dict[int, dict[str, float]]
    names: dict[int, str] | None = None
