from __future__ import annotations

import dataclasses
import inspect
import typing
from decimal import Decimal
from enum import IntEnum
from io import BufferedIOBase
from struct import Struct as _Struct
from struct import error as _StructError
from typing import (
    Annotated,
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Literal,
    TypeVar,
    Union,
)


__version__ = "0.5.0"


class BstructError(Exception):
    pass


ByteOrder = Literal["big", "little"]

NativeValue = Union[bool, bytes, int]
ValueIterator = Iterator[NativeValue]
ValueList = list[NativeValue]

T = TypeVar("T")
Decoder = Callable[[ValueIterator, ByteOrder], T]
Encoder = Callable[[T, ValueList, ByteOrder], None]


def _raw_encode(value: Any, attributes: ValueList, _byte_order: ByteOrder) -> None:
    attributes.append(value)


def _raw_decode(attributes: ValueIterator, _byteorder: ByteOrder) -> Any:
    return next(attributes)


class Encoding(Generic[T]):
    def __init__(
        self,
        target: type[T],
        format: str,
        decode_attributes: Decoder[T],
        encode_attributes: Encoder[T],
    ):
        self.target = target
        self.format = format
        self.decode_attributes = decode_attributes
        self.encode_attributes = encode_attributes

        self.le_struct = _Struct(f"<{format}")
        self.be_struct = _Struct(f">{format}")
        self.size = self.le_struct.size

    def get_struct(self, byteorder: ByteOrder) -> _Struct:
        """
        Return the underlying `struct.Struct` instance used to (un)pack
        the binary data.
        """
        if byteorder == "little":
            return self.le_struct
        else:
            return self.be_struct

    def decode(self, data: bytes, byteorder: ByteOrder = "little") -> T:
        """
        Decode an instance of `cls` from the provided data.
        The size of `data` must exactly match the size of `cls`.
        """
        try:
            raw_attributes = self.get_struct(byteorder).unpack(data)
            return self.decode_attributes(iter(raw_attributes), byteorder)
        except _StructError as error:
            raise BstructError(str(error)) from error

    def decode_all(self, data: bytes, byteorder: ByteOrder = "little") -> Iterator[T]:
        """
        Decode multiple instances of `cls`.
        The size of `data` must be an integer multiple of the size of `S`.
        """
        try:
            iterator = self.get_struct(byteorder).iter_unpack(data)

            for raw_attributes in iterator:
                yield self.decode_attributes(iter(raw_attributes), byteorder)
        except _StructError as error:
            raise BstructError(str(error)) from error

    def read(self, buffer: BufferedIOBase, byteorder: ByteOrder = "little") -> T:
        """
        Read and decode an instance of `cls` from the `buffer`.
        """
        data = buffer.read(self.size)
        return self.decode(data, byteorder)

    def read_many(
        self,
        buffer: BufferedIOBase,
        count: int,
        byteorder: ByteOrder = "little",
    ) -> list[T]:
        """
        Read and decode `count` instances of `cls` from the `buffer`.
        """
        data = buffer.read(self.size * count)

        return list(self.decode_all(data, byteorder))

    def encode(self, value: T, byteorder: ByteOrder = "little") -> bytes:
        """
        Encode the value according to the provided byteorder.
        """

        raw_attributes: list[Any] = []
        self.encode_attributes(value, raw_attributes, byteorder)

        try:
            return self.get_struct(byteorder).pack(*raw_attributes)
        except _StructError as error:
            raise BstructError(str(error)) from error

    def write(
        self, value: T, buffer: BufferedIOBase, byteorder: ByteOrder = "little"
    ) -> None:
        """
        Encode and write `value` into the `buffer`.
        """
        data = self.encode(value, byteorder)
        buffer.write(data)

    def write_many(
        self,
        items: Iterable[T],
        buffer: BufferedIOBase,
        byteorder: ByteOrder = "little",
    ) -> None:
        """
        Encode and write all `items` into the `buffer`.
        """
        for item in items:
            data = self.encode(item, byteorder)
            buffer.write(data)

    def get_size(self) -> int:
        """
        Return the size in bytes of the serialized form of a `bstruct.Struct` class.
        """
        return self.size


class _NativeEncoding(Encoding[T]):
    def __init__(self, target: type[T], format: str):
        super().__init__(
            target, format, decode_attributes=_raw_decode, encode_attributes=_raw_encode
        )


