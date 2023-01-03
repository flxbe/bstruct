# Quickstart

```{testcode}
from typing import Annotated
from dataclasses import dataclass

import bstruct


@dataclass
class Item:
    identifier: bstruct.u64  # shorthand for: Annotated[int, bstruct.Encodings.u64]
    value: bstruct.i32       # shorthand for: Annotated[int, bstruct.Encodings.i32]


ItemArray = Annotated[list[Item], bstruct.Array(3)]

ItemArrayEncoding = bstruct.derive(ItemArray)


array = [
    Item(identifier=0, value=-1),
    Item(identifier=1, value=0),
    Item(identifier=2, value=1),
]

encoded = ItemArrayEncoding.encode(array)
decoded = ItemArrayEncoding.decode(encoded)

assert decoded == array
```
