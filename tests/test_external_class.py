from typing import Annotated

import bstruct


class Range:
    FIELDS = [bstruct.Encodings.u8, bstruct.Encodings.u8]

    start: int
    end: int

    def __init__(self, start: int, end: int):
        assert start < end

        self.start = start
        self.end = end


def decode_range(
    attributes: bstruct.AttributeIterator, _byteorder: bstruct.ByteOrder
) -> Range:
    start = next(attributes)
    assert isinstance(start, int)

    end = next(attributes)
    assert isinstance(end, int)

    return Range(start, end)


def encode_range(
    value: Range, attributes: bstruct.AttributeList, _byteorder: bstruct.ByteOrder
) -> None:
    attributes.append(value.start)
    attributes.append(value.end)


RangeEncoding = bstruct.CustomEncoding.create(
    target=Range,
    fields=Range.FIELDS,
    decode=decode_range,
    encode=encode_range,
)


def test_should_correctly_encode_an_external_class():
    class Struct(bstruct.Struct):
        range: Annotated[Range, RangeEncoding]

    struct = Struct(range=Range(1, 2))
    data = bstruct.encode(struct)

    assert data == b"\x01\x02"

    decoded = bstruct.decode(Struct, data)
    assert decoded.range.start == 1
    assert decoded.range.end == 2
