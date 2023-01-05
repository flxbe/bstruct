from dataclasses import dataclass
from typing import Annotated

import construct
import pyperf

import bstruct


@dataclass(slots=True)
class TestData:
    u8: bstruct.u8
    u16: bstruct.u16
    u32: bstruct.u32
    u64: bstruct.u64
    byte_data: Annotated[bytes, bstruct.Bytes(12)]
    l: Annotated[list[bstruct.u8], bstruct.Array(5)]


TestDataEncoding = bstruct.derive(TestData)


EXPECTED = TestData(
    u8=1,
    u16=2,
    u32=3,
    u64=4,
    byte_data=b"hello, world",
    l=[1, 2, 3, 4, 5],
)

DATA = TestDataEncoding.encode(EXPECTED)


def _decode_bstruct() -> TestData:
    return TestDataEncoding.decode(DATA)


def _encode_bstruct() -> bytes:
    return TestDataEncoding.encode(EXPECTED)


raw_struct = TestDataEncoding.get_struct("little")


def _decode_struct() -> TestData:
    u8, u16, u32, u64, byte_data, l1, l2, l3, l4, l5 = raw_struct.unpack(DATA)

    return TestData(u8, u16, u32, u64, byte_data, [l1, l2, l3, l4, l5])


def _encode_struct() -> bytes:
    return raw_struct.pack(1, 2, 3, 4, b"hello, world", 1, 2, 3, 4, 5)


ConstructFormat = construct.Struct(
    "u8" / construct.Int8ul,  # type: ignore
    "u16" / construct.Int16ul,  # type: ignore
    "u32" / construct.Int32ul,  # type: ignore
    "u64" / construct.Int64ul,  # type: ignore
    "byte_data" / construct.Bytes(12),
    "l" / construct.Array(5, construct.Int8ul),
).compile()


def _decode_construct() -> TestData:
    data = ConstructFormat.parse(DATA)  # type: ignore

    return TestData(
        data["u8"],  # type: ignore
        data["u16"],  # type: ignore
        data["u32"],  # type: ignore
        data["u64"],  # type: ignore
        data["byte_data"],  # type: ignore
        [item for item in data["l"]],  # type: ignore
    )


def _encode_construct() -> bytes:
    return ConstructFormat.build(  # type: ignore
        {
            "u8": 1,
            "u16": 2,
            "u32": 3,
            "u64": 4,
            "byte_data": b"hello, world",
            "l": [1, 2, 3, 4, 5],
        }
    )


assert _encode_construct() == DATA


runner = pyperf.Runner()
runner.bench_func("decode (bstruct)", _decode_bstruct)  # type: ignore
runner.bench_func("encode (bstruct)", _encode_bstruct)  # type: ignore
runner.bench_func("decode (struct)", _decode_struct)  # type: ignore
runner.bench_func("encode (struct)", _encode_struct)  # type: ignore
runner.bench_func("decode (construct)", _decode_construct)  # type: ignore
runner.bench_func("encode (construct)", _encode_construct)  # type: ignore
