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

V18_TYPE_UNKNOWN = 0
V18_TYPE_BOOLEAN = 2
V18_TYPE_BYTE = 3
V18_TYPE_SHORT = 4
V18_TYPE_FLOAT = 5
V18_TYPE_DOUBLE = 6
V18_TYPE_STRING = 7
V18_TYPE_NULL = 8
V18_TYPE_COMPRESSED_INT = 9
V18_TYPE_COMPRESSED_LONG = 10
V18_TYPE_INT1 = 11
V18_TYPE_INT1_NEGATIVE = 12
V18_TYPE_INT2 = 13
V18_TYPE_INT2_NEGATIVE = 14
V18_TYPE_LONG1 = 15
V18_TYPE_LONG1_NEGATIVE = 16
V18_TYPE_LONG2 = 17
V18_TYPE_LONG2_NEGATIVE = 18
V18_TYPE_CUSTOM = 19
V18_TYPE_DICTIONARY = 20
V18_TYPE_HASHTABLE = 21
V18_TYPE_OBJECT_ARRAY = 23
V18_TYPE_BOOLEAN_FALSE = 27
V18_TYPE_BOOLEAN_TRUE = 28
V18_TYPE_SHORT_ZERO = 29
V18_TYPE_INT_ZERO = 30
V18_TYPE_LONG_ZERO = 31
V18_TYPE_FLOAT_ZERO = 32
V18_TYPE_DOUBLE_ZERO = 33
V18_TYPE_BYTE_ZERO = 34
V18_TYPE_ARRAY_FLAG = 0x40
MAX_COLLECTION_LENGTH = 4096


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
    try:
        parameters, _ = _decode_parameter_table(payload, offset)
        return EventData(code=code, parameters=parameters)
    except Protocol16Error as exc:
        try:
            return _decode_event_data_v18(payload)
        except Protocol16Error:
            raise exc


def decode_operation_request(payload: bytes) -> OperationRequest:
    if not payload:
        raise Protocol16Error("Empty operation payload")
    code = payload[0]
    try:
        parameters, _ = _decode_parameter_table(payload, 1)
        return OperationRequest(code=code, parameters=parameters)
    except Protocol16Error as exc:
        try:
            return _decode_operation_request_v18(payload)
        except Protocol16Error:
            raise exc


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
        try:
            offset = 3
            debug_message, offset = _read_string(payload, offset)
            parameters, _ = _decode_parameter_table(payload, offset)
            return OperationResponse(
                code=code,
                return_code=return_code,
                debug_message=debug_message,
                parameters=parameters,
            )
        except Protocol16Error as exc:
            try:
                return _decode_operation_response_v18(payload)
            except Protocol16Error:
                raise exc


def _decode_parameter_table(payload: bytes, offset: int) -> tuple[dict[int, Any], int]:
    count, offset = _read_u16(payload, offset)
    if count > (len(payload) - offset) // 2:
        raise Protocol16Error(f"Invalid parameter count: {count}")
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


def _decode_event_data_v18(payload: bytes) -> EventData:
    offset = 0
    code, offset = _read_u8(payload, offset)
    parameters, offset = _decode_parameter_table_v18(payload, offset)
    if offset != len(payload):
        raise Protocol16Error("Trailing bytes in Protocol18 event payload")
    return EventData(code=code, parameters=parameters)


def _decode_operation_request_v18(payload: bytes) -> OperationRequest:
    offset = 0
    code, offset = _read_u8(payload, offset)
    parameters, offset = _decode_parameter_table_v18(payload, offset)
    if offset != len(payload):
        raise Protocol16Error("Trailing bytes in Protocol18 operation payload")
    return OperationRequest(code=code, parameters=parameters)


def _decode_operation_response_v18(payload: bytes) -> OperationResponse:
    offset = 0
    code, offset = _read_u8(payload, offset)
    return_code, offset = _read_i16_le(payload, offset)
    debug_type, offset = _read_u8(payload, offset)
    if debug_type in (V18_TYPE_UNKNOWN, V18_TYPE_NULL):
        debug_message = None
    else:
        debug_value, offset = _decode_value_v18(payload, offset, debug_type)
        debug_message = str(debug_value) if debug_value is not None else None
    parameters, offset = _decode_parameter_table_v18(payload, offset)
    if offset != len(payload):
        raise Protocol16Error("Trailing bytes in Protocol18 operation response payload")
    return OperationResponse(
        code=code,
        return_code=return_code,
        debug_message=debug_message,
        parameters=parameters,
    )


