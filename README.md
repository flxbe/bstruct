# bstruct

Declaratively create encoders and decoders for binary data using type annotations.
The goal is to strike a sensible balance between usability and efficiency
while allowing easy fallback to Python's built-in `struct` library for maximum performance.

## ⚠️ DISCLAIMER

While I used this approach successfully in production for over a year, this project is still a work in progress
and has multiple areas that need a lot of work (support for big-endian order, error handling).
Use at your own risk.

## Getting Started

```bash
pip install bstruct
```

```python
from dataclasses import dataclass

import bstruct


@bstruct.derive()
@dataclass
class Data:
    a: bool
    b: bstruct.u8

data = Data(a=True, b=1)

encoded = bstruct.encode(data)
decoded = bstruct.decode(Data, encoded)

assert decoded == data
```

The helper type `bstruct.u8` is just an annotated int: `Annotated[int, Encodings.u8]`.
As a result, `bstruct` simply returns native types.

### Supported Types

```python
from dataclasses import dataclass
from typing import Annotated

import bstruct


@bstruct.derive()
@dataclass
class Data:
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
@bstruct.derive()
@dataclass
class Inner:
    value: bstruct.u32

@bstruct.derive()
@dataclass
class Outer:
    value: Inner
```

### `IntEnum`

```python
class Type(IntEnum):
    A = 1
    B = 2

@bstruct.derive()
@dataclass
class Data:
    type: Annotated[Type, bstruct.Encodings.u8]
```

### Patch Existing Classes

```python
@dataclass
class ExistingClass:
    a: int
    b: int

def _decode_test_class(data: bytes) -> TestData:
    u8 = int.from_bytes(data[0:1], byteorder="little", signed=False)
    u16 = int.from_bytes(data[1:3], byteorder="little", signed=False)

    return TestData(u8, u16)

def _encode_test_class(value: TestData) -> bytes:
    b8 = value.u8.to_bytes(1, "little", signed=False)
    b16 = value.u16.to_bytes(2, "little", signed=False)

    return b8 + b16

bstruct.patch(
    TestData, size=3, decode=_decode_test_class, encode=_encode_test_class
)

```

### Use Underlying `struct.Struct`

```python
@bstruct.derive()
@dataclass
class Data:
    u8: bstruct.u8
    u16: bstruct.u16

native_struct = bstruct.get_struct(Data)
```

It is also possible to use `bstruct` only as a convenience wrapper for creating the native `struct` format string.
This of course only works for types supported by `struct`.

```python
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
The benchmarks where executed using Python 3.10.4 on a MacBook Pro 2018 with a 2.3GHz i5 processor.

### `benchmarks/builtins.py`

| Name                 | decode   | encode   |
| -------------------- | -------- | -------- |
| bstruct              | 2.57 us  | 2.29 us  |
| struct               | 0.94 us  | 0.30 us  |
| construct            | 28.08 us | 25.58 us |
| construct (compiled) | 27.65 us | 25.63 us |

### `benchmarks/lists.py`

| Name                     | decode   | encode    |
| ------------------------ | -------- | --------- |
| bstruct (native items)   | 2.26 us  | 1.30 us   |
| bstruct (class items)    | 8.64 us  | 6.20 us   |
| struct (native items)    | 0.25 us  | 0.38 us   |
| construct (native items) | 20.25 us | 19.49 us  |
| construct (class items)  | 97.84 us | 105.71 us |
