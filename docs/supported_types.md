# Supported Types

The library uses Python'b builtin `Annotated` type to extend builtin types like
`int` and `str` with the necessary information for (de)serialization.

```{testcode}
from typing import Annotated

import bstruct


class Data(bstruct.Struct):
    value: Annotated[int, bstruct.Encodings.u64]
```

For convenience, there exist predefined constants where ever possible.

## Basic Types

```{testcode}
from typing import Annotated

import bstruct


class Data(bstruct.Struct):
    b: bool

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

    i80f48: bstruct.I80F48

    raw: Annotated[bytes, bstruct.Size(size=8)]
```

## Strings

It is possible to work directly with utf-8 encoded strings.
This works similar to extracting the raw value using `bytes`.
However, any trailing `\0` bytes are removed when decoding a string value.
During encoding, the value is filled with `\0` bytes or truncated to exactly match the specified length.

```{testcode}
from typing import Annotated

import bstruct


class Data(bstruct.Struct):
    text: Annotated[str, bstruct.Size(size=8)]
```

## `IntEnum`

Custom `IntEnum` classes can be used the same way as `int`s.

```{testcode}
from enum import IntEnum
from typing import Annotated

import bstruct


class Type(IntEnum):
    A = 1
    B = 2


class Data(bstruct.Struct):
    type: Annotated[Type, bstruct.Encodings.u8]
```

## Nested Classes

```{testcode}
import bstruct


class Inner(bstruct.Struct):
    value: bstruct.u32


class Outer(bstruct.Struct):
    value: Inner
```

## Arrays

Fixed sized arrays can be translated from/into Python lists.

```{testcode}
from typing import Annotated

import bstruct


class Data(bstruct.Struct):
    items: Annotated[list[bstruct.u8], bstruct.Length(10)]
```
