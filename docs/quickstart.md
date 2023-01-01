# Quickstart

```{testcode}
from typing import Annotated

import bstruct


class Item(bstruct.Struct):
    identifier: bstruct.u64  # shorthand for: Annotated[int, bstruct.Encodings.u64]
    value: bstruct.i32       # shorthand for: Annotated[int, bstruct.Encodings.i32]


class Sequence(bstruct.Struct):
    items: Annotated[list[Item], bstruct.Length(3)]


sequence = Sequence(
    items=[
        Item(identifier=0, value=-1),
        Item(identifier=1, value=0),
        Item(identifier=2, value=1),
    ]
)

encoded = bstruct.encode(sequence)
decoded = bstruct.decode(Sequence, encoded)

assert decoded == sequence
```
