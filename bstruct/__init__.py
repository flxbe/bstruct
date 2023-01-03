from __future__ import annotations
from io import BufferedIOBase
from typing import (
    Any,
    Sequence,
    NewType,
    Union,
    Generic,
    Iterator,
    TypeVar,
    Callable,
    Literal,
    Annotated,
    ClassVar,
    Iterable,
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
Attribute = Union[bool, bytes, int]
AttributeIterator = Iterator[Attribute]
AttributeList = list[Attribute]

Decoder = Callable[[AttributeIterator, ByteOrder], T]
Encoder = Callable[[T, AttributeList, ByteOrder], None]


def _raw_encode(value: Any, attributes: AttributeList, _byte_order: ByteOrder) -> None:
    attributes.append(value)


def _raw_decode(iterator: AttributeIterator, _byteorder: ByteOrder) -> Any:
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

    def get_struct(self, byteorder: ByteOrder) -> _Struct:
        if byteorder == "little":
            return self.le_struct
        else:
            return self.be_struct


class _NativeEncoding(Generic[T]):
    decode: Decoder[T]
    encode: Encoder[T]

    def __init__(self, target: type[T], format: str):
        self.target = target
        self.format = format
        self.decode = _raw_decode
        self.encode = _raw_encode


class _IntEncoding(_NativeEncoding[int]):
    def __init__(self, format: str):
        super().__init__(int, format)


class Bytes(_NativeEncoding[bytes]):
    def __init__(self, size: int):
        assert size > 0
        super().__init__(bytes, f"{size}s")


def compile_format(fields: Sequence[_NativeEncoding[Attribute]]) -> str:
    """
    Compile a list of attribute descriptions into a `struct.Struct` format string.
    This does not contain the byteorder specifier (e.g. `<` or `>`).
    """
    return "".join([field.format for field in fields])


class Array:
    """
    Special annotation class to specify the length of an array.
    """

    def __init__(self, length: int):
        assert length > 0

        self.length = length


class CustomEncoding(Generic[T]):
    def __init__(
        self,
        target: type[T],
        format: str,
        decode: Decoder[T],
        encode: Encoder[T],
    ):
        self.target = target
        self.format = format
        self.decode = decode
        self.encode = encode

    @staticmethod
    def create(
        target: type[T],
        fields: Sequence[_NativeEncoding[Any]],
        decode: Decoder[T],
        encode: Encoder[T],
    ) -> CustomEncoding[T]:
        return CustomEncoding(
            target,
            format=compile_format(fields),
            decode=decode,
            encode=encode,
        )


class String(CustomEncoding[str]):
    def __init__(self, size: int):
        super().__init__(
            target=str,
            format=Bytes(size).format,
            decode=_decode_str,
            encode=_encode_str,
        )


Encoding = Union[_NativeEncoding[T], CustomEncoding[T], _StructEncoding[T]]


def _decode_str(attributes: AttributeIterator, _byteorder: ByteOrder) -> str:
    value = next(attributes)
    assert isinstance(value, bytes)

    return value.rstrip(b"\0").decode("utf-8")


def _encode_str(value: str, attributes: AttributeList, _byteorder: ByteOrder) -> None:
    # The `struct` library automatically adds zeros to the end of
    # the encoded string to fill the necessary `data.size` bytes.
    data = value.encode("utf-8")
    attributes.append(data)


def _decode_uint(attributes: AttributeIterator, byteorder: ByteOrder) -> int:
    value = next(attributes)
    assert isinstance(value, bytes)

    return int.from_bytes(value, byteorder, signed=False)


def _encode_uint128(
    value: int, attributes: AttributeList, byteorder: ByteOrder
) -> None:
    data = value.to_bytes(16, byteorder, signed=False)
    attributes.append(data)


def _encode_uint256(
    value: int, attributes: AttributeList, byteorder: ByteOrder
) -> None:
    data = value.to_bytes(32, byteorder, signed=False)
    attributes.append(data)


def _decode_int(attributes: AttributeIterator, byteorder: ByteOrder) -> int:
    value = next(attributes)
    assert isinstance(value, bytes)

    return int.from_bytes(value, byteorder, signed=True)


def _encode_int128(value: int, attributes: AttributeList, byteorder: ByteOrder) -> None:
    data = value.to_bytes(16, byteorder, signed=True)
    attributes.append(data)


def _encode_int256(value: int, attributes: AttributeList, byteorder: ByteOrder) -> None:
    data = value.to_bytes(32, byteorder, signed=True)
    attributes.append(data)


# The last 6 bytes (== 6 * 8 == 48 bits) of the 16 byte value is the fractional part.
# Therefore, divide by 2^48.
I80F48_DIVISOR = Decimal(2**48)


def _decode_I80F48(attributes: AttributeIterator, byte_order: ByteOrder) -> Decimal:
    value = next(attributes)
    assert isinstance(value, bytes)

    return int.from_bytes(value, byte_order, signed=True) / I80F48_DIVISOR


def _encode_I80F48(
    value: Decimal, attributes: AttributeList, byte_order: ByteOrder
) -> None:
    data = int(value * I80F48_DIVISOR).to_bytes(16, byte_order, signed=True)
    attributes.append(data)


class Encodings:
    bool: _NativeEncoding[bool] = _NativeEncoding(bool, format="?")

    u8 = _IntEncoding("B")
    u16 = _IntEncoding(format="H")
    u32 = _IntEncoding(format="I")
    u64 = _IntEncoding(format="Q")
    u128 = CustomEncoding.create(
        int, fields=[Bytes(16)], decode=_decode_uint, encode=_encode_uint128
    )
    u256 = CustomEncoding.create(
        int, fields=[Bytes(32)], decode=_decode_uint, encode=_encode_uint256
    )

    i8 = _IntEncoding(format="b")
    i16 = _IntEncoding(format="h")
    i32 = _IntEncoding(format="i")
    i64 = _IntEncoding(format="q")
    i128 = CustomEncoding.create(
        int, fields=[Bytes(16)], decode=_decode_int, encode=_encode_int128
    )
    i256 = CustomEncoding.create(
        int, fields=[Bytes(32)], decode=_decode_int, encode=_encode_int256
    )

    I80F48 = CustomEncoding.create(
        Decimal,
        fields=[Bytes(16)],
        decode=_decode_I80F48,
        encode=_encode_I80F48,
    )


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


def _resolve_encoding(
    attribute_type: Any,
) -> Encoding[Any]:
    if isinstance(attribute_type, str):
        raise Exception(
            "Do not use 'from __future__ import annotations' in the same file in which 'binary.derive()' is used."
        )

    if attribute_type is bool:
        return Encodings.bool
    elif _has_struct_encoding(attribute_type):
        return _get_struct_encoding(attribute_type)
    elif typing.get_origin(attribute_type) is typing.Annotated:
        annotated_type, *annotation_args = typing.get_args(attribute_type)

        if inspect.isclass(annotated_type) and issubclass(annotated_type, IntEnum):
            return _resolve_int_enum_encoding(annotated_type, annotation_args)
        elif annotated_type is list:
            raise TypeError("Inner type for list needed.")
        elif typing.get_origin(annotated_type) is list:
            return _resolve_array_encoding(annotated_type, annotation_args)
        elif type(annotated_type) is NewType:
            return _resolve_unsafe_encoding(annotation_args)
        else:
            return _resolve_simple_encoding(annotated_type, annotation_args)

    assert False


def _encode_native_list(
    l: list[Attribute], attributes: AttributeList, _byteorder: ByteOrder
) -> None:
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

    return CustomEncoding(array_type, array_format, _decode, _encode)


def _resolve_array_length(metadata: list[Any]) -> int:
    for data in metadata:
        if isinstance(data, Array):
            return data.length

    raise TypeError("Cannot find length annotation for list")


I = TypeVar("I", bound=IntEnum)


def _resolve_int_enum_encoding(cls: type[I], metadata: list[Any]) -> CustomEncoding[I]:
    inner_encoding = _resolve_simple_encoding(int, metadata)

    return CustomEncoding(
        cls,
        format=inner_encoding.format,
        decode=lambda a, b: cls(inner_encoding.decode(a, b)),
        encode=inner_encoding.encode,
    )


def _resolve_simple_encoding(target: type[T], metadata: list[Any]) -> Encoding[T]:
    for data in metadata:
        if isinstance(data, (_NativeEncoding, CustomEncoding)):
            data: Encoding[Any] = data

            if data.target is not target:
                raise TypeError(
                    f"Wrong encoding: Expected Encoding[{data}], got `Encoding[{data.target}]`"
                )
            else:
                return data

    raise TypeError(f"Cannot find type annotation for type {target}")


def _resolve_unsafe_encoding(metadata: list[Any]) -> Encoding[Any]:
    for data in metadata:
        if isinstance(data, (_NativeEncoding, CustomEncoding)):
            data: Encoding[Any] = data
            return data

    raise TypeError("Cannot find encoding")


@dataclass_transform()
class Struct:
    """
    Inherit from this class to automatically derive the necessary
    decoding/encoding information.
    Also transforms any subclass into a Python dataclass.
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

    def _decode(raw_attributes: AttributeIterator, byteorder: ByteOrder) -> T:
        attributes = [
            decode_attribute(raw_attributes, byteorder)
            for decode_attribute in attribute_decoders
        ]

        return cls(*attributes)

    def _encode(value: T, raw_attributes: AttributeList, byteorder: ByteOrder) -> None:
        for encode_attribute, name in zip(attribute_encoders, attribute_names):
            attribute = getattr(value, name)
            encode_attribute(attribute, raw_attributes, byteorder)

    return _StructEncoding(
        format=full_format,
        decode=_decode,
        encode=_encode,
    )


S = TypeVar("S", bound=Struct)


def decode(cls: type[S], data: bytes, byteorder: ByteOrder = "little") -> S:
    """
    Decode an instance of `cls` from the provided data.
    The size of `data` must exactly match the size of `cls`.
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
    Decode multiple instances of `cls`.
    The size of `data` must be an integer multiple of the size of `S`.
    """
    encoding = cls.__bstruct_encoding__

    try:
        iterator = encoding.get_struct(byteorder).iter_unpack(data)

        for raw_attributes in iterator:
            yield encoding.decode(iter(raw_attributes), byteorder)
    except _StructError as error:
        raise BstructError(str(error)) from error


def read(cls: type[S], buffer: BufferedIOBase, byteorder: ByteOrder = "little") -> S:
    """
    Read and decode an instance of `cls` from the `buffer`.
    """
    data = buffer.read(cls.__bstruct_encoding__.size)
    return decode(cls, data, byteorder)


def read_many(
    cls: type[S],
    buffer: BufferedIOBase,
    count: int,
    byteorder: ByteOrder = "little",
) -> list[S]:
    """
    Read and decode `count` instances of `cls` from the `buffer`.
    """
    size = cls.__bstruct_encoding__.size
    data = buffer.read(size * count)

    return list(decode_all(cls, data, byteorder))


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


def write(
    value: Struct, buffer: BufferedIOBase, byteorder: ByteOrder = "little"
) -> None:
    """
    Encode and write `value` into the `buffer`.
    """
    data = encode(value, byteorder)
    buffer.write(data)


def write_many(
    items: Iterable[Struct], buffer: BufferedIOBase, byteorder: ByteOrder = "little"
) -> None:
    """
    Encode and write all `items` into the `buffer`.
    """
    for item in items:
        data = encode(item, byteorder)
        buffer.write(data)


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


def _has_struct_encoding(cls: Any) -> bool:
    return hasattr(cls, "__bstruct_encoding__")
