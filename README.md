# bstruct

[![ci](https://github.com/flxbe/bstruct/actions/workflows/ci.yml/badge.svg)](https://github.com/flxbe/bstruct/actions/workflows/ci.yml)
[![pypi](https://img.shields.io/pypi/v/bstruct)](https://pypi.org/project/bstruct/)

Declaratively create encoders and decoders for binary data using type annotations.

- **Simple**: Just use regular type annotations to declare all the necessary information for parsing.
  No custom syntax, operator overloading or custom wrapper types.
- **Efficient**: Only do the minimum work necessary to pack/unpack the binary data and translate from/into complex data types.
  Allow easy fallback to Python's built-in `struct` library for maximum performance.

## ⚠️ DISCLAIMER

This project is still a work in progress and has multiple areas that need some work (big-endian support, error handling).
Use at your own risk.

## Getting Started

```bash
pip install bstruct
```

```python
from typing import Annotated
import bstruct


class Item(bstruct.Struct):
    id: bstruct.u64
    value: bstruct.i32

class Sequence(bstruct.Struct):
    items: Annotated[list[Item], bstruct.Length(3)]

sequence = Sequence(
    items=[
        Item(id=0, value=-1),
        Item(id=1, value=0),
        Item(id=2, value=1),
    ]
)

encoded = bstruct.encode(sequence)
decoded = bstruct.decode(Data, encoded)

assert decoded == sequence
```

The helper type `bstruct.u64` is just an annotated int: `Annotated[int, Encodings.u64]` under the hood.
Both during runtime and type-checking, both `id` and `value` are just plain `int` values.

### Supported Types

```python
from typing import Annotated

import bstruct


class Data(bstruct.Struct):
    u8: bstruct.u8
    u16: bstruct.u16
    u32: bstruct.u32
    u64: bstruct.u64
    u128: bstruct.u128
    u256: bstruct.u256

    i8: bstruct.i8
    i16: bstruct.i16
    i32: bstruct.i32
    i64: bstruct.i64
    i128: bstruct.i128
    i256: bstruct.i256

    text: Annotated[str, bstruct.Size(size=8)]
    raw: Annotated[bytes, bstruct.Size(size=8)]
```

### Nested Classes

```python
import bstruct


class Inner(bstruct.Struct):
    value: bstruct.u32

class Outer(bstruct.Struct):
    value: Inner
```

### `IntEnum`

```python
import bstruct


class Type(IntEnum):
    A = 1
    B = 2

class Data(bstruct.Struct):
    type: Annotated[Type, bstruct.Encodings.u8]
```

### Patch Existing Classes

```python
from dataclasses import dataclass

import bstruct

@dataclass
class ExistingClass:
    a: int
    b: int

def _decode_existing_class(data: bytes) -> ExistingClass:
    u8 = int.from_bytes(data[0:1], byteorder="little", signed=False)
    u16 = int.from_bytes(data[1:3], byteorder="little", signed=False)

    return ExistingClass(u8, u16)

def _encode_existing_class(value: ExistingClass) -> bytes:
    b8 = value.u8.to_bytes(1, "little", signed=False)
    b16 = value.u16.to_bytes(2, "little", signed=False)

    return b8 + b16

bstruct.patch(
    ExistingClass, size=3, decode=_decode_existing_class, encode=_encode_existing_class
)

```

### Use Underlying `struct.Struct`

```python
import bstruct


class Data(bstruct.Struct):
    u8: bstruct.u8
    u16: bstruct.u16

native_struct = bstruct.get_struct(Data)
```

It is also possible to use `bstruct` only as a convenience wrapper for creating the native `struct` format string.
This of course only works for types supported by `struct`.

```python
import struct

import bstruct


format_str = bstruct.compile_format([
    bstruct.Encodings.u8,
    bstruct.Encodings.bytes(8),
    bstruct.Encodings.i64
])

struct.Struct(f"<{format_str}")
```

## Benchmarks

Please see the source of the benchmarks in the `benchmarks` directory.
Feel free to create an issue or PR should there be a problem with the methodology.
The benchmarks where executed using Python 3.11.1 and
[construct](https://pypi.org/project/construct/) 2.10.68
on a MacBook Pro 2018 with a 2.3GHz i5 processor.

### `benchmarks/builtins.py`

| Name                 | decode   | encode   |
| -------------------- | -------- | -------- |
| struct               | 0.62 us  | 0.23 us  |
| bstruct              | 1.97 us  | 1.67 us  |
| construct            | 23.10 us | 22.11 us |
| construct (compiled) | 24.90 us | 25.43 us |

### `benchmarks/native_list.py`

| Name      | decode  | encode  |
| --------- | ------- | ------- |
| struct    | 0.18 us | 0.34 us |
| bstruct   | 2.03 us | 1.04 us |
| construct | 8.99 us | 8.34 us |

### `benchmarks/class_list.py`

| Name      | decode   | encode   |
| --------- | -------- | -------- |
| bstruct   | 7.28 us  | 5.19 us  |
| construct | 88.78 us | 84.85 us |

### `benchmarks/nested.py`

| Name      | decode   | encode   |
| --------- | -------- | -------- |
| bstruct   | 5.36 us  | 4.44 us  |
| construct | 70.48 us | 70.93 us |
