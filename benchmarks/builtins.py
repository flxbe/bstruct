import timeit
from typing import Annotated, Callable
from dataclasses import dataclass

import struct
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


def _measure_and_print(name: str, func: Callable[[], TestData]) -> None:
    result = func()
    assert result == EXPECTED

    total_runtime = timeit.Timer(func).timeit(RUNS)

    us_per_run = (total_runtime / RUNS) * 1e6
    print(f"{name}: {us_per_run:.02f} us")


def _decode_bstruct() -> TestData:
    return bstruct.decode(TestData, DATA)


_measure_and_print("bstruct", _decode_bstruct)


def _decode_struct() -> TestData:
    u8, u16, u32, u64, byte_data, l1, l2, l3, l4, l5 = struct.unpack(
        f"<BHIQ12s5B", DATA
    )

    return TestData(u8, u16, u32, u64, byte_data, [l1, l2, l3, l4, l5])


_measure_and_print("struct", _decode_struct)


ConstructFormat = construct.Struct(
    "u8" / construct.Int8ul,
    "u16" / construct.Int16ul,
    "u32" / construct.Int32ul,
    "u64" / construct.Int64ul,
    "byte_data" / construct.Bytes(12),
    "l" / construct.Array(5, construct.Int8ul),
)


def _decode_construct() -> TestData:
    data = ConstructFormat.parse(DATA)

    return TestData(
        data["u8"],
        data["u16"],
        data["u32"],
        data["u64"],
        data["byte_data"],
        [item for item in data["l"]],
    )


_measure_and_print("construct", _decode_construct)


CompiledConstructFormat = construct.Struct(
    "u8" / construct.Int8ul,
    "u16" / construct.Int16ul,
    "u32" / construct.Int32ul,
    "u64" / construct.Int64ul,
    "byte_data" / construct.Bytes(12),
    "l" / construct.Array(5, construct.Int8ul),
)
CompiledConstructFormat.compile()


def _decode_compiled_construct() -> TestData:
    data = CompiledConstructFormat.parse(DATA)

    return TestData(
        data["u8"],
        data["u16"],
        data["u32"],
        data["u64"],
        data["byte_data"],
        [item for item in data["l"]],
    )


_measure_and_print("construct_compiled", _decode_compiled_construct)
