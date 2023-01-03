# Create a Custom Encoding

If you want to use external classes or classes with custom initialization logic,
a `CustomEncoding` can be created to tell `bstruct` how to handle those.
This is the same mechanism the library uses internally to create the encodings for
`str` or `Decimal`.

During decoding, an `AttributeIterator` of all the decoded fields is passed to the custom decode function.
You are supposed to take only the fields you specified.
During encoding, the fields must be pushed into the provided `AttributeList`.
The order in which the attributes are pushed/popped **must be the same** during decoding and encoding.

```{testcode}
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


range = Range(1, 2)
data = RangeEncoding.encode(range)

assert data == b"\x01\x02"

decoded = RangeEncoding.decode(data)
assert decoded.start == 1
assert decoded.end == 2
```
