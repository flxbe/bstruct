from io import BytesIO
from typing import (
    Any,
    Generic,
    TypeVar,
    Callable,
    Literal,
    Optional,
    Annotated,
    Union,
)
import typing
import dataclasses
from enum import IntEnum
from struct import Struct
from decimal import Decimal


# TODO: add support for big endian


__version__ = "0.1.0"


T = TypeVar("T")


IntDecoder = Callable[[int], T]
BytesDecoder = Callable[[bytes], T]
Decoder = Union[IntDecoder[T], BytesDecoder[T]]


IntEncoder = Callable[[T], int]
BytesEncoder = Callable[[T], bytes]
Encoder = Union[IntEncoder[T], BytesEncoder[T]]


ByteOrder = Literal["big", "little"]


class _BinaryData(Generic[T]):
    def __init__(self, size: int, decode: BytesDecoder[T], encode: BytesEncoder[T]):
        self.size = size
        self.decode = decode
        self.encode = encode


_IntSize = Literal[8, 16, 32, 64, 128, 256]


class UnsignedInteger:
    def __init__(self, size: _IntSize):
        self.size = size


u8 = Annotated[int, UnsignedInteger(8)]
u16 = Annotated[int, UnsignedInteger(16)]
u32 = Annotated[int, UnsignedInteger(32)]
u64 = Annotated[int, UnsignedInteger(64)]
u128 = Annotated[int, UnsignedInteger(128)]
u256 = Annotated[int, UnsignedInteger(256)]


class SignedInteger:
    def __init__(self, size: _IntSize):
        self.size = size


i8 = Annotated[int, SignedInteger(8)]
i16 = Annotated[int, SignedInteger(16)]
i32 = Annotated[int, SignedInteger(32)]
i64 = Annotated[int, SignedInteger(64)]
i128 = Annotated[int, SignedInteger(128)]
i256 = Annotated[int, SignedInteger(256)]


class Length:
    def __init__(self, length: int):
        assert length > 0

        self.length = length


class Size:
    def __init__(self, size: int):
        assert size > 0

        self.size = size


class _I80F48:
    pass


I80F48 = Annotated[Decimal, _I80F48()]


def _resolve_parser(
    attribute_type: Any,
) -> tuple[str, Optional[Decoder[Any]], Optional[Encoder[Any]]]:
    if isinstance(attribute_type, str):
        raise Exception(
            "Do not use 'from __future__ import annotation' in the same file in which 'binary.derive()' is used."
        )

    if attribute_type is bool:
        return "?", None, None
    elif typing.get_origin(attribute_type) is typing.Annotated:
        annotated_type, *annotation_args = typing.get_args(attribute_type)

        if annotated_type is int:
            return _resolve_int_encoding(annotation_args)
        elif issubclass(annotated_type, IntEnum):
            return _resolve_int_enum_encoding(annotated_type, annotation_args)
        elif annotated_type is str:
            return _resolve_str_encoding(annotation_args)
        elif annotated_type is bytes:
            return _resolve_bytes_encoding(annotation_args)
        elif annotated_type is Decimal:
            return _resolve_decimal_encoding(annotation_args)
        elif annotated_type is list:
            raise TypeError("Inner type for list needed.")
        elif typing.get_origin(annotated_type) is list:
            return _resolve_array_encoding(annotated_type, annotation_args)
    elif _has_binary_data(attribute_type):
        return _resolve_custom_encoding(attribute_type)

    assert False


def _resolve_array_encoding(
    array_type: Any, metadata: list[Any]
) -> tuple[str, BytesDecoder[Any], BytesEncoder[Any]]:
    array_length = _resolve_array_length(metadata)

    array_type_args = typing.get_args(array_type)
    assert len(array_type_args) == 1
    inner_type = array_type_args[0]

    inner_format, inner_decode, inner_encode = _resolve_parser(inner_type)

    array_format = "".join([inner_format] * array_length)
    array_struct = Struct(array_format)

    total_array_format = f"{array_struct.size}s"

    if inner_decode is None:
        decode: BytesDecoder[list] = lambda data: list(array_struct.unpack(data))
    else:
        decode: BytesDecoder[list] = lambda data: [
            inner_decode(v) for v in array_struct.unpack(data)  # type: ignore
        ]

    if inner_encode is None:
        encode: BytesEncoder[list[Any]] = lambda l: array_struct.pack(*l)
    else:
        encode: BytesEncoder[list[Any]] = lambda l: array_struct.pack(*(inner_encode(v) for v in l))  # type: ignore

    return total_array_format, decode, encode


