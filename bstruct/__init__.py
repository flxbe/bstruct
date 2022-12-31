from __future__ import annotations
from io import BufferedIOBase
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
    ClassVar,
)
import typing
from typing_extensions import dataclass_transform
import inspect
import dataclasses
from enum import IntEnum
from struct import Struct as _Struct, error as _StructError
from decimal import Decimal


__version__ = "0.4.0"


class BstructError(Exception):
    pass


T = TypeVar("T")

ByteOrder = Literal["big", "little"]
BytesDecoder = Callable[[bytes, ByteOrder], T]
BytesEncoder = Callable[[T, ByteOrder], bytes]

Decoder = Callable[[Iterator[Any], ByteOrder], T]
Encoder = Callable[[T, list[Any], ByteOrder], None]


def _raw_encode(value: Any, attributes: list[Any], _byte_order: ByteOrder) -> None:
    attributes.append(value)


def _raw_decode(iterator: Iterator[Any], _byteorder: ByteOrder) -> Any:
    return next(iterator)


class _StructEncoding(Generic[T]):
    def __init__(
        self,
        format: str,
        decode: Decoder[T],
        encode: Encoder[T],
    ):
        self.format = format
        self.le_struct = _Struct(f"<{format}")
        self.be_struct = _Struct(f">{format}")
        self.size = self.le_struct.size

        self.decode = decode
        self.encode = encode

    @staticmethod
    def create_patched_data(
        size: int, decode: BytesDecoder[T], encode: BytesEncoder[T]
    ) -> _StructEncoding[T]:
        return _StructEncoding(
            format=f"{size}s",
            decode=lambda iterator, byte_order: decode(next(iterator), byte_order),
            encode=lambda t, l, b: l.append(encode(t, b)),
        )

    def get_struct(self, byteorder: ByteOrder) -> _Struct:
        if byteorder == "little":
            return self.le_struct
        else:
            return self.be_struct


class _CustomEncoding(Generic[T]):
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
    decode: Decoder[T]
    encode: Encoder[T]

    def __init__(self, format: str):
        self.format = format
        self.decode = _raw_decode
        self.encode = _raw_encode


class _IntEncoding(_NativeEncoding[int]):
    pass


Encoding = Union[_NativeEncoding[T], _CustomEncoding[T], _StructEncoding[T]]


def _decode_str(attributes: Iterator[Any], _byteorder: ByteOrder) -> str:
    value: bytes = next(attributes)
    return value.rstrip(b"\0").decode("utf-8")


def _encode_str(value: str, attributes: list[Any], _byteorder: ByteOrder) -> None:
    # The `struct` library automatically adds zeros to the end of
    # the encoded string to fill the necessary `data.size` bytes.
    data = value.encode("utf-8")
    attributes.append(data)


def _decode_uint(attributes: Iterator[Any], byteorder: ByteOrder) -> int:
    return int.from_bytes(next(attributes), byteorder, signed=False)


def _encode_uint128(value: int, attributes: list[Any], byteorder: ByteOrder) -> None:
    data = value.to_bytes(16, byteorder, signed=False)
    attributes.append(data)


def _encode_uint256(value: int, attributes: list[Any], byteorder: ByteOrder) -> None:
    data = value.to_bytes(32, byteorder, signed=False)
    attributes.append(data)


def _decode_int(attributes: Iterator[Any], byteorder: ByteOrder) -> int:
    return int.from_bytes(next(attributes), byteorder, signed=True)


def _encode_int128(value: int, attributes: list[Any], byteorder: ByteOrder) -> None:
    data = value.to_bytes(16, byteorder, signed=True)
    attributes.append(data)


def _encode_int256(value: int, attributes: list[Any], byteorder: ByteOrder) -> None:
    data = value.to_bytes(32, byteorder, signed=True)
    attributes.append(data)


# The last 6 bytes (== 6 * 8 == 48 bits) of the 16 byte value is the fractional part.
# Therefore, divide by 2^48.
I80F48_DIVISOR = Decimal(2**48)


def _decode_I80F48(attributes: Iterator[Any], byte_order: ByteOrder) -> Decimal:
    return int.from_bytes(next(attributes), byte_order, signed=True) / I80F48_DIVISOR


