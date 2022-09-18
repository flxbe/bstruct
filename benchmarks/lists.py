import timeit
from typing import Annotated, Any, Callable
from dataclasses import dataclass

import bstruct


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


_measure_and_print("native_list", _decode_native_list)


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


_measure_and_print("class_list", _decode_class_list)


def _decode_raw_class_list() -> None:
    bstruct.decode_raw(ClassList, class_list_data)


_measure_and_print("raw_class_list", _decode_raw_class_list)