def _resolve_array_length(metadata: list[Any]) -> int:
    for data in metadata:
        if isinstance(data, Length):
            return data.length

    raise TypeError("Cannot find length annotation for list")


def _resolve_int_encoding(
    metadata: list[Any],
) -> tuple[str, Optional[BytesDecoder[int]], Optional[BytesEncoder[int]]]:
    for data in metadata:
        if isinstance(data, UnsignedInteger):
            if data.size == 8:
                return "B", None, None
            elif data.size == 16:
                return "H", None, None
            elif data.size == 32:
                return "I", None, None
            elif data.size == 64:
                return "Q", None, None
            elif data.size == 128:
                return "16s", _decode_uint, _encode_uint128
            elif data.size == 256:
                return "32s", _decode_uint, _encode_uint256
            else:
                assert False
        elif isinstance(data, SignedInteger):
            if data.size == 8:
                return "b", None, None
            elif data.size == 16:
                return "h", None, None
            elif data.size == 32:
                return "i", None, None
            elif data.size == 64:
                return "q", None, None
            elif data.size == 128:
                return "16s", _decode_int, _encode_int128
            elif data.size == 256:
                return "32s", _decode_int, _encode_int256
            else:
                assert False

    raise TypeError("Cannot find integer type annotation")


def _decode_uint(data: bytes) -> int:
    return int.from_bytes(data, "little", signed=False)


def _encode_uint128(value: int) -> bytes:
    return value.to_bytes(16, byteorder="little", signed=False)


def _encode_uint256(value: int) -> bytes:
    return value.to_bytes(32, byteorder="little", signed=False)


def _decode_int(data: bytes) -> int:
    return int.from_bytes(data, "little", signed=True)


def _encode_int128(value: int) -> bytes:
    return value.to_bytes(16, byteorder="little", signed=True)


def _encode_int256(value: int) -> bytes:
    return value.to_bytes(32, byteorder="little", signed=True)


def _resolve_int_enum_encoding(
    cls: type[IntEnum], metadata: list[Any]
) -> tuple[str, Decoder[IntEnum], Optional[Encoder[IntEnum]]]:
    for data in metadata:
        if isinstance(data, UnsignedInteger):
            if data.size == 8:
                return "B", cls, None
            elif data.size == 16:
                return "H", cls, None
            elif data.size == 32:
                return "I", cls, None
            elif data.size == 64:
                return "Q", cls, None
            elif data.size == 128:

                def _decode_cls(data: bytes) -> IntEnum:
                    return cls(_decode_uint(data))

                return "16s", _decode_cls, _encode_uint128
            elif data.size == 256:

                def _decode_cls(data: bytes) -> IntEnum:
                    return cls(_decode_uint(data))

                return "32s", _decode_cls, _encode_uint256
            else:
                assert False

    raise TypeError("Cannot find integer type annotation")


def _resolve_str_encoding(
    metadata: list[Any],
) -> tuple[str, BytesDecoder[str], BytesEncoder[str]]:
    for data in metadata:
        if isinstance(data, Size):
            return (
                f"{data.size}s",
                _decode_str,
                _encode_str,
            )

    raise TypeError("Cannot find string type annotation")


def _decode_str(value: bytes) -> str:
    return value.rstrip(b"\0").decode("utf-8")


def _encode_str(value: str) -> bytes:
    # The `struct` library automatically adds zeros to the end of
    # the encoded string to fill the necessary `data.size` bytes.
    return value.encode("utf-8")


def _resolve_bytes_encoding(metadata: list[Any]) -> tuple[str, None, None]:
    for data in metadata:
        if isinstance(data, Size):
            return f"{data.size}s", None, None

    raise TypeError("Cannot find bytes type annotation")


