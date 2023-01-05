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
    attributes: bstruct.ValueIterator, _byteorder: bstruct.ByteOrder
) -> Range:
    start = next(attributes)
    assert isinstance(start, int)

    end = next(attributes)
    assert isinstance(end, int)

    return Range(start, end)


def encode_range(
    value: Range, attributes: bstruct.ValueList, _byteorder: bstruct.ByteOrder
) -> None:
    attributes.append(value.start)
    attributes.append(value.end)


RangeEncoding = bstruct.CustomEncoding.create(
    target=Range,
    fields=Range.FIELDS,
    decode_attributes=decode_range,
    encode_attributes=encode_range,
)


def test_should_correctly_encode_an_external_class():
    range = Range(1, 2)
    data = RangeEncoding.encode(range)

    assert data == b"\x01\x02"

    decoded = RangeEncoding.decode(data)
    assert decoded.start == 1
    assert decoded.end == 2
