from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum
from typing import Annotated

import pytest

import bstruct


def test_should_encode_bool_values() -> None:
    @dataclass
    class TestData:
        v1: bool
        v2: bool

    encoding = bstruct.derive(TestData)

    original = TestData(v1=True, v2=False)

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_unsigned_integers() -> None:
    @dataclass
    class TestData:
        u8: bstruct.u8
        u16: bstruct.u16
        u32: bstruct.u32
        u64: bstruct.u64
        u128: bstruct.u128
        u256: bstruct.u256

    encoding = bstruct.derive(TestData)

    original = TestData(u8=1, u16=2, u32=3, u64=4, u128=5, u256=6)

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_signed_integers() -> None:
    @dataclass
    class TestData:
        i8: bstruct.i8
        i16: bstruct.i16
        i32: bstruct.i32
        i64: bstruct.i64
        i128: bstruct.i128
        i256: bstruct.i256

    encoding = bstruct.derive(TestData)

    original = TestData(i8=-1, i16=-2, i32=-3, i64=-4, i128=-5, i256=-6)

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_int_enums() -> None:
    class TestEnum(IntEnum):
        A = 1
        B = 2

    @dataclass
    class TestData:
        a8: Annotated[TestEnum, bstruct.Encodings.u8]
        b8: Annotated[TestEnum, bstruct.Encodings.i8]
        a16: Annotated[TestEnum, bstruct.Encodings.u16]
        b16: Annotated[TestEnum, bstruct.Encodings.i16]
        a32: Annotated[TestEnum, bstruct.Encodings.u32]
        b32: Annotated[TestEnum, bstruct.Encodings.i32]
        a64: Annotated[TestEnum, bstruct.Encodings.u64]
        b64: Annotated[TestEnum, bstruct.Encodings.i64]
        a128: Annotated[TestEnum, bstruct.Encodings.u128]
        b128: Annotated[TestEnum, bstruct.Encodings.i128]
        a256: Annotated[TestEnum, bstruct.Encodings.u256]
        b256: Annotated[TestEnum, bstruct.Encodings.i256]

    encoding = bstruct.derive(TestData)

    original = TestData(
        a8=TestEnum.A,
        b8=TestEnum.B,
        a16=TestEnum.A,
        b16=TestEnum.B,
        a32=TestEnum.A,
        b32=TestEnum.B,
        a64=TestEnum.A,
        b64=TestEnum.B,
        a128=TestEnum.A,
        b128=TestEnum.B,
        a256=TestEnum.A,
        b256=TestEnum.B,
    )

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_strings() -> None:
    @dataclass
    class TestData:
        v1: Annotated[str, bstruct.String(size=11)]
        v2: Annotated[str, bstruct.String(size=20)]

    encoding = bstruct.derive(TestData)

    original = TestData(v1="hello world", v2="🎉")

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_bytes() -> None:
    @dataclass
    class TestData:
        v1: Annotated[bytes, bstruct.Bytes(size=11)]

    encoding = bstruct.derive(TestData)

    original = TestData(v1=b"hello world")

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_native_types() -> None:
    @dataclass
    class TestData:
        boolean: bool
        i32: int
        f64: float

    encoding = bstruct.derive(TestData)

    original = TestData(boolean=True, i32=-123456, f64=7654321.1234567)

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_nested_classes() -> None:
    @dataclass
    class InnerClass:
        value_1: bstruct.u32
        value_2: bstruct.u32

    @dataclass
    class OuterClass:
        inner_1: InnerClass
        inner_2: InnerClass

    encoding = bstruct.derive(OuterClass)

    original = OuterClass(
        inner_1=InnerClass(12, 34),
        inner_2=InnerClass(56, 78),
    )

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_I80F48() -> None:
    @dataclass
    class TestData:
        value: bstruct.I80F48

    encoding = bstruct.derive(TestData)

    original = TestData(Decimal("1234"))

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_float() -> None:
    @dataclass
    class TestData:
        f16: bstruct.f16
        f32: bstruct.f32
        f64: bstruct.f64

    encoding = bstruct.derive(TestData)

    original = TestData(0.15625, 1234.15625, 1234567.1234567)

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_encode_arrays() -> None:
    @dataclass
    class TestItem:
        a: bstruct.u8
        b: bstruct.u8

    @dataclass
    class TestData:
        native_values: Annotated[list[bstruct.u8], bstruct.Array(5)]
        custom_values: Annotated[list[TestItem], bstruct.Array(2)]

    encoding = bstruct.derive(TestData)

    original = TestData([1, 2, 3, 4, 5], custom_values=[TestItem(1, 2), TestItem(3, 4)])

    data = encoding.encode(original)
    decoded = encoding.decode(data)

    assert decoded == original


