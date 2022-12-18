import timeit
from typing import Annotated, Any, Callable

import bstruct
import construct


RUNS = 100_000


def _measure_and_print(name: str, func: Callable[[], Any]) -> None:
    total_runtime = timeit.Timer(func).timeit(RUNS)

    us_per_run = (total_runtime / RUNS) * 1e6
    print(f"{name}: {us_per_run:.02f} us")


class BstructItem(bstruct.Struct):
    a: bstruct.u8


class BstructList(bstruct.Struct):
    values: Annotated[list[BstructItem], bstruct.Length(10)]


bstruct_list = BstructList(
    values=[
        BstructItem(1),
        BstructItem(2),
        BstructItem(3),
        BstructItem(4),
        BstructItem(5),
        BstructItem(6),
        BstructItem(7),
        BstructItem(8),
        BstructItem(9),
        BstructItem(0),
    ]
)


list_data = bstruct.encode(bstruct_list)


def _decode_bstruct() -> None:
    bstruct.decode(BstructList, list_data)


_measure_and_print("bstruct: decode", _decode_bstruct)


def _encode_bstruct() -> None:
    bstruct.encode(bstruct_list)


_measure_and_print("bstruct: encode", _encode_bstruct)


ConstructItem = construct.Struct(
    "a" / construct.Int8ul,  # type: ignore
)

ConstructList = construct.Array(10, ConstructItem)


def _decode_construct() -> construct.Container:
    return ConstructList.parse(list_data)  # type: ignore


_measure_and_print("construct: decode", _decode_construct)


construct_list = [
    {"a": 1},
    {"a": 2},
    {"a": 3},
    {"a": 4},
    {"a": 5},
    {"a": 6},
    {"a": 7},
    {"a": 8},
    {"a": 9},
    {"a": 0},
]


def _encode_construct() -> bytes:
    return ConstructList.build(construct_list)  # type: ignore


_measure_and_print("construct: encode", _encode_construct)
