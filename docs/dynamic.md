# Dynamic Data

Any `bstruct.Encoding[T]` can only describe data with a fixed layout.
To make working with dynamic data layouts more convenient, the library supports writing to and reading from `bytes` buffers.

```{testcode}
from io import BytesIO
from dataclasses import dataclass

import bstruct


@dataclass
class Header:
    item_count: bstruct.u8


HeaderEncoding = bstruct.derive(Header)


@dataclass
class Item:
    value: bstruct.u8


ItemEncoding = bstruct.derive(Item)


def decode(buffer: BytesIO) -> list[Item]:
    header = HeaderEncoding.read(buffer)
    items = ItemEncoding.read_many(buffer, count=header.item_count)

    return list(items)


def encode(items: list[Item], buffer: BytesIO) -> None:
    HeaderEncoding.write(Header(len(items)), buffer)
    ItemEncoding.write_many(items, buffer)


items = [Item(i) for i in range(100)]

# This could also be a file or a stream.
buffer = BytesIO()
encode(items, buffer)

# Reset buffer to the start, so the decode function has something to read.
buffer.seek(0)
decoded = decode(buffer)

assert items == decoded
```
