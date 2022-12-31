from io import BytesIO

import bstruct


class Header(bstruct.Struct):
    item_count: bstruct.u8


class Item(bstruct.Struct):
    value: bstruct.u8


def decode(buffer: BytesIO) -> list[Item]:
    header = bstruct.read(Header, buffer)
    items = bstruct.read_many(Item, buffer, count=header.item_count)

    return list(items)


def encode(items: list[Item], buffer: BytesIO) -> None:
    bstruct.write(Header(len(items)), buffer)
    bstruct.write_many(items, buffer)


def test_should_correctly_work_with_dynamic_content() -> None:
    items = [Item(i) for i in range(100)]

    # This could also be a file or a stream.
    buffer = BytesIO()
    encode(items, buffer)

    # Reset buffer to the start, so the decode function has something to read.
    buffer.seek(0)
    decoded = decode(buffer)

    assert items == decoded
