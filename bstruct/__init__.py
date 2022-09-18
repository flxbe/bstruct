from __future__ import annotations
from io import BytesIO
from typing import (
    Any,
    Generic,
    Iterator,
    TypeVar,
    Callable,
    Literal,
    Optional,
    Annotated,
)
import typing
import dataclasses
from enum import IntEnum
from struct import Struct, error as StructError
from decimal import Decimal


# TODO:
# - add support for different byte orders
# - create Benchmark with different implementations
# - Handle struct errors
# - Allow variably sized list/bytes attribute at the end of a struct
# - Test behaviour when using 'NewType'


__version__ = "0.1.0"


T = TypeVar("T")

BytesDecoder = Callable[[bytes], T]
BytesEncoder = Callable[[T], bytes]

Decoder = Callable[[Iterator[Any]], T]
Encoder = Callable[[T, list[Any]], None]

ByteOrder = Literal["big", "little"]


class _StructData(Generic[T]):
    def __init__(
        self,
        format: str,
        decode: Decoder[T],
        encode: Encoder[T],
    ):
        self.format = format
        self.struct = Struct(f"<{format}")
        self.size = self.struct.size

        self.decode = decode
        self.encode = encode

    @staticmethod
    def create_patched_data(
        size: int, decode: BytesDecoder[T], encode: BytesEncoder[T]
    ) -> _StructData[T]:
        return _StructData(
            format=f"{size}s",
            decode=lambda iterator: decode(next(iterator)),
            encode=lambda t, l: l.append(encode(t)),
        )


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
    elif _has_struct_data(attribute_type):
        return _resolve_custom_encoding(attribute_type)

    assert False


def _resolve_array_encoding(
    array_type: Any, metadata: list[Any]
) -> tuple[str, Decoder[Any], Encoder[Any]]:
    array_length = _resolve_array_length(metadata)

    array_type_args = typing.get_args(array_type)
    assert len(array_type_args) == 1
    inner_type = array_type_args[0]

    inner_format, inner_decode, inner_encode = _resolve_parser(inner_type)
    array_format = "".join([inner_format] * array_length)

    if inner_decode is None:
        assert inner_encode is None

        # If the array consists of simple, native elements, decode the complete array directly.

        def _decode(attributes: Iterator[Any]) -> list[Any]:
            return [next(attributes) for _ in range(array_length)]

        def _encode(l: list[Any], attributes: list[Any]) -> None:
            attributes.extend(l)

    elif inner_encode is None:
        assert inner_decode is not None

        # If only the decoder must process the items

        # Reassign to new variable to avoid type checking errors of inner_decode
        # being None
        _inner_decode = inner_decode

        def _decode(attributes: Iterator[Any]) -> list[Any]:
            return [_inner_decode(attributes) for _ in range(array_length)]

        def _encode(l: list[Any], attributes: list[Any]) -> None:
            attributes.extend(l)

    else:
        assert inner_decode is not None
        assert inner_encode is not None

        # Reassign to new variable to avoid type checking errors of inner_decode
        # being None
        _inner_decode = inner_decode

        def _decode(attributes: Iterator[Any]) -> list[Any]:
            return [_inner_decode(attributes) for _ in range(array_length)]

        def _encode(l: list[Any], attributes: list[Any]) -> None:
            for item in l:
                inner_encode(item, attributes)

    return array_format, _decode, _encode


def _resolve_array_length(metadata: list[Any]) -> int:
    for data in metadata:
        if isinstance(data, Length):
            return data.length

    raise TypeError("Cannot find length annotation for list")


def _resolve_int_encoding(
    metadata: list[Any],
) -> tuple[str, Optional[Decoder[int]], Optional[Encoder[int]]]:
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


def _decode_uint(attributes: Iterator[Any]) -> int:
    return int.from_bytes(next(attributes), "little", signed=False)


def _encode_uint128(value: int, attributes: list[Any]) -> None:
    data = value.to_bytes(16, byteorder="little", signed=False)
    attributes.append(data)


def _encode_uint256(value: int, attributes: list[Any]) -> None:
    data = value.to_bytes(32, byteorder="little", signed=False)
    attributes.append(data)


def _decode_int(attributes: Iterator[Any]) -> int:
    return int.from_bytes(next(attributes), "little", signed=True)


def _encode_int128(value: int, attributes: list[Any]) -> None:
    data = value.to_bytes(16, byteorder="little", signed=True)
    attributes.append(data)


def _encode_int256(value: int, attributes: list[Any]) -> None:
    data = value.to_bytes(32, byteorder="little", signed=True)
    attributes.append(data)


def _resolve_int_enum_encoding(
    cls: Callable[[int], IntEnum], metadata: list[Any]
) -> tuple[str, Decoder[IntEnum], Optional[Encoder[IntEnum]]]:
    for data in metadata:
        if isinstance(data, UnsignedInteger):
            if data.size == 8:
                return "B", lambda a: cls(next(a)), None
            elif data.size == 16:
                return "H", lambda a: cls(next(a)), None
            elif data.size == 32:
                return "I", lambda a: cls(next(a)), None
            elif data.size == 64:
                return "Q", lambda a: cls(next(a)), None
            elif data.size == 128:

                def _decode_cls(attributes: Iterator[Any]) -> IntEnum:
                    return cls(_decode_uint(attributes))

                return "16s", _decode_cls, _encode_uint128
            elif data.size == 256:

                def _decode_cls(attributes: Iterator[Any]) -> IntEnum:
                    return cls(_decode_uint(attributes))

                return "32s", _decode_cls, _encode_uint256
            else:
                assert False

    raise TypeError("Cannot find integer type annotation")


