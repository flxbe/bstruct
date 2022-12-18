# bstruct

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
import bstruct


class Data(bstruct.Struct):
    a: bool
    b: bstruct.u8

data = Data(a=True, b=1)

encoded = bstruct.encode(data)
decoded = bstruct.decode(Data, encoded)

assert decoded == data
```

The helper type `bstruct.u8` is just an annotated int: `Annotated[int, Encodings.u8]`.
As a result, the attribute `b` is just a native `int`.

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
| bstruct              | 1.97 us  | 1.67 us  |
| struct               | 0.62 us  | 0.23 us  |
| construct            | 23.10 us | 22.11 us |
| construct (compiled) | 24.90 us | 25.43 us |

### `benchmarks/lists.py`

| Name                     | decode   | encode    |
| ------------------------ | -------- | --------- |
| bstruct (native items)   | 1.85 us  | 1.03 us   |
| bstruct (class items)    | 7.88 us  | 5.69 us   |
| struct (native items)    | 0.20 us  | 0.35 us   |
| construct (native items) | 17.66 us | 17.34 us  |
| construct (class items)  | 98.07 us | 100.76 us |
