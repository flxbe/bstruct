import timeit
from typing import Annotated, Any, Callable
from dataclasses import dataclass

import bstruct
import construct


RUNS = 100_000


@bstruct.derive()
@dataclass
class NativeList:
    values: Annotated[list[bstruct.u8], bstruct.Length(10)]


native_list = NativeList(
    values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
)

native_list_data = bstruct.encode(native_list)


def _measure_and_print(name: str, func: Callable[[], Any]) -> None:
    total_runtime = timeit.Timer(func).timeit(RUNS)

    us_per_run = (total_runtime / RUNS) * 1e6
    print(f"{name}: {us_per_run:.02f} us")


def _decode_native_list() -> None:
    bstruct.decode(NativeList, native_list_data)


_measure_and_print("decode: native_list", _decode_native_list)


def _encode_native_list() -> None:
    bstruct.encode(native_list)


_measure_and_print("encode: native_list", _encode_native_list)


@bstruct.derive()
@dataclass
class ListItem:
    a: bstruct.u8


@bstruct.derive()
@dataclass
class ClassList:
    values: Annotated[list[ListItem], bstruct.Length(10)]


class_list = ClassList(
    values=[
        ListItem(1),
        ListItem(2),
        ListItem(3),
        ListItem(4),
        ListItem(5),
        ListItem(6),
        ListItem(7),
        ListItem(8),
        ListItem(9),
        ListItem(0),
    ]
)


class_list_data = bstruct.encode(class_list)


def _decode_class_list() -> None:
    bstruct.decode(ClassList, class_list_data)


_measure_and_print("decode: class_list", _decode_class_list)


def _encode_class_list() -> None:
    bstruct.encode(class_list)


_measure_and_print("encode: class_list", _encode_class_list)


raw_struct = bstruct.get_struct(ClassList)
raw_list = (1, 2, 3, 4, 5, 6, 7, 8, 9, 0)


def _decode_raw_list() -> tuple[int]:
    return raw_struct.unpack(class_list_data)


assert _decode_raw_list() == raw_list


_measure_and_print("decode: raw_list", _decode_raw_list)


def _encode_raw_list() -> bytes:
    return raw_struct.pack(*raw_list)


assert _encode_raw_list() == class_list_data


_measure_and_print("encode: raw_list", _encode_raw_list)


ConstructItem = construct.Struct(
    "a" / construct.Int8ul,  # type: ignore
)

ConstructClass = construct.Struct(
    "values" / construct.Array(10, ConstructItem),
)


def _decode_construct_list() -> construct.Container:
    return ConstructClass.parse(class_list_data)  # type: ignore


_measure_and_print("decode: construct_list", _decode_construct_list)


def _encode_construct_list() -> bytes:
    return ConstructClass.build(  # type: ignore
        {
            "values": [
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
        }
    )


_measure_and_print("encode: construct_list", _encode_construct_list)
