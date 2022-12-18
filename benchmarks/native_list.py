import timeit
from typing import Annotated, Any, Callable

import bstruct
import construct


RUNS = 100_000


class BstructList(bstruct.Struct):
    values: Annotated[list[bstruct.u8], bstruct.Length(10)]


bstruct_list = BstructList(
    values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
)

list_data = bstruct.encode(bstruct_list)


def _measure_and_print(name: str, func: Callable[[], Any]) -> None:
    total_runtime = timeit.Timer(func).timeit(RUNS)

    us_per_run = (total_runtime / RUNS) * 1e6
    print(f"{name}: {us_per_run:.02f} us")


def _decode_bstruct() -> None:
    bstruct.decode(BstructList, list_data)


_measure_and_print("bstruct: decode", _decode_bstruct)


def _encode_bstruct() -> None:
    bstruct.encode(bstruct_list)


_measure_and_print("bstruct: encode", _encode_bstruct)


raw_struct = bstruct.get_struct(BstructList)
raw_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]


def _decode_struct() -> tuple[int]:
    return raw_struct.unpack(list_data)


_measure_and_print("struct: decode", _decode_struct)


def _encode_struct() -> bytes:
    return raw_struct.pack(*raw_list)


_measure_and_print("struct: encode", _encode_struct)


ConstructList = construct.Array(10, construct.Int8ul)


def _decode_construct() -> construct.Container:
    return ConstructList.parse(list_data)  # type: ignore


_measure_and_print("construct: decode", _decode_construct)


def _encode_construct() -> bytes:
    return ConstructList.build(raw_list)  # type: ignore


_measure_and_print("construct: encode", _encode_construct)