class Bytes(_NativeEncoding[bytes]):
    def __init__(self, size: int):
        assert size > 0
        super().__init__(bytes, f"{size}s")


def compile_format(fields: Iterable[_NativeEncoding[Any]]) -> str:
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


class CustomEncoding(Encoding[T]):
    def __init__(
        self,
        target: type[T],
        format: str,
        decode_attributes: Decoder[T],
        encode_attributes: Encoder[T],
    ):
        super().__init__(
            target,
            format,
            decode_attributes=decode_attributes,
            encode_attributes=encode_attributes,
        )

    @staticmethod
    def create(
        target: type[T],
        fields: Iterable[_NativeEncoding[Any]],
        decode_attributes: Decoder[T],
        encode_attributes: Encoder[T],
    ) -> CustomEncoding[T]:
        return CustomEncoding(
            target,
            format=compile_format(fields),
            decode_attributes=decode_attributes,
            encode_attributes=encode_attributes,
        )


class String(CustomEncoding[str]):
    def __init__(self, size: int):
        super().__init__(
            target=str,
            format=Bytes(size).format,
            decode_attributes=_decode_str,
            encode_attributes=_encode_str,
        )


def _decode_str(attributes: ValueIterator, _byteorder: ByteOrder) -> str:
    value = next(attributes)
    assert isinstance(value, bytes)

    return value.rstrip(b"\0").decode("utf-8")


def _encode_str(value: str, attributes: ValueList, _byteorder: ByteOrder) -> None:
    # The `struct` library automatically adds zeros to the end of
    # the encoded string to fill the necessary `data.size` bytes.
    data = value.encode("utf-8")
    attributes.append(data)


def _decode_uint(attributes: ValueIterator, byteorder: ByteOrder) -> int:
    value = next(attributes)
    assert isinstance(value, bytes)

    return int.from_bytes(value, byteorder, signed=False)


def _encode_uint128(value: int, attributes: ValueList, byteorder: ByteOrder) -> None:
    data = value.to_bytes(16, byteorder, signed=False)
    attributes.append(data)


def _encode_uint256(value: int, attributes: ValueList, byteorder: ByteOrder) -> None:
    data = value.to_bytes(32, byteorder, signed=False)
    attributes.append(data)


def _decode_int(attributes: ValueIterator, byteorder: ByteOrder) -> int:
    value = next(attributes)
    assert isinstance(value, bytes)

    return int.from_bytes(value, byteorder, signed=True)


def _encode_int128(value: int, attributes: ValueList, byteorder: ByteOrder) -> None:
    data = value.to_bytes(16, byteorder, signed=True)
    attributes.append(data)


def _encode_int256(value: int, attributes: ValueList, byteorder: ByteOrder) -> None:
    data = value.to_bytes(32, byteorder, signed=True)
    attributes.append(data)


# The last 6 bytes (== 6 * 8 == 48 bits) of the 16 byte value is the fractional part.
# Therefore, divide by 2^48.
I80F48_DIVISOR = Decimal(2**48)


def _decode_I80F48(attributes: ValueIterator, byte_order: ByteOrder) -> Decimal:
    value = next(attributes)
    assert isinstance(value, bytes)

    return int.from_bytes(value, byte_order, signed=True) / I80F48_DIVISOR


def _encode_I80F48(
    value: Decimal, attributes: ValueList, byte_order: ByteOrder
) -> None:
    data = int(value * I80F48_DIVISOR).to_bytes(16, byte_order, signed=True)
    attributes.append(data)


