import timeit
from typing import Annotated, Callable, Any
from dataclasses import dataclass

import construct
import bstruct


@bstruct.derive()
@dataclass
class TestData:
    u8: bstruct.u8
    u16: bstruct.u16
    u32: bstruct.u32
    u64: bstruct.u64
    byte_data: Annotated[bytes, bstruct.Size(12)]
    l: Annotated[list[bstruct.u8], bstruct.Length(5)]


EXPECTED = TestData(
    u8=1,
    u16=2,
    u32=3,
    u64=4,
    byte_data=b"hello, world",
    l=[1, 2, 3, 4, 5],
)

DATA = bstruct.encode(EXPECTED)


RUNS = 100_000


def _measure_and_print(name: str, func: Callable[[], Any]) -> None:
    total_runtime = timeit.Timer(func).timeit(RUNS)

    us_per_run = (total_runtime / RUNS) * 1e6
    print(f"{name}: {us_per_run:.02f} us")


def _decode_bstruct() -> TestData:
    return bstruct.decode(TestData, DATA)


_measure_and_print("decode: bstruct", _decode_bstruct)


def _encode_bstruct() -> bytes:
    return bstruct.encode(EXPECTED)


_measure_and_print("encode: bstruct", _encode_bstruct)


raw_struct = bstruct.get_struct(TestData)


def _decode_struct() -> TestData:
    u8, u16, u32, u64, byte_data, l1, l2, l3, l4, l5 = raw_struct.unpack(DATA)

    return TestData(u8, u16, u32, u64, byte_data, [l1, l2, l3, l4, l5])


_measure_and_print("decode: struct", _decode_struct)


def _encode_struct() -> bytes:
    return raw_struct.pack(1, 2, 3, 4, b"hello, world", 1, 2, 3, 4, 5)


_measure_and_print("encode: struct", _encode_struct)


ConstructFormat = construct.Struct(
    "u8" / construct.Int8ul,  # type: ignore
    "u16" / construct.Int16ul,  # type: ignore
    "u32" / construct.Int32ul,  # type: ignore
    "u64" / construct.Int64ul,  # type: ignore
    "byte_data" / construct.Bytes(12),
    "l" / construct.Array(5, construct.Int8ul),
)


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


_measure_and_print("decode: construct", _decode_construct)


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

_measure_and_print("encode: construct", _encode_construct)


CompiledConstructFormat = construct.Struct(
    "u8" / construct.Int8ul,  # type: ignore
    "u16" / construct.Int16ul,  # type: ignore
    "u32" / construct.Int32ul,  # type: ignore
    "u64" / construct.Int64ul,  # type: ignore
    "byte_data" / construct.Bytes(12),
    "l" / construct.Array(5, construct.Int8ul),
)
CompiledConstructFormat.compile()  # type: ignore


def _decode_compiled_construct() -> TestData:
    data = CompiledConstructFormat.parse(DATA)  # type: ignore

    return TestData(
        data["u8"],  # type: ignore
        data["u16"],  # type: ignore
        data["u32"],  # type: ignore
        data["u64"],  # type: ignore
        data["byte_data"],  # type: ignore
        [item for item in data["l"]],  # type: ignore
    )


_measure_and_print("decode: construct_compiled", _decode_compiled_construct)


def _encode_construct_compiled() -> bytes:
    return CompiledConstructFormat.build(  # type: ignore
        {
            "u8": 1,
            "u16": 2,
            "u32": 3,
            "u64": 4,
            "byte_data": b"hello, world",
            "l": [1, 2, 3, 4, 5],
        }
    )


assert _encode_construct_compiled() == DATA

_measure_and_print("encode: construct_compiled", _encode_construct_compiled)
