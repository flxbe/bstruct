import timeit
from typing import Annotated, Any, Callable

import bstruct
import construct


RUNS = 100_000


def _measure_and_print(name: str, func: Callable[[], Any]) -> None:
    total_runtime = timeit.Timer(func).timeit(RUNS)

    us_per_run = (total_runtime / RUNS) * 1e6
    print(f"{name}: {us_per_run:.02f} us")


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


_measure_and_print("bstruct: decode", _decode_bstruct)


def _encode_bstruct() -> None:
    bstruct.encode(bstruct_class)


_measure_and_print("bstruct: encode", _encode_bstruct)


ConstructInner = construct.Struct(
    "a" / construct.Int64ul,  # type: ignore
    "b" / construct.Int64ul,  # type: ignore
)

ConstructClass = construct.Struct(
    "inner" / ConstructInner, "items" / construct.Array(5, ConstructInner)
)

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


_measure_and_print("construct: decode", _decode_construct)


def _encode_construct() -> bytes:
    return ConstructClass.build(construct_class)  # type: ignore


_measure_and_print("construct: encode", _encode_construct)
