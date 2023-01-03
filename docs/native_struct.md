# Fallback to `struct.Struct`

```{testcode}
from dataclasses import dataclass

import bstruct


@dataclass
class Data:
    u8: bstruct.u8
    u16: bstruct.u16


DataEncoding = bstruct.derive(Data)

native_struct = DataEncoding.get_struct(byteorder="little")
```

It is also possible to use `bstruct` only as a convenience wrapper for creating the native `struct` format string.
This of course only works for types supported by `struct`.

```{testcode}
import struct

import bstruct


format_str = bstruct.compile_format([
    bstruct.Encodings.u8,
    bstruct.Bytes(8),
    bstruct.Encodings.i64
])

struct.Struct(f"<{format_str}")
```