def _decode_parameter_table_v18(payload: bytes, offset: int) -> tuple[dict[int, Any], int]:
    count, offset = _read_compressed_int_v18(payload, offset)
    if count < 0 or count > 4096:
        raise Protocol16Error(f"Invalid Protocol18 parameter count: {count}")
    parameters: dict[int, Any] = {}
    for _ in range(count):
        if offset + 2 > len(payload):
            raise Protocol16Error("Truncated Protocol18 parameter entry")
        key, offset = _read_u8(payload, offset)
        type_code, offset = _read_u8(payload, offset)
        value, offset = _decode_value_v18(payload, offset, type_code)
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


def _decode_value_v18(payload: bytes, offset: int, type_code: int) -> tuple[Any, int]:
    if type_code in (V18_TYPE_UNKNOWN, V18_TYPE_NULL):
        return None, offset
    if type_code == V18_TYPE_BOOLEAN:
        value, offset = _read_u8(payload, offset)
        if value not in (0, 1):
            raise Protocol16Error(f"Invalid Protocol18 boolean: {value}")
        return value == 1, offset
    if type_code == V18_TYPE_BYTE:
        return _read_u8(payload, offset)
    if type_code == V18_TYPE_SHORT:
        return _read_i16_le(payload, offset)
    if type_code == V18_TYPE_FLOAT:
        return _read_f32_le(payload, offset)
    if type_code == V18_TYPE_DOUBLE:
        return _read_f64_le(payload, offset)
    if type_code == V18_TYPE_STRING:
        return _read_string_v18(payload, offset)
    if type_code == V18_TYPE_COMPRESSED_INT:
        return _read_compressed_int_v18(payload, offset)
    if type_code == V18_TYPE_COMPRESSED_LONG:
        return _read_compressed_int_v18(payload, offset)
    if type_code == V18_TYPE_INT1:
        return _read_u8(payload, offset)
    if type_code == V18_TYPE_INT1_NEGATIVE:
        value, offset = _read_u8(payload, offset)
        return -value, offset
    if type_code == V18_TYPE_INT2:
        return _read_u16_le(payload, offset)
    if type_code == V18_TYPE_INT2_NEGATIVE:
        value, offset = _read_u16_le(payload, offset)
        return -value, offset
    if type_code == V18_TYPE_LONG1:
        return _read_u8(payload, offset)
    if type_code == V18_TYPE_LONG1_NEGATIVE:
        value, offset = _read_u8(payload, offset)
        return -value, offset
    if type_code == V18_TYPE_LONG2:
        return _read_u16_le(payload, offset)
    if type_code == V18_TYPE_LONG2_NEGATIVE:
        value, offset = _read_u16_le(payload, offset)
        return -value, offset
    if type_code == V18_TYPE_CUSTOM:
        return _read_custom_v18(payload, offset)
    if type_code == V18_TYPE_DICTIONARY:
        return _read_dictionary_v18(payload, offset)
    if type_code == V18_TYPE_HASHTABLE:
        return _read_hashtable_v18(payload, offset)
    if type_code == V18_TYPE_OBJECT_ARRAY:
        return _read_object_array_v18(payload, offset)
    if type_code == V18_TYPE_BOOLEAN_FALSE:
        return False, offset
    if type_code == V18_TYPE_BOOLEAN_TRUE:
        return True, offset
    if type_code in (
        V18_TYPE_SHORT_ZERO,
        V18_TYPE_INT_ZERO,
        V18_TYPE_LONG_ZERO,
        V18_TYPE_FLOAT_ZERO,
        V18_TYPE_DOUBLE_ZERO,
        V18_TYPE_BYTE_ZERO,
    ):
        return 0, offset
    if type_code & V18_TYPE_ARRAY_FLAG:
        element_type = type_code & ~V18_TYPE_ARRAY_FLAG
        return _read_array_v18(payload, offset, element_type)
    raise Protocol16Error(f"Unsupported Protocol18 type code: {type_code}")