def _resolve_str_encoding(
    metadata: list[Any],
) -> tuple[str, Decoder[str], Encoder[str]]:
    for data in metadata:
        if isinstance(data, Size):
            return (
                f"{data.size}s",
                _decode_str,
                _encode_str,
            )

    raise TypeError("Cannot find string type annotation")


def _decode_str(attributes: Iterator[Any]) -> str:
    value: bytes = next(attributes)
    return value.rstrip(b"\0").decode("utf-8")


def _encode_str(value: str, attributes: list[Any]) -> None:
    # The `struct` library automatically adds zeros to the end of
    # the encoded string to fill the necessary `data.size` bytes.
    data = value.encode("utf-8")
    attributes.append(data)


def _resolve_bytes_encoding(metadata: list[Any]) -> tuple[str, None, None]:
    for data in metadata:
        if isinstance(data, Size):
            return f"{data.size}s", None, None

    raise TypeError("Cannot find bytes type annotation")


def _resolve_decimal_encoding(
    metadata: list[Any],
) -> tuple[str, Decoder[Decimal], Encoder[Decimal]]:
    for data in metadata:
        if isinstance(data, _I80F48):
            return "16s", _decode_I80F48, _encode_I80F48

    raise TypeError("Cannot find decimal type annotation")


# The last 6 bytes (== 6 * 8 == 48 bits) of the 16 byte value is the fractional part.
# Therefore, divide by 2^48.
I80F48_DIVISOR = Decimal(2**48)


def _decode_I80F48(attributes: Iterator[Any]) -> Decimal:
    return int.from_bytes(next(attributes), "little", signed=True) / I80F48_DIVISOR


def _encode_I80F48(value: Decimal, attributes: list[Any]) -> None:
    data = int(value * I80F48_DIVISOR).to_bytes(16, "little", signed=True)
    attributes.append(data)


def _resolve_custom_encoding(
    cls: type[T],
) -> tuple[str, Decoder[T], Encoder[T]]:
    struct_data = _get_struct_data(cls)

    return struct_data.format, struct_data.decode, struct_data.encode

    # return f"{struct_data.size}s", struct_data.decode, struct_data.encode


def derive(*, byte_order: ByteOrder = "little") -> Callable[[type[T]], type[T]]:
    return lambda cls: _derive(cls, byte_order=byte_order)


def _derive(cls: type[T], byte_order: ByteOrder) -> type[T]:
    if not dataclasses.is_dataclass(cls):
        raise TypeError("Class must be a dataclass")

    fields = dataclasses.fields(cls)

    attribute_decoders: list[Optional[Decoder[Any]]] = []
    attribute_encoders: list[Optional[Encoder[Any]]] = []
    full_format = ""
    for field in fields:
        format, decoder, encoder = _resolve_parser(field.type)

        full_format += format
        attribute_decoders.append(decoder)
        attribute_encoders.append(encoder)

    attribute_names = [field.name for field in fields]

    def _decode(raw_attributes: Iterator[Any]) -> T:
        attributes = [
            decode_attribute(raw_attributes)
            if decode_attribute is not None
            else next(raw_attributes)
            for decode_attribute in attribute_decoders
        ]

        return cls(*attributes)

    def _encode(value: T, raw_attributes: list[Any]) -> None:
        for encode_attribute, name in zip(attribute_encoders, attribute_names):
            attribute = getattr(value, name)
            if encode_attribute is not None:
                encode_attribute(attribute, raw_attributes)
            else:
                raw_attributes.append(attribute)

    struct_data = _StructData(
        format=full_format,
        decode=_decode,
        encode=_encode,
    )
    _set_struct_data(cls, struct_data)

    return cls


def patch(
    cls: type[T], size: int, decode: BytesDecoder[T], encode: BytesEncoder[T]
) -> None:
    struct_data = _StructData.create_patched_data(size, decode, encode)
    _set_struct_data(cls, struct_data)


def decode(cls: type[T], data: bytes, strict: bool = True) -> T:
    struct_data = _get_struct_data(cls)

    if not strict:
        data = data[: struct_data.size]

    try:
        raw_attributes = struct_data.struct.unpack(data)
        return struct_data.decode(iter(raw_attributes))
    except StructError:
        # TODO: Handle
        raise


def decode_from(cls: type[T], data_stream: BytesIO) -> T:
    struct_data = _get_struct_data(cls)

    data = data_stream.read(struct_data.size)

    try:
        raw_attributes = struct_data.struct.unpack(data)
        return struct_data.decode(iter(raw_attributes))
    except StructError:
        # TODO: Handle
        raise


def encode(value: Any) -> bytes:
    cls = type(value)
    struct_data = _get_struct_data(cls)

    raw_attributes: list[Any] = []
    struct_data.encode(value, raw_attributes)

    return struct_data.struct.pack(*raw_attributes)


def get_size(cls: Any) -> int:
    struct_data = _get_struct_data(cls)
    return struct_data.size


def _get_struct_data(cls: type[T]) -> _StructData[T]:
    return getattr(cls, "__bstruct_data")


def _set_struct_data(cls: type[T], data: _StructData[T]) -> None:
    setattr(cls, "__bstruct_data", data)


def _has_struct_data(cls: Any) -> bool:
    return hasattr(cls, "__bstruct_data")
