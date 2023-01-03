# Quickstart

```{testcode}
from typing import Annotated
from dataclasses import dataclass

import bstruct


@dataclass(slots=True)
class Measurement:
    timestamp: bstruct.u32  # shorthand for: Annotated[int, bstruct.Encodings.u32]
    values: Annotated[list[bstruct.u8], bstruct.Array(3)]


MeasurementEncoding = bstruct.derive(Measurement)


measurement = Measurement(
    timestamp=1672764049,
    values=[1, 2, 3],
)

encoded = MeasurementEncoding.encode(measurement)
decoded = MeasurementEncoding.decode(encoded)

assert decoded == measurement
```
