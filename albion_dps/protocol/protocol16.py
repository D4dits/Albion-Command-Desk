from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Any


TYPE_UNKNOWN = 0
TYPE_NULL = 42
TYPE_DICTIONARY = 68
TYPE_STRING_ARRAY = 97
TYPE_BYTE = 98
TYPE_DOUBLE = 100
TYPE_FLOAT = 102
TYPE_INTEGER = 105
TYPE_HASHTABLE = 104
TYPE_SHORT = 107
TYPE_LONG = 108
TYPE_INTEGER_ARRAY = 110
TYPE_BOOLEAN = 111
TYPE_OPERATION_RESPONSE = 112
TYPE_OPERATION_REQUEST = 113
TYPE_STRING = 115
TYPE_BYTE_ARRAY = 120
TYPE_ARRAY = 121
TYPE_OBJECT_ARRAY = 122


class Protocol16Error(ValueError):
    pass


@dataclass(frozen=True)
class EventData:
    code: int
    parameters: dict[int, Any]


@dataclass(frozen=True)
class OperationRequest:
    code: int
    parameters: dict[int, Any]


@dataclass(frozen=True)
class OperationResponse:
    code: int
    return_code: int
    debug_message: str | None
    parameters: dict[int, Any]


def decode_event_data(payload: bytes) -> EventData:
    if not payload:
        raise Protocol16Error("Empty event payload")
    offset = 0
    code = payload[offset]
    offset += 1
    parameters, _ = _decode_parameter_table(payload, offset)
    return EventData(code=code, parameters=parameters)


def decode_operation_request(payload: bytes) -> OperationRequest:
    if not payload:
        raise Protocol16Error("Empty operation payload")
    code = payload[0]
    parameters, _ = _decode_parameter_table(payload, 1)
    return OperationRequest(code=code, parameters=parameters)


def decode_operation_response(payload: bytes) -> OperationResponse:
    if not payload:
        raise Protocol16Error("Empty operation response payload")
    offset = 0
    code, offset = _read_u8(payload, offset)
    return_code, offset = _read_i16(payload, offset)
    try:
        debug_type, offset = _read_u8(payload, offset)
        if debug_type in (TYPE_NULL, TYPE_UNKNOWN):
            debug_message = None
        else:
            debug_message, offset = _decode_value(payload, offset, debug_type)
        parameters, _ = _decode_parameter_table(payload, offset)
        return OperationResponse(
            code=code,
            return_code=return_code,
            debug_message=debug_message,
            parameters=parameters,
        )
    except Protocol16Error:
        offset = 3
        debug_message, offset = _read_string(payload, offset)
        parameters, _ = _decode_parameter_table(payload, offset)
        return OperationResponse(
            code=code,
            return_code=return_code,
            debug_message=debug_message,
            parameters=parameters,
        )


def _decode_parameter_table(payload: bytes, offset: int) -> tuple[dict[int, Any], int]:
    count, offset = _read_u16(payload, offset)
    parameters: dict[int, Any] = {}
    for _ in range(count):
        if offset + 2 > len(payload):
            raise Protocol16Error("Truncated parameter entry")
        key = payload[offset]
        offset += 1
        type_code = payload[offset]
        offset += 1
        value, offset = _decode_value(payload, offset, type_code)
        parameters[key] = value
    return parameters, offset


def _decode_value(payload: bytes, offset: int, type_code: int) -> tuple[Any, int]:
    if type_code in (TYPE_UNKNOWN, TYPE_NULL):
        return None, offset

    if type_code == TYPE_BYTE:
        return _read_u8(payload, offset)
    if type_code == TYPE_BOOLEAN:
        value, offset = _read_u8(payload, offset)
        return value != 0, offset
    if type_code == TYPE_SHORT:
        return _read_i16(payload, offset)
    if type_code == TYPE_INTEGER:
        return _read_i32(payload, offset)
    if type_code == TYPE_LONG:
        return _read_i64(payload, offset)
    if type_code == TYPE_FLOAT:
        return _read_f32(payload, offset)
    if type_code == TYPE_DOUBLE:
        return _read_f64(payload, offset)
    if type_code == TYPE_STRING:
        return _read_string(payload, offset)
    if type_code == TYPE_BYTE_ARRAY:
        return _read_byte_array(payload, offset)
    if type_code == TYPE_INTEGER_ARRAY:
        return _read_int_array(payload, offset)
    if type_code == TYPE_STRING_ARRAY:
        return _read_string_array(payload, offset)
    if type_code == TYPE_OBJECT_ARRAY:
        return _read_object_array(payload, offset)
    if type_code == TYPE_DICTIONARY:
        return _read_dictionary(payload, offset)
    if type_code == TYPE_ARRAY:
        return _read_array(payload, offset)

    raise Protocol16Error(f"Unsupported type code: {type_code}")


