from __future__ import annotations
from io import BytesIO
from typing import (
    Any,
    NewType,
    Union,
    Generic,
    Iterator,
    TypeVar,
    Callable,
    Literal,
    Annotated,
)
import typing
from typing_extensions import dataclass_transform
import inspect
import dataclasses
from enum import IntEnum
from struct import Struct as _Struct, error as StructError
from decimal import Decimal


__version__ = "0.1.0"


T = TypeVar("T")

BytesDecoder = Callable[[bytes], T]
BytesEncoder = Callable[[T], bytes]

Decoder = Callable[[Iterator[Any]], T]
Encoder = Callable[[T, list[Any]], None]

ByteOrder = Literal["big", "little"]


def _raw_insert(value: Any, attributes: list[Any]) -> None:
    attributes.append(value)


class _StructEncoding(Generic[T]):
    def __init__(
        self,
        format: str,
        decode: Decoder[T],
        encode: Encoder[T],
    ):
        self.format = format
        self.struct = _Struct(f"<{format}")
        self.size = self.struct.size

        self.decode = decode
        self.encode = encode

    @staticmethod
    def create_patched_data(
        size: int, decode: BytesDecoder[T], encode: BytesEncoder[T]
    ) -> _StructEncoding[T]:
        return _StructEncoding(
            format=f"{size}s",
            decode=lambda iterator: decode(next(iterator)),
            encode=lambda t, l: l.append(encode(t)),
        )


class CustomEncoding(Generic[T]):
    def __init__(
        self,
        format: str,
        decode: Decoder[T],
        encode: Encoder[T],
    ):
        self.format = format
        self.decode = decode
        self.encode = encode


class _NativeEncoding(Generic[T]):
    def __init__(self, format: str):
        self.format = format
        self.decode = next
        self.encode = _raw_insert


class _IntEncoding(_NativeEncoding[int]):
    pass


Encoding = Union[_NativeEncoding[T], CustomEncoding[T], _StructEncoding[T]]


def _decode_str(attributes: Iterator[Any]) -> str:
    value: bytes = next(attributes)
    return value.rstrip(b"\0").decode("utf-8")


def _encode_str(value: str, attributes: list[Any]) -> None:
    # The `struct` library automatically adds zeros to the end of
    # the encoded string to fill the necessary `data.size` bytes.
    data = value.encode("utf-8")
    attributes.append(data)


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


# The last 6 bytes (== 6 * 8 == 48 bits) of the 16 byte value is the fractional part.
# Therefore, divide by 2^48.
I80F48_DIVISOR = Decimal(2**48)


def _decode_I80F48(attributes: Iterator[Any]) -> Decimal:
    return int.from_bytes(next(attributes), "little", signed=True) / I80F48_DIVISOR


def _encode_I80F48(value: Decimal, attributes: list[Any]) -> None:
    data = int(value * I80F48_DIVISOR).to_bytes(16, "little", signed=True)
    attributes.append(data)


class Encodings:
    bool: _NativeEncoding[bool] = _NativeEncoding(format="?")

    u8 = _IntEncoding(format="B")
    u16 = _IntEncoding(format="H")
    u32 = _IntEncoding(format="I")
    u64 = _IntEncoding(format="Q")
    u128: CustomEncoding[int] = CustomEncoding(
        format="16s", decode=_decode_uint, encode=_encode_uint128
    )
    u256: CustomEncoding[int] = CustomEncoding(
        format="32s", decode=_decode_uint, encode=_encode_uint256
    )

    i8 = _IntEncoding(format="b")
    i16 = _IntEncoding(format="h")
    i32 = _IntEncoding(format="i")
    i64 = _IntEncoding(format="q")
    i128: CustomEncoding[int] = CustomEncoding(
        format="16s", decode=_decode_int, encode=_encode_int128
    )
    i256: CustomEncoding[int] = CustomEncoding(
        format="32s", decode=_decode_int, encode=_encode_int256
    )

    I80F48: CustomEncoding[Decimal] = CustomEncoding(
        "16s", _decode_I80F48, _encode_I80F48
    )

    @staticmethod
    def bytes(size: int) -> _NativeEncoding[bytes]:
        assert size > 0
        return _NativeEncoding(format=f"{size}s")


