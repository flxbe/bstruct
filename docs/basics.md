# Basics

The core of the library is the function `bstruct.derive`:

```python
bstruct.derive(value_type: type[T]) -> bstruct.Encoding[T]
```

It takes a type and tries to derive a binary encoding.
The encoding can then be used to translate between an instance of `T` and
the binary representation.

The native Python types usually do not provide enough information to derive
the binary encoding.
The only exception is the `bool` type.
For example, an `int` could be encoded as a 32-bit signed integer or a 64-bit
unsigned integer.
To add the missing information, the native types in Python can
be `Annotated` with metadata.

```{testcode}
from typing import Annotated

import bstruct


u8 = Annotated[int, bstruct.Encodings.u8]

IntEncoding = bstruct.derive(u8)

print(IntEncoding.encode(1))
```

```{testoutput}
b'\x01'
```

By annotating a type with an encoding, `bstruct.derive` has all the necessary information
to derive the correct binary format.
In addition, the annotations are transparent during runtime and for type checkers.
Please notice that in practice you could use `bstruct.Encodings.u8` directly, as this is
identical to the created `IntEncoding` in this simple example.

To support more complex data types, the library can automatically derive the encoding
for a dataclass, as long as every attribute contains enough metadata for `bstruct.derive`.
For convenience, there exist predefined constants for the most common types.

```{testcode}
from typing import Annotated
from dataclasses import dataclass

import bstruct


@dataclass
class Data:
    b: bool

    u8: bstruct.u8  # Annotated[int, bstruct.Encodings.u8]
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

    f16: bstruct.f16
    f32: bstruct.f32
    f64: bstruct.f64

    i80f48: bstruct.I80F48

    raw: Annotated[bytes, bstruct.Bytes(size=8)]


DataEncoding = bstruct.derive(Data)
```

### Strings

It is possible to work directly with utf-8 encoded strings.
This works similar to extracting the raw value using `bytes`.
However, any trailing `\0` bytes are removed when decoding a string value.
During encoding, the value is filled with `\0` bytes or truncated to exactly match the specified length.

```{testcode}
from typing import Annotated
from dataclasses import dataclass

import bstruct


@dataclass
class Data:
    text: Annotated[str, bstruct.String(size=8)]


DataEncoding = bstruct.derive(Data)
```

### `IntEnum`

Custom `IntEnum` classes can be used the same way as `int`s.

```{testcode}
from enum import IntEnum
from dataclasses import dataclass
from typing import Annotated

import bstruct


class Type(IntEnum):
    A = 1
    B = 2


@dataclass
class Data:
    type: Annotated[Type, bstruct.Encodings.u8]


DataEncoding = bstruct.derive(Data)
```

### Nested Classes

```{testcode}
from dataclasses import dataclass

import bstruct


@dataclass
class Inner:
    value: bstruct.u32


@dataclass
class Outer:
    value: Inner


OuterEncoding = bstruct.derive(Outer)
```

### Arrays

Fixed sized arrays can be translated from/into Python lists.

```{testcode}
from typing import Annotated
from dataclasses import dataclass

import bstruct


Data = Annotated[list[bstruct.u8], bstruct.Array(10)]

DataEncoding = bstruct.derive(Data)
```
