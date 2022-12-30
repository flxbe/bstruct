from typing import Annotated

import pyperf
import bstruct
import construct


class BStructInner(bstruct.Struct):
    a: bstruct.u64
    b: bstruct.u64


class BstructClass(bstruct.Struct):
    inner: BStructInner
    items: Annotated[list[BStructInner], bstruct.Length(5)]


bstruct_class = BstructClass(
    inner=BStructInner(1, 2),
    items=[
        BStructInner(1, 3),
        BStructInner(1, 4),
        BStructInner(1, 5),
        BStructInner(1, 6),
        BStructInner(1, 7),
    ],
)


data = bstruct.encode(bstruct_class)


def _decode_bstruct() -> None:
    bstruct.decode(BstructClass, data)


def _encode_bstruct() -> None:
    bstruct.encode(bstruct_class)


ConstructInner = construct.Struct(
    "a" / construct.Int64ul,  # type: ignore
    "b" / construct.Int64ul,  # type: ignore
).compile()

ConstructClass = construct.Struct(
    "inner" / ConstructInner, "items" / construct.Array(5, ConstructInner)  # type: ignore
).compile()

construct_class = {
    "inner": {"a": 1, "b": 2},
    "items": [
        {"a": 1, "b": 3},
        {"a": 1, "b": 4},
        {"a": 1, "b": 5},
        {"a": 1, "b": 6},
        {"a": 1, "b": 7},
    ],
}

assert ConstructClass.build(construct_class) == data  # type: ignore


def _decode_construct() -> construct.Container:
    return ConstructClass.parse(data)  # type: ignore


def _encode_construct() -> bytes:
    return ConstructClass.build(construct_class)  # type: ignore


runner = pyperf.Runner()
runner.bench_func("decode (bstruct)", _decode_bstruct)  # type: ignore
runner.bench_func("encode (bstruct)", _encode_bstruct)  # type: ignore
runner.bench_func("decode (construct)", _decode_construct)  # type: ignore
runner.bench_func("encode (construct)", _encode_construct)  # type: ignore