def test_should_unpack_multiple_instances() -> None:
    @dataclass
    class TestData:
        value: bstruct.u8

    encoding = bstruct.derive(TestData)

    original_1 = TestData(1)
    original_2 = TestData(2)
    original_3 = TestData(3)

    data = (
        encoding.encode(original_1)
        + encoding.encode(original_2)
        + encoding.encode(original_3)
    )

    decoded_1, decoded_2, decoded_3 = list(encoding.decode_all(data))

    assert decoded_1 == original_1
    assert decoded_2 == original_2
    assert decoded_3 == original_3


def test_should_correctly_handle_byte_order() -> None:
    @dataclass
    class Struct:
        small: bstruct.u16
        large: bstruct.u128

    encoding = bstruct.derive(Struct)

    value = Struct(small=0xFF00, large=0xFFFF_FFFF_FFFF_FFFF_0000_0000_0000_0000)

    data = encoding.encode(value, byteorder="little")
    assert encoding.decode(data, byteorder="little") == Struct(
        small=0xFF00,
        large=0xFFFF_FFFF_FFFF_FFFF_0000_0000_0000_0000,
    )
    assert encoding.decode(data, byteorder="big") == Struct(
        small=0x00FF,
        large=0x0000_0000_0000_0000_FFFF_FFFF_FFFF_FFFF,
    )

    data = encoding.encode(value, byteorder="big")
    assert encoding.decode(data, byteorder="little") == Struct(
        small=0x00FF,
        large=0x0000_0000_0000_0000_FFFF_FFFF_FFFF_FFFF,
    )
    assert encoding.decode(data, byteorder="big") == Struct(
        small=0xFF00,
        large=0xFFFF_FFFF_FFFF_FFFF_0000_0000_0000_0000,
    )


def test_should_fail_for_wrong_data_size() -> None:
    @dataclass
    class Struct:
        value: bstruct.u16

    encoding = bstruct.derive(Struct)

    data = b"\x00"

    with pytest.raises(bstruct.BstructError):
        encoding.decode(data)


def test_should_fail_for_missing_annotation() -> None:
    @dataclass
    class Struct:
        value: complex

    with pytest.raises(TypeError) as exc_info:
        bstruct.derive(Struct)

    assert str(exc_info.value) == "Missing annotation for type complex"


def test_should_fail_for_missing_encoding() -> None:
    @dataclass
    class Struct:
        value: Annotated[int, "some_annotation"]

    with pytest.raises(TypeError) as exc_info:
        bstruct.derive(Struct)

    assert str(exc_info.value) == "Cannot find encoding for type int"


def test_should_fail_for_wrong_encoding() -> None:
    @dataclass
    class Struct:
        value: Annotated[str, bstruct.Encodings.u8]

    with pytest.raises(TypeError) as exc_info:
        bstruct.derive(Struct)

    assert (
        str(exc_info.value)
        == "Wrong encoding: Expected Encoding[str], got Encoding[int]"
    )


def test_should_fail_for_missing_list_type() -> None:
    @dataclass
    class Struct:
        items: Annotated[list, bstruct.Array(3)]  # type: ignore

    with pytest.raises(TypeError) as exc_info:
        bstruct.derive(Struct)

    assert str(exc_info.value) == "list is missing inner type"


def test_should_fail_for_missing_array_length() -> None:
    @dataclass
    class Struct:
        items: Annotated[list[bstruct.u8], "some_annotation"]

    with pytest.raises(TypeError) as exc_info:
        bstruct.derive(Struct)

    assert str(exc_info.value) == "Cannot find length annotation for list"


def test_should_fail_for_missing_item() -> None:
    @dataclass
    class Struct:
        items: Annotated[list[bool], bstruct.Array(2)]

    StructEncoding = bstruct.derive(Struct)

    struct = Struct(items=[True])

    with pytest.raises(bstruct.BstructError):
        StructEncoding.encode(struct)


def test_should_fail_too_many_items() -> None:
    @dataclass
    class Struct:
        items: Annotated[list[bool], bstruct.Array(2)]

    StructEncoding = bstruct.derive(Struct)

    struct = Struct(items=[True, True, True])

    with pytest.raises(bstruct.BstructError):
        StructEncoding.encode(struct)
