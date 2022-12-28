# Advanced

## Patch Existing Classes

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

## Use Underlying `struct.Struct`

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
