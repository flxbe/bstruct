# Fallback to `struct.Struct`

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