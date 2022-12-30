from typing import Annotated

import pyperf
import bstruct
import construct


class BstructList(bstruct.Struct):
    values: Annotated[list[bstruct.u8], bstruct.Length(10)]


bstruct_list = BstructList(
    values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
)

list_data = bstruct.encode(bstruct_list)


def _decode_bstruct() -> None:
    bstruct.decode(BstructList, list_data)


def _encode_bstruct() -> None:
    bstruct.encode(bstruct_list)


raw_struct = bstruct.get_struct(BstructList)
raw_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]


def _decode_struct() -> tuple[int]:
    return raw_struct.unpack(list_data)


def _encode_struct() -> bytes:
    return raw_struct.pack(*raw_list)


ConstructList = construct.Array(10, construct.Int8ul).compile()  # type: ignore


def _decode_construct() -> construct.Container:
    return ConstructList.parse(list_data)  # type: ignore


def _encode_construct() -> bytes:
    return ConstructList.build(raw_list)  # type: ignore


runner = pyperf.Runner()
runner.bench_func("decode (bstruct)", _decode_bstruct)  # type: ignore
runner.bench_func("encode (bstruct)", _encode_bstruct)  # type: ignore
runner.bench_func("decode (struct)", _decode_struct)  # type: ignore
runner.bench_func("encode (struct)", _encode_struct)  # type: ignore
runner.bench_func("decode (construct)", _decode_construct)  # type: ignore
runner.bench_func("encode (construct)", _encode_construct)  # type: ignore