def _resolve_decimal_encoding(
    metadata: list[Any],
) -> tuple[str, BytesDecoder[Decimal], BytesEncoder[Decimal]]:
    for data in metadata:
        if isinstance(data, _I80F48):
            return "16s", _decode_I80F48, _encode_I80F48

    raise TypeError("Cannot find decimal type annotation")


# The last 6 bytes (== 6 * 8 == 48 bits) of the 16 byte value is the fractional part.
# Therefore, divide by 2^48.
I80F48_DIVISOR = Decimal(2**48)


def _decode_I80F48(data: bytes) -> Decimal:
    return int.from_bytes(data, "little", signed=True) / I80F48_DIVISOR


def _encode_I80F48(value: Decimal) -> bytes:
    return int(value * I80F48_DIVISOR).to_bytes(16, "little", signed=True)


def _resolve_custom_encoding(
    cls: type[T],
) -> tuple[str, BytesDecoder[T], BytesEncoder[T]]:
    binary_data = _get_binary_data(cls)

    return f"{binary_data.size}s", binary_data.decode, binary_data.encode


def derive(*, byte_order: ByteOrder = "little") -> Callable[[type[T]], type[T]]:
    return lambda cls: _derive(cls, byte_order=byte_order)


def _derive(cls: type[T], byte_order: ByteOrder) -> type[T]:
    if not dataclasses.is_dataclass(cls):
        raise TypeError("Class must be a dataclass")

    fields = dataclasses.fields(cls)

    attribute_decoders: list[Optional[Decoder[Any]]] = []
    attribute_encoders: list[Optional[Encoder[Any]]] = []
    full_format = "<"
    for field in fields:
        format, decoder, encoder = _resolve_parser(field.type)

        full_format += format
        attribute_decoders.append(decoder)
        attribute_encoders.append(encoder)

    struct = Struct(full_format)
    attribute_names = [field.name for field in fields]

    def _decode(data: bytes) -> T:
        if len(data) != struct.size:
            raise ValueError(
                f"Invalid data size: Expected {struct.size} bytes, but got {len(data)}"
            )

        raw_attributes = struct.unpack(data)

        attributes = (
            decode_attribute(d) if decode_attribute is not None else d
            for decode_attribute, d in zip(attribute_decoders, raw_attributes)
        )

        return cls(*attributes)

    def _encode(value: T) -> bytes:
        raw_attributes = (
            encode_attribute(getattr(value, name))
            if encode_attribute is not None
            else getattr(value, name)
            for encode_attribute, name in zip(attribute_encoders, attribute_names)
        )

        return struct.pack(*raw_attributes)

    binary_data = _BinaryData(struct.size, _decode, _encode)
    _set_binary_data(cls, binary_data)

    return cls


def patch(
    cls: type[T], size: int, decode: BytesDecoder[T], encode: BytesEncoder[T]
) -> None:
    binary_data = _BinaryData(size, decode, encode)
    _set_binary_data(cls, binary_data)


def decode(cls: type[T], data: bytes, strict: bool = True) -> T:
    binary_data = _get_binary_data(cls)

    if not strict:
        data = data[: binary_data.size]

    return binary_data.decode(data)


def decode_from(cls: type[T], data_stream: BytesIO) -> T:
    binary_data = _get_binary_data(cls)

    data = data_stream.read(binary_data.size)

    return binary_data.decode(data)


def encode(value: Any) -> bytes:
    cls = type(value)
    binary_data = _get_binary_data(cls)
    return binary_data.encode(value)


def get_size(cls: Any) -> int:
    binary_data = _get_binary_data(cls)
    return binary_data.size


def _get_binary_data(cls: type[T]) -> _BinaryData[T]:
    return getattr(cls, "__binary_data")


def _set_binary_data(cls: type[T], data: _BinaryData[T]) -> None:
    setattr(cls, "__binary_data", data)


def _has_binary_data(cls: Any) -> bool:
    return hasattr(cls, "__binary_data")
