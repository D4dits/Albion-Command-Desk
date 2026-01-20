from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PhotonRegistry:
    event_codes: dict[int, str] = field(default_factory=dict)
    operation_codes: dict[int, str] = field(default_factory=dict)

    def is_known_event(self, code: int) -> bool:
        return code in self.event_codes

    def is_known_operation(self, code: int) -> bool:
        return code in self.operation_codes

    def has_event_codes(self) -> bool:
        return bool(self.event_codes)

    def has_operation_codes(self) -> bool:
        return bool(self.operation_codes)


def default_registry() -> PhotonRegistry:
    return PhotonRegistry(event_codes={1: "HealthUpdate"}, operation_codes={1: "Op1"})