u8 = Annotated[int, Encodings.u8]
u16 = Annotated[int, Encodings.u16]
u32 = Annotated[int, Encodings.u32]
u64 = Annotated[int, Encodings.u64]
u128 = Annotated[int, Encodings.u128]
u256 = Annotated[int, Encodings.u256]

i8 = Annotated[int, Encodings.i8]
i16 = Annotated[int, Encodings.i16]
i32 = Annotated[int, Encodings.i32]
i64 = Annotated[int, Encodings.i64]
i128 = Annotated[int, Encodings.i128]
i256 = Annotated[int, Encodings.i256]

I80F48 = Annotated[Decimal, Encodings.I80F48]


class Length:
    def __init__(self, length: int):
        assert length > 0

        self.length = length


class Size:
    def __init__(self, size: int):
        assert size > 0

        self.size = size


def _resolve_encoding(
    attribute_type: Any,
) -> Encoding[Any]:
    if isinstance(attribute_type, str):
        raise Exception(
            "Do not use 'from __future__ import annotations' in the same file in which 'binary.derive()' is used."
        )

    if attribute_type is bool:
        return Encodings.bool
    elif typing.get_origin(attribute_type) is typing.Annotated:
        annotated_type, *annotation_args = typing.get_args(attribute_type)

        if annotated_type is int:
            return _resolve_simple_encoding(annotation_args)
        elif inspect.isclass(annotated_type) and issubclass(annotated_type, IntEnum):
            return _resolve_int_enum_encoding(annotated_type, annotation_args)
        elif annotated_type is str:
            return _resolve_str_encoding(annotation_args)
        elif annotated_type is bytes:
            return _resolve_bytes_encoding(annotation_args)
        elif annotated_type is Decimal:
            return _resolve_simple_encoding(annotation_args)
        elif annotated_type is list:
            raise TypeError("Inner type for list needed.")
        elif typing.get_origin(annotated_type) is list:
            return _resolve_array_encoding(annotated_type, annotation_args)
        elif type(annotated_type) is NewType:
            return _resolve_simple_encoding(annotation_args)
    elif _has_struct_encoding(attribute_type):
        return _get_struct_encoding(attribute_type)

    assert False


def _encode_native_list(l: list[Any], attributes: list[Any]) -> None:
    attributes.extend(l)


def _resolve_array_encoding(
    array_type: Any, metadata: list[Any]
) -> CustomEncoding[list[Any]]:
    array_length = _resolve_array_length(metadata)

    array_type_args = typing.get_args(array_type)
    assert len(array_type_args) == 1
    inner_type = array_type_args[0]

    inner_encoding = _resolve_encoding(inner_type)
    array_format = "".join([inner_encoding.format] * array_length)

    inner_decode = inner_encoding.decode
    inner_encode = inner_encoding.encode

    def _decode(attributes: Iterator[Any]) -> list[Any]:
        return [inner_decode(attributes) for _ in range(array_length)]

    # Optimization: If the encoding function of the element is just inserting the raw element,
    # use a batch insert to speed things up.
    if inner_encode == _raw_insert:
        _encode = _encode_native_list
    else:

        def _encode(l: list[Any], attributes: list[Any]) -> None:
            for item in l:
                inner_encode(item, attributes)

    return CustomEncoding(array_format, _decode, _encode)


def _resolve_array_length(metadata: list[Any]) -> int:
    for data in metadata:
        if isinstance(data, Length):
            return data.length

    raise TypeError("Cannot find length annotation for list")


def _resolve_int_enum_encoding(
    cls: Callable[[int], IntEnum], metadata: list[Any]
) -> CustomEncoding[IntEnum]:
    inner_encoding: Encoding[int] = _resolve_simple_encoding(metadata)

    return CustomEncoding(
        format=inner_encoding.format,
        decode=lambda a: cls(inner_encoding.decode(a)),
        encode=inner_encoding.encode,
    )


def _resolve_simple_encoding(metadata: list[Any]) -> Encoding[Any]:
    for data in metadata:
        if isinstance(data, (_IntEncoding, CustomEncoding)):
            data: Encoding[Any] = data
            return data

    raise TypeError("Cannot find integer type annotation")


