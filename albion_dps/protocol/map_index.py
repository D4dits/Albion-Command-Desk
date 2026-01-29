from __future__ import annotations

from albion_dps.models import PhotonMessage
from albion_dps.protocol.protocol16 import (
    OperationResponse,
    Protocol16Error,
    decode_operation_response,
)

OPERATION_CODE_KEY = 253
JOIN_OPERATION_CODE = 2
CHANGE_CLUSTER_OPERATION_CODE = 35
JOIN_MAP_INDEX_KEY = 8
CHANGE_CLUSTER_INDEX_KEY = 0


def extract_map_index(message: PhotonMessage) -> str | None:
    if message.event_code is not None:
        return None
    try:
        response = decode_operation_response(message.payload)
    except Protocol16Error:
        return None
    return extract_map_index_from_response(response)


def extract_map_index_from_response(response: OperationResponse) -> str | None:
    op_code = response.parameters.get(OPERATION_CODE_KEY, response.code)
    if op_code == JOIN_OPERATION_CODE:
        return _normalize_map_index(response.parameters.get(JOIN_MAP_INDEX_KEY))
    if op_code == CHANGE_CLUSTER_OPERATION_CODE:
        return _normalize_map_index(response.parameters.get(CHANGE_CLUSTER_INDEX_KEY))
    return None


def _normalize_map_index(value: object) -> str | None:
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        if not value:
            return None
        if "@" in value:
            head = value.split("@", 1)[0]
            return head or value
        return value
    return None
