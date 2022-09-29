from typing import Annotated
from dataclasses import dataclass
from enum import IntEnum
from decimal import Decimal

import bstruct


def test_should_encode_bool_values() -> None:
    @bstruct.derive()
    @dataclass
    class TestData:
        v1: bool
        v2: bool

    original = TestData(v1=True, v2=False)

    data = bstruct.encode(original)
    decoded = bstruct.decode(TestData, data)

    assert decoded == original


def test_should_encode_unsigned_integers() -> None:
    @bstruct.derive()
    @dataclass
    class TestData:
        u8: bstruct.u8
        u16: bstruct.u16
        u32: bstruct.u32
        u64: bstruct.u64
        u128: bstruct.u128
        u256: bstruct.u256

    original = TestData(u8=1, u16=2, u32=3, u64=4, u128=5, u256=6)

    data = bstruct.encode(original)
    decoded = bstruct.decode(TestData, data)

    assert decoded == original


def test_should_encode_signed_integers() -> None:
    @bstruct.derive()
    @dataclass
    class TestData:
        i8: bstruct.i8
        i16: bstruct.i16
        i32: bstruct.i32
        i64: bstruct.i64
        i128: bstruct.i128
        i256: bstruct.i256

    original = TestData(i8=-1, i16=-2, i32=-3, i64=-4, i128=-5, i256=-6)

    data = bstruct.encode(original)
    decoded = bstruct.decode(TestData, data)

    assert decoded == original


def test_should_encode_int_enums() -> None:
    class TestEnum(IntEnum):
        A = 1
        B = 2

    @bstruct.derive()
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

    data = bstruct.encode(original)
    decoded = bstruct.decode(TestData, data)

    assert decoded == original


def test_should_encode_strings() -> None:
    @bstruct.derive()
    @dataclass
    class TestData:
        v1: Annotated[str, bstruct.Size(size=11)]
        v2: Annotated[str, bstruct.Size(size=20)]

    original = TestData(v1="hello world", v2="🎉")

    data = bstruct.encode(original)
    decoded = bstruct.decode(TestData, data)

    assert decoded == original


def test_should_encode_bytes() -> None:
    @bstruct.derive()
    @dataclass
    class TestData:
        v1: Annotated[bytes, bstruct.Size(size=11)]

    original = TestData(v1=b"hello world")

    data = bstruct.encode(original)
    decoded = bstruct.decode(TestData, data)

    assert decoded == original


def test_should_encode_nested_classes() -> None:
    @bstruct.derive()
    @dataclass
    class InnerClass:
        value_1: bstruct.u32
        value_2: bstruct.u32

    @bstruct.derive()
    @dataclass
    class OuterClass:
        inner_1: InnerClass
        inner_2: InnerClass

    original = OuterClass(
        inner_1=InnerClass(12, 34),
        inner_2=InnerClass(56, 78),
    )

    data = bstruct.encode(original)
    decoded = bstruct.decode(OuterClass, data)

    assert decoded == original


def test_should_patch_external_classes() -> None:
    @dataclass
    class TestData:
        u8: int
        u16: int

    def _decode_test_class(data: bytes) -> TestData:
        u8 = int.from_bytes(data[0:1], byteorder="little", signed=False)
        u16 = int.from_bytes(data[1:3], byteorder="little", signed=False)

        return TestData(u8, u16)

    def _encode_test_class(value: TestData) -> bytes:
        b8 = value.u8.to_bytes(1, "little", signed=False)
        b16 = value.u16.to_bytes(2, "little", signed=False)

        return b8 + b16

    bstruct.patch(
        TestData, size=3, decode=_decode_test_class, encode=_encode_test_class
    )

    original = TestData(u8=1, u16=2)

    data = bstruct.encode(original)
    decoded = bstruct.decode(TestData, data)

    assert decoded == original


def test_should_encode_I80F48() -> None:
    @bstruct.derive()
    @dataclass
    class TestData:
        value: bstruct.I80F48

    original = TestData(Decimal("1234"))

    data = bstruct.encode(original)
    decoded = bstruct.decode(TestData, data)

    assert decoded == original


def test_should_encode_arrays() -> None:
    @bstruct.derive()
    @dataclass
    class TestItem:
        a: bstruct.u8
        b: bstruct.u8

    @bstruct.derive()
    @dataclass
    class TestData:
        native_values: Annotated[list[bstruct.u8], bstruct.Length(5)]
        custom_values: Annotated[list[TestItem], bstruct.Length(2)]

    original = TestData([1, 2, 3, 4, 5], custom_values=[TestItem(1, 2), TestItem(3, 4)])

    data = bstruct.encode(original)
    decoded = bstruct.decode(TestData, data)

    assert decoded == original


def test_should_unpack_multiple_instances() -> None:
    @bstruct.derive()
    @dataclass
    class TestData:
        value: bstruct.u8

    original_1 = TestData(1)
    original_2 = TestData(2)
    original_3 = TestData(3)

    data = (
        bstruct.encode(original_1)
        + bstruct.encode(original_2)
        + bstruct.encode(original_3)
    )

    decoded_1, decoded_2, decoded_3 = list(bstruct.decode_all(TestData, data))

    assert decoded_1 == original_1
    assert decoded_2 == original_2
    assert decoded_3 == original_3