def _read_u8(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 1 > len(payload):
        raise Protocol16Error("Truncated byte")
    return payload[offset], offset + 1


def _read_u16(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 2 > len(payload):
        raise Protocol16Error("Truncated short")
    value = struct.unpack_from(">H", payload, offset)[0]
    return value, offset + 2


def _read_i16(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 2 > len(payload):
        raise Protocol16Error("Truncated short")
    value = struct.unpack_from(">h", payload, offset)[0]
    return value, offset + 2


def _read_i32(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 4 > len(payload):
        raise Protocol16Error("Truncated int")
    value = struct.unpack_from(">i", payload, offset)[0]
    return value, offset + 4


def _read_i64(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 8 > len(payload):
        raise Protocol16Error("Truncated long")
    value = struct.unpack_from(">q", payload, offset)[0]
    return value, offset + 8


def _read_f32(payload: bytes, offset: int) -> tuple[float, int]:
    if offset + 4 > len(payload):
        raise Protocol16Error("Truncated float")
    value = struct.unpack_from(">f", payload, offset)[0]
    return value, offset + 4


def _read_f64(payload: bytes, offset: int) -> tuple[float, int]:
    if offset + 8 > len(payload):
        raise Protocol16Error("Truncated double")
    value = struct.unpack_from(">d", payload, offset)[0]
    return value, offset + 8


def _read_string(payload: bytes, offset: int) -> tuple[str, int]:
    length, offset = _read_u16(payload, offset)
    if length == 0:
        return "", offset
    end = offset + length
    if end > len(payload):
        raise Protocol16Error("Truncated string")
    value = payload[offset:end].decode("utf-8", errors="replace")
    return value, end


def _read_byte_array(payload: bytes, offset: int) -> tuple[bytes, int]:
    length, offset = _read_i32(payload, offset)
    if length < 0:
        raise Protocol16Error("Negative byte array length")
    end = offset + length
    if end > len(payload):
        raise Protocol16Error("Truncated byte array")
    return payload[offset:end], end


def _read_int_array(payload: bytes, offset: int) -> tuple[list[int], int]:
    length, offset = _read_i32(payload, offset)
    if length < 0:
        raise Protocol16Error("Negative int array length")
    values = []
    for _ in range(length):
        value, offset = _read_i32(payload, offset)
        values.append(value)
    return values, offset


def _read_string_array(payload: bytes, offset: int) -> tuple[list[str], int]:
    length, offset = _read_u16(payload, offset)
    values = []
    for _ in range(length):
        value, offset = _read_string(payload, offset)
        values.append(value)
    return values, offset


def _read_object_array(payload: bytes, offset: int) -> tuple[list[Any], int]:
    length, offset = _read_u16(payload, offset)
    values = []
    for _ in range(length):
        type_code, offset = _read_u8(payload, offset)
        value, offset = _decode_value(payload, offset, type_code)
        values.append(value)
    return values, offset


def _read_dictionary(payload: bytes, offset: int) -> tuple[dict[Any, Any], int]:
    key_type, offset = _read_u8(payload, offset)
    value_type, offset = _read_u8(payload, offset)
    size, offset = _read_u16(payload, offset)
    output: dict[Any, Any] = {}
    for _ in range(size):
        key_type_code = key_type
        value_type_code = value_type
        if key_type_code in (TYPE_UNKNOWN, TYPE_NULL):
            key_type_code, offset = _read_u8(payload, offset)
        if value_type_code in (TYPE_UNKNOWN, TYPE_NULL):
            value_type_code, offset = _read_u8(payload, offset)
        key, offset = _decode_value(payload, offset, key_type_code)
        value, offset = _decode_value(payload, offset, value_type_code)
        output[key] = value
    return output, offset


def _read_array(payload: bytes, offset: int) -> tuple[list[Any], int]:
    length, offset = _read_u16(payload, offset)
    type_code, offset = _read_u8(payload, offset)

    if type_code == TYPE_ARRAY:
        values: list[Any] = []
        for _ in range(length):
            value, offset = _read_array(payload, offset)
            values.append(value)
        return values, offset

    if type_code == TYPE_BYTE_ARRAY:
        values = []
        for _ in range(length):
            value, offset = _read_byte_array(payload, offset)
            values.append(value)
        return values, offset

    if type_code == TYPE_DICTIONARY:
        return _read_dictionary_array(payload, offset, length)

    values = []
    for _ in range(length):
        value, offset = _decode_value(payload, offset, type_code)
        values.append(value)
    return values, offset


def _read_dictionary_array(
    payload: bytes, offset: int, length: int
) -> tuple[list[dict[Any, Any]], int]:
    key_type, offset = _read_u8(payload, offset)
    value_type, offset = _read_u8(payload, offset)
    values: list[dict[Any, Any]] = []
    for _ in range(length):
        size, offset = _read_u16(payload, offset)
        dictionary: dict[Any, Any] = {}
        for _ in range(size):
            key_type_code = key_type
            value_type_code = value_type
            if key_type_code in (TYPE_UNKNOWN, TYPE_NULL):
                key_type_code, offset = _read_u8(payload, offset)
            if value_type_code in (TYPE_UNKNOWN, TYPE_NULL):
                value_type_code, offset = _read_u8(payload, offset)
            key, offset = _decode_value(payload, offset, key_type_code)
            value, offset = _decode_value(payload, offset, value_type_code)
            dictionary[key] = value
        values.append(dictionary)
    return values, offset