def _read_u8(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 1 > len(payload):
        raise Protocol16Error("Truncated byte")
    return payload[offset], offset + 1


def _read_u16(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 2 > len(payload):
        raise Protocol16Error("Truncated short")
    value = struct.unpack_from(">H", payload, offset)[0]
    return value, offset + 2


def _read_u16_le(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 2 > len(payload):
        raise Protocol16Error("Truncated Protocol18 short")
    value = struct.unpack_from("<H", payload, offset)[0]
    return value, offset + 2


def _read_i16(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 2 > len(payload):
        raise Protocol16Error("Truncated short")
    value = struct.unpack_from(">h", payload, offset)[0]
    return value, offset + 2


def _read_i16_le(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 2 > len(payload):
        raise Protocol16Error("Truncated Protocol18 short")
    value = struct.unpack_from("<h", payload, offset)[0]
    return value, offset + 2


def _read_i32(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 4 > len(payload):
        raise Protocol16Error("Truncated int")
    value = struct.unpack_from(">i", payload, offset)[0]
    return value, offset + 4


def _read_i32_le(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 4 > len(payload):
        raise Protocol16Error("Truncated Protocol18 int")
    value = struct.unpack_from("<i", payload, offset)[0]
    return value, offset + 4


def _read_i64(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 8 > len(payload):
        raise Protocol16Error("Truncated long")
    value = struct.unpack_from(">q", payload, offset)[0]
    return value, offset + 8


def _read_i64_le(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 8 > len(payload):
        raise Protocol16Error("Truncated Protocol18 long")
    value = struct.unpack_from("<q", payload, offset)[0]
    return value, offset + 8


def _read_f32(payload: bytes, offset: int) -> tuple[float, int]:
    if offset + 4 > len(payload):
        raise Protocol16Error("Truncated float")
    value = struct.unpack_from(">f", payload, offset)[0]
    return value, offset + 4


def _read_f32_le(payload: bytes, offset: int) -> tuple[float, int]:
    if offset + 4 > len(payload):
        raise Protocol16Error("Truncated Protocol18 float")
    value = struct.unpack_from("<f", payload, offset)[0]
    return value, offset + 4


def _read_f64(payload: bytes, offset: int) -> tuple[float, int]:
    if offset + 8 > len(payload):
        raise Protocol16Error("Truncated double")
    value = struct.unpack_from(">d", payload, offset)[0]
    return value, offset + 8


def _read_f64_le(payload: bytes, offset: int) -> tuple[float, int]:
    if offset + 8 > len(payload):
        raise Protocol16Error("Truncated Protocol18 double")
    value = struct.unpack_from("<d", payload, offset)[0]
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


def _read_string_v18(payload: bytes, offset: int) -> tuple[str, int]:
    length, offset = _read_compressed_int_v18(payload, offset)
    if length < 0:
        raise Protocol16Error("Negative Protocol18 string length")
    end = offset + length
    if end > len(payload):
        raise Protocol16Error("Truncated Protocol18 string")
    value = payload[offset:end].decode("utf-8", errors="replace")
    return value, end


def _read_compressed_int_v18(payload: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if offset >= len(payload):
            raise Protocol16Error("Truncated Protocol18 compressed integer")
        byte = payload[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
        if shift > 63:
            raise Protocol16Error("Protocol18 compressed integer is too large")


def _read_custom_v18(payload: bytes, offset: int) -> tuple[bytes, int]:
    _custom_type, offset = _read_u8(payload, offset)
    length, offset = _read_compressed_int_v18(payload, offset)
    if length < 0:
        raise Protocol16Error("Negative Protocol18 custom value length")
    end = offset + length
    if end > len(payload):
        raise Protocol16Error("Truncated Protocol18 custom value")
    return payload[offset:end], end


def _read_array_v18(payload: bytes, offset: int, element_type: int) -> tuple[list[Any], int]:
    length, offset = _read_compressed_int_v18(payload, offset)
    if length < 0 or length > MAX_COLLECTION_LENGTH:
        raise Protocol16Error(f"Invalid Protocol18 array length: {length}")
    values: list[Any] = []
    for _ in range(length):
        value, offset = _decode_value_v18(payload, offset, element_type)
        values.append(value)
    return values, offset


def _read_object_array_v18(payload: bytes, offset: int) -> tuple[list[Any], int]:
    length, offset = _read_compressed_int_v18(payload, offset)
    if length < 0 or length > MAX_COLLECTION_LENGTH:
        raise Protocol16Error(f"Invalid Protocol18 object array length: {length}")
    values: list[Any] = []
    for _ in range(length):
        type_code, offset = _read_u8(payload, offset)
        value, offset = _decode_value_v18(payload, offset, type_code)
        values.append(value)
    return values, offset


def _read_dictionary_v18(payload: bytes, offset: int) -> tuple[dict[Any, Any], int]:
    key_type, offset = _read_u8(payload, offset)
    value_type, offset = _read_u8(payload, offset)
    length, offset = _read_compressed_int_v18(payload, offset)
    if length < 0 or length > MAX_COLLECTION_LENGTH:
        raise Protocol16Error(f"Invalid Protocol18 dictionary length: {length}")
    output: dict[Any, Any] = {}
    for _ in range(length):
        key, offset = _decode_value_v18(payload, offset, key_type)
        value, offset = _decode_value_v18(payload, offset, value_type)
        output[_dictionary_key(key)] = value
    return output, offset


def _read_hashtable_v18(payload: bytes, offset: int) -> tuple[dict[Any, Any], int]:
    length, offset = _read_compressed_int_v18(payload, offset)
    if length < 0 or length > MAX_COLLECTION_LENGTH:
        raise Protocol16Error(f"Invalid Protocol18 hashtable length: {length}")
    output: dict[Any, Any] = {}
    for _ in range(length):
        key_type, offset = _read_u8(payload, offset)
        key, offset = _decode_value_v18(payload, offset, key_type)
        value_type, offset = _read_u8(payload, offset)
        value, offset = _decode_value_v18(payload, offset, value_type)
        output[_dictionary_key(key)] = value
    return output, offset


def _dictionary_key(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_dictionary_key(item) for item in value)
    if isinstance(value, dict):
        return tuple(
            (_dictionary_key(key), _dictionary_key(item))
            for key, item in value.items()
        )
    if isinstance(value, bytearray):
        return bytes(value)
    try:
        hash(value)
    except TypeError as exc:
        raise Protocol16Error(
            f"Unhashable dictionary key: {type(value).__name__}"
        ) from exc
    return value


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
    if length < 0 or length > MAX_COLLECTION_LENGTH:
        raise Protocol16Error(f"Invalid int array length: {length}")
    values = []
    for _ in range(length):
        value, offset = _read_i32(payload, offset)
        values.append(value)
    return values, offset


def _read_string_array(payload: bytes, offset: int) -> tuple[list[str], int]:
    length, offset = _read_u16(payload, offset)
    if length > MAX_COLLECTION_LENGTH:
        raise Protocol16Error(f"Invalid string array length: {length}")
    values = []
    for _ in range(length):
        value, offset = _read_string(payload, offset)
        values.append(value)
    return values, offset


def _read_object_array(payload: bytes, offset: int) -> tuple[list[Any], int]:
    length, offset = _read_u16(payload, offset)
    if length > MAX_COLLECTION_LENGTH:
        raise Protocol16Error(f"Invalid object array length: {length}")
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
    if size > MAX_COLLECTION_LENGTH:
        raise Protocol16Error(f"Invalid dictionary length: {size}")
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
        output[_dictionary_key(key)] = value
    return output, offset


def _read_array(payload: bytes, offset: int) -> tuple[list[Any], int]:
    length, offset = _read_u16(payload, offset)
    if length > MAX_COLLECTION_LENGTH:
        raise Protocol16Error(f"Invalid array length: {length}")
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
        if size > MAX_COLLECTION_LENGTH:
            raise Protocol16Error(f"Invalid dictionary length: {size}")
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
            dictionary[_dictionary_key(key)] = value
        values.append(dictionary)
    return values, offset