class Encodings:
    bool: _NativeEncoding[bool] = _NativeEncoding(bool, format="?")

    u8 = _NativeEncoding(int, "B")
    u16 = _NativeEncoding(int, format="H")
    u32 = _NativeEncoding(int, format="I")
    u64 = _NativeEncoding(int, format="Q")
    u128 = CustomEncoding.create(
        int,
        fields=[Bytes(16)],
        decode_attributes=_decode_uint,
        encode_attributes=_encode_uint128,
    )
    u256 = CustomEncoding.create(
        int,
        fields=[Bytes(32)],
        decode_attributes=_decode_uint,
        encode_attributes=_encode_uint256,
    )

    i8 = _NativeEncoding(int, format="b")
    i16 = _NativeEncoding(int, format="h")
    i32 = _NativeEncoding(int, format="i")
    i64 = _NativeEncoding(int, format="q")
    i128 = CustomEncoding.create(
        int,
        fields=[Bytes(16)],
        decode_attributes=_decode_int,
        encode_attributes=_encode_int128,
    )
    i256 = CustomEncoding.create(
        int,
        fields=[Bytes(32)],
        decode_attributes=_decode_int,
        encode_attributes=_encode_int256,
    )

    I80F48 = CustomEncoding.create(
        Decimal,
        fields=[Bytes(16)],
        decode_attributes=_decode_I80F48,
        encode_attributes=_encode_I80F48,
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


def derive(attribute_type: type[T]) -> Encoding[T]:
    return _derive(attribute_type)


def _derive(
    attribute_type: Any,
) -> Encoding[Any]:
    if isinstance(attribute_type, str):
        raise Exception(
            "Do not use 'from __future__ import annotations' in the same file in which 'binary.derive()' is used."
        )

    if attribute_type is bool:
        return Encodings.bool
    elif inspect.isclass(attribute_type) and dataclasses.is_dataclass(attribute_type):
        return _resolve_dataclass_encoding(attribute_type)
    elif typing.get_origin(attribute_type) is typing.Annotated:
        annotated_type, *annotation_args = typing.get_args(attribute_type)

        if inspect.isclass(annotated_type) and issubclass(annotated_type, IntEnum):
            return _resolve_int_enum_encoding(annotated_type, annotation_args)
        elif annotated_type is list:
            raise TypeError("list is missing inner type")
        elif typing.get_origin(annotated_type) is list:
            return _resolve_array_encoding(annotated_type, annotation_args)
        else:
            return _resolve_simple_encoding(annotated_type, annotation_args)
    else:
        raise TypeError(f"Missing annotation for type {attribute_type.__name__}")


def _encode_native_list(
    l: list[NativeValue], attributes: ValueList, _byteorder: ByteOrder
) -> None:
    attributes.extend(l)


def _resolve_array_encoding(
    array_type: Any, metadata: list[Any]
) -> CustomEncoding[list[Any]]:
    array_length = _resolve_array_length(metadata)

    array_type_args = typing.get_args(array_type)
    assert len(array_type_args) == 1
    inner_type = array_type_args[0]

    inner_encoding = derive(inner_type)
    array_format = "".join([inner_encoding.format] * array_length)

    inner_decode = inner_encoding.decode_attributes
    inner_encode = inner_encoding.encode_attributes

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
        decode_attributes=lambda a, b: cls(inner_encoding.decode_attributes(a, b)),
        encode_attributes=inner_encoding.encode_attributes,
    )


def _resolve_simple_encoding(target: type[T], metadata: list[Any]) -> Encoding[T]:
    for data in metadata:
        if isinstance(data, (_NativeEncoding, CustomEncoding)):
            data: Encoding[Any] = data

            if data.target is not target:
                raise TypeError(
                    f"Wrong encoding: Expected Encoding[{target.__name__}], got Encoding[{data.target.__name__}]"
                )
            else:
                return data

    raise TypeError(f"Cannot find encoding for type {target.__name__}")


def _resolve_dataclass_encoding(cls: type[T]) -> CustomEncoding[T]:
    fields = dataclasses.fields(cls)

    attribute_decoders: list[Decoder[Any]] = []
    attribute_encoders: list[Encoder[Any]] = []
    full_format: str = ""
    for field in fields:
        encoding = derive(field.type)

        full_format += encoding.format
        attribute_decoders.append(encoding.decode_attributes)
        attribute_encoders.append(encoding.encode_attributes)

    attribute_names = [field.name for field in fields]

    def _decode(raw_attributes: ValueIterator, byteorder: ByteOrder) -> T:
        attributes = [
            decode_attribute(raw_attributes, byteorder)
            for decode_attribute in attribute_decoders
        ]

        return cls(*attributes)

    def _encode(value: T, raw_attributes: ValueList, byteorder: ByteOrder) -> None:
        for encode_attribute, name in zip(attribute_encoders, attribute_names):
            attribute = getattr(value, name)
            encode_attribute(attribute, raw_attributes, byteorder)

    return CustomEncoding(
        cls,
        format=full_format,
        decode_attributes=_decode,
        encode_attributes=_encode,
    )
