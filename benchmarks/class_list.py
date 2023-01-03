from typing import Annotated

import pyperf
import bstruct
import construct


class BstructItem(bstruct.Struct):
    a: bstruct.u8


class BstructList(bstruct.Struct):
    values: Annotated[list[BstructItem], bstruct.Array(10)]


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


def _encode_bstruct() -> None:
    bstruct.encode(bstruct_list)


ConstructItem = construct.Struct(
    "a" / construct.Int8ul,  # type: ignore
).compile()

ConstructList = construct.Array(10, ConstructItem).compile()  # type: ignore


def _decode_construct() -> construct.Container:
    return ConstructList.parse(list_data)  # type: ignore


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


runner = pyperf.Runner()
runner.bench_func("decode (bstruct)", _decode_bstruct)  # type: ignore
runner.bench_func("encode (bstruct)", _encode_bstruct)  # type: ignore
runner.bench_func("decode (construct)", _decode_construct)  # type: ignore
runner.bench_func("encode (construct)", _encode_construct)  # type: ignore
