# Patch Existing Classes

```python
from dataclasses import dataclass

import bstruct

@dataclass
class ExistingClass:
    a: int
    b: int

def _decode_existing_class(data: bytes, byteorder: bstruct.ByteOrder) -> ExistingClass:
    u8 = int.from_bytes(data[0:1], byteorder, signed=False)
    u16 = int.from_bytes(data[1:3], byteorder, signed=False)

    return ExistingClass(u8, u16)

def _encode_existing_class(value: ExistingClass, byteorder: bstruct.ByteOrder) -> bytes:
    b8 = value.u8.to_bytes(1, byteorder, signed=False)
    b16 = value.u16.to_bytes(2, byteorder, signed=False)

    return b8 + b16

bstruct.patch(
    ExistingClass, size=3, decode=_decode_existing_class, encode=_encode_existing_class
)

```