def _resolve_str_encoding(metadata: list[Any]) -> CustomEncoding[str]:
    for data in metadata:
        if isinstance(data, Size):
            return CustomEncoding(
                format=f"{data.size}s",
                decode=_decode_str,
                encode=_encode_str,
            )

    raise TypeError("Cannot find string type annotation")


def _resolve_bytes_encoding(metadata: list[Any]) -> _NativeEncoding[bytes]:
    for data in metadata:
        if isinstance(data, Size):
            return _NativeEncoding(format=f"{data.size}s")

    raise TypeError("Cannot find bytes type annotation")


@dataclass_transform()
class Struct:
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        assert not dataclasses.is_dataclass(cls)
        dataclasses.dataclass(cls)

        _derive(cls, byte_order="little")


def _derive(cls: type[T], byte_order: ByteOrder) -> _StructEncoding[T]:
    fields = dataclasses.fields(cls)

    attribute_decoders: list[Decoder[Any]] = []
    attribute_encoders: list[Encoder[Any]] = []
    full_format: str = ""
    for field in fields:
        encoding = _resolve_encoding(field.type)

        full_format += encoding.format
        attribute_decoders.append(encoding.decode)
        attribute_encoders.append(encoding.encode)

    attribute_names = [field.name for field in fields]

    def _decode(raw_attributes: Iterator[Any]) -> T:
        attributes = [
            decode_attribute(raw_attributes) for decode_attribute in attribute_decoders
        ]

        return cls(*attributes)

    def _encode(value: T, raw_attributes: list[Any]) -> None:
        for encode_attribute, name in zip(attribute_encoders, attribute_names):
            attribute = getattr(value, name)
            encode_attribute(attribute, raw_attributes)

    encoding = _StructEncoding(
        format=full_format,
        decode=_decode,
        encode=_encode,
    )
    _set_struct_encoding(cls, encoding)

    return encoding


def compile_format(fields: list[_NativeEncoding[Any]]) -> str:
    return "".join([field.format for field in fields])


def patch(
    cls: type[T], size: int, decode: BytesDecoder[T], encode: BytesEncoder[T]
) -> None:
    encoding = _StructEncoding.create_patched_data(size, decode, encode)
    _set_struct_encoding(cls, encoding)


S = TypeVar("S", bound=Struct)


def decode(cls: type[S], data: bytes, strict: bool = True) -> S:
    encoding = _get_struct_encoding(cls)

    if not strict:
        data = data[: encoding.size]

    try:
        raw_attributes = encoding.struct.unpack(data)
        return encoding.decode(iter(raw_attributes))
    except StructError:
        # TODO: Handle
        raise


def decode_all(cls: type[S], data: bytes) -> Iterator[S]:
    encoding = _get_struct_encoding(cls)

    try:
        iterator = encoding.struct.iter_unpack(data)

        for raw_attributes in iterator:
            yield encoding.decode(iter(raw_attributes))
    except StructError:
        # TODO: Handle
        raise


def decode_from(cls: type[S], data_stream: BytesIO) -> S:
    encoding = _get_struct_encoding(cls)

    data = data_stream.read(encoding.size)

    try:
        raw_attributes = encoding.struct.unpack(data)
        return encoding.decode(iter(raw_attributes))
    except StructError:
        # TODO: Handle
        raise


def encode(value: Struct) -> bytes:
    encoding = _get_struct_encoding(type(value))

    raw_attributes: list[Any] = []
    encoding.encode(value, raw_attributes)

    return encoding.struct.pack(*raw_attributes)


def get_struct(cls: type[Struct]) -> _Struct:
    encoding = _get_struct_encoding(cls)
    return encoding.struct


def get_size(cls: type[Struct]) -> int:
    encoding = _get_struct_encoding(cls)
    return encoding.size


def _get_struct_encoding(cls: type[S]) -> _StructEncoding[S]:
    return getattr(cls, "__bstruct_encoding")


def _set_struct_encoding(cls: type[T], data: _StructEncoding[T]) -> None:
    setattr(cls, "__bstruct_encoding", data)


def _has_struct_encoding(cls: Any) -> bool:
    return hasattr(cls, "__bstruct_encoding")