def _encode_I80F48(
    value: Decimal, attributes: list[Any], byte_order: ByteOrder
) -> None:
    data = int(value * I80F48_DIVISOR).to_bytes(16, byte_order, signed=True)
    attributes.append(data)


class Encodings:
    bool: _NativeEncoding[bool] = _NativeEncoding(format="?")

    u8 = _IntEncoding(format="B")
    u16 = _IntEncoding(format="H")
    u32 = _IntEncoding(format="I")
    u64 = _IntEncoding(format="Q")
    u128: _CustomEncoding[int] = _CustomEncoding(
        format="16s", decode=_decode_uint, encode=_encode_uint128
    )
    u256: _CustomEncoding[int] = _CustomEncoding(
        format="32s", decode=_decode_uint, encode=_encode_uint256
    )

    i8 = _IntEncoding(format="b")
    i16 = _IntEncoding(format="h")
    i32 = _IntEncoding(format="i")
    i64 = _IntEncoding(format="q")
    i128: _CustomEncoding[int] = _CustomEncoding(
        format="16s", decode=_decode_int, encode=_encode_int128
    )
    i256: _CustomEncoding[int] = _CustomEncoding(
        format="32s", decode=_decode_int, encode=_encode_int256
    )

    I80F48: _CustomEncoding[Decimal] = _CustomEncoding(
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


def _encode_native_list(
    l: list[Any], attributes: list[Any], _byteorder: ByteOrder
) -> None:
    attributes.extend(l)


def _resolve_array_encoding(
    array_type: Any, metadata: list[Any]
) -> _CustomEncoding[list[Any]]:
    array_length = _resolve_array_length(metadata)

    array_type_args = typing.get_args(array_type)
    assert len(array_type_args) == 1
    inner_type = array_type_args[0]

    inner_encoding = _resolve_encoding(inner_type)
    array_format = "".join([inner_encoding.format] * array_length)

    inner_decode = inner_encoding.decode
    inner_encode = inner_encoding.encode

    def _decode(attributes: Iterator[Any], byte_order: ByteOrder) -> list[Any]:
        return [inner_decode(attributes, byte_order) for _ in range(array_length)]

    # Optimization: If the encoding function of the element is just inserting the raw element,
    # use a batch insert to speed things up.
    if inner_encode == _raw_encode:
        _encode = _encode_native_list
    else:

        def _encode(l: list[Any], attributes: list[Any], byte_order: ByteOrder) -> None:
            for item in l:
                inner_encode(item, attributes, byte_order)

    return _CustomEncoding(array_format, _decode, _encode)


def _resolve_array_length(metadata: list[Any]) -> int:
    for data in metadata:
        if isinstance(data, Length):
            return data.length

    raise TypeError("Cannot find length annotation for list")


def _resolve_int_enum_encoding(
    cls: Callable[[int], IntEnum], metadata: list[Any]
) -> _CustomEncoding[IntEnum]:
    inner_encoding: Encoding[int] = _resolve_simple_encoding(metadata)

    return _CustomEncoding(
        format=inner_encoding.format,
        decode=lambda a, b: cls(inner_encoding.decode(a, b)),
        encode=inner_encoding.encode,
    )


def _resolve_simple_encoding(metadata: list[Any]) -> Encoding[Any]:
    for data in metadata:
        if isinstance(data, (_IntEncoding, _CustomEncoding)):
            data: Encoding[Any] = data
            return data

    raise TypeError("Cannot find integer type annotation")


def _resolve_str_encoding(metadata: list[Any]) -> _CustomEncoding[str]:
    for data in metadata:
        if isinstance(data, Size):
            return _CustomEncoding(
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
    """
    Inherit from this class to automatically derive the necessary
    decoding/encoding information.
    Also transforms any subclasses into a Python dataclass.
    """

    __bstruct_encoding__: ClassVar[_StructEncoding[Any]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        assert not dataclasses.is_dataclass(cls)
        dataclasses.dataclass(cls)

        cls.__bstruct_encoding__ = _derive(cls)


def _derive(cls: type[T]) -> _StructEncoding[T]:
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

    def _decode(raw_attributes: Iterator[Any], byteorder: ByteOrder) -> T:
        attributes = [
            decode_attribute(raw_attributes, byteorder)
            for decode_attribute in attribute_decoders
        ]

        return cls(*attributes)

    def _encode(value: T, raw_attributes: list[Any], byteorder: ByteOrder) -> None:
        for encode_attribute, name in zip(attribute_encoders, attribute_names):
            attribute = getattr(value, name)
            encode_attribute(attribute, raw_attributes, byteorder)

    return _StructEncoding(
        format=full_format,
        decode=_decode,
        encode=_encode,
    )


def compile_format(fields: list[_NativeEncoding[Any]]) -> str:
    """
    Compile a list of attribute descriptions into a `struct.Struct` format string.
    This does not contain the byteorder specifier (e.g. `<` or `>`).
    """
    return "".join([field.format for field in fields])


def patch(
    cls: type[T], size: int, decode: BytesDecoder[T], encode: BytesEncoder[T]
) -> None:
    """
    Patch an existing class.
    The size must be the expected size in bytes of the serialized form of `T`.
    """
    encoding = _StructEncoding.create_patched_data(size, decode, encode)
    _set_struct_encoding(cls, encoding)


S = TypeVar("S", bound=Struct)


def decode(cls: type[S], data: bytes, byteorder: ByteOrder = "little") -> S:
    """
    Decode an instance of `S` from the provided data.
    The size of `data` must exactly match the size of `S`.
    """
    encoding = cls.__bstruct_encoding__

    try:
        raw_attributes = encoding.get_struct(byteorder).unpack(data)
        return encoding.decode(iter(raw_attributes), byteorder)
    except _StructError as error:
        raise BstructError(str(error)) from error


def decode_all(
    cls: type[S], data: bytes, byteorder: ByteOrder = "little"
) -> Iterator[S]:
    """
    Decode multiple instances of `S`.
    The size of `data` must be an integer multiple of the size of `S`.
    """
    encoding = cls.__bstruct_encoding__

    try:
        iterator = encoding.get_struct(byteorder).iter_unpack(data)

        for raw_attributes in iterator:
            yield encoding.decode(iter(raw_attributes), byteorder)
    except _StructError as error:
        raise BstructError(str(error)) from error


def decode_from(
    cls: type[S], data_stream: BufferedIOBase, byteorder: ByteOrder = "little"
) -> S:
    """
    Read and decode an instance of `S` from the data stream.
    """
    encoding = cls.__bstruct_encoding__

    data = data_stream.read(encoding.size)

    try:
        raw_attributes = encoding.get_struct(byteorder).unpack(data)
        return encoding.decode(iter(raw_attributes), byteorder)
    except _StructError as error:
        raise BstructError(str(error)) from error


def encode(value: Struct, byteorder: ByteOrder = "little") -> bytes:
    """
    Encode the value according to the provided byteorder.
    """
    encoding = value.__bstruct_encoding__

    raw_attributes: list[Any] = []
    encoding.encode(value, raw_attributes, byteorder)

    try:
        return encoding.get_struct(byteorder).pack(*raw_attributes)
    except _StructError as error:
        raise BstructError(str(error)) from error


def get_struct(cls: type[Struct], byteorder: ByteOrder = "little") -> _Struct:
    """
    Return the underlying `struct.Struct` instance used to (un)pack
    the binary data.
    """
    return cls.__bstruct_encoding__.get_struct(byteorder)


def get_size(cls: type[Struct]) -> int:
    """
    Return the size in bytes of the serialized form of a `bstruct.Struct` class.
    """
    return cls.__bstruct_encoding__.size


def _get_struct_encoding(cls: type[S]) -> _StructEncoding[S]:
    return getattr(cls, "__bstruct_encoding__")


def _set_struct_encoding(cls: type[T], data: _StructEncoding[T]) -> None:
    setattr(cls, "__bstruct_encoding__", data)


def _has_struct_encoding(cls: Any) -> bool:
    return hasattr(cls, "__bstruct_encoding__")
