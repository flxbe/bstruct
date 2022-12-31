from io import BytesIO

import bstruct


class Header(bstruct.Struct):
    item_count: bstruct.u8


class Item(bstruct.Struct):
    value: bstruct.u8


def decode(data: bytes) -> list[Item]:
    buffer = BytesIO(data)

    header = bstruct.read(Header, buffer)
    items = bstruct.read_many(Item, buffer, count=header.item_count)

    return list(items)


def encode(items: list[Item]) -> bytes:
    buffer = BytesIO()

    bstruct.write(Header(len(items)), buffer)
    bstruct.write_all(items, buffer)

    return buffer.getvalue()


def test_should_correctly_work_with_dynamic_content() -> None:
    items = [Item(i) for i in range(100)]

    data = encode(items)
    decoded = decode(data)

    assert items == decoded
