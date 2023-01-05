from dataclasses import dataclass
from io import BytesIO

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


def test_should_correctly_work_with_dynamic_content() -> None:
    items = [Item(i) for i in range(100)]

    # This could also be a file or a stream.
    buffer = BytesIO()
    encode(items, buffer)

    # Reset buffer to the start, so the decode function has something to read.
    buffer.seek(0)
    decoded = decode(buffer)

    assert items == decoded
