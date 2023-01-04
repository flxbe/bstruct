# bstruct

[![ci](https://github.com/flxbe/bstruct/actions/workflows/ci.yml/badge.svg)](https://github.com/flxbe/bstruct/actions/workflows/ci.yml)
[![pypi](https://img.shields.io/pypi/v/bstruct)](https://pypi.org/project/bstruct/)
[![python](https://img.shields.io/pypi/pyversions/bstruct)](https://img.shields.io/pypi/pyversions/bstruct)

<!-- start elevator-pitch -->

Simple and efficient binary parsing using type annotations.
Supports easy fallback to Python's built-in `struct` library for maximum performance.

<!-- end elevator-pitch -->

## Getting Started

<!-- start quickstart -->

```bash
pip install bstruct
```

```python
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

<!-- end quickstart -->

See the [documentation](https://bstruct.readthedocs.io/) for more information.

## Benchmarks

Please see the source of the benchmarks in the `benchmarks` directory.
Feel free to create an issue or PR should there be a problem with the methodology.
The benchmarks where executed with
[pyperf](https://github.com/psf/pyperf)
using Python 3.11.1 and
[construct](https://pypi.org/project/construct/) 2.10.68
on a MacBook Pro 2018 with a 2.3GHz i5 processor.

### `benchmarks/builtins.py`

| Name                 | decode  | encode  |
| -------------------- | ------- | ------- |
| struct               | 0.56 us | 0.22 us |
| bstruct              | 2.58 us | 1.68 us |
| construct (compiled) | 9.31 us | 9.85 us |

### `benchmarks/native_list.py`

| Name                 | decode  | encode  |
| -------------------- | ------- | ------- |
| struct               | 0.16 us | 0.32 us |
| bstruct              | 2.46 us | 0.97 us |
| construct (compiled) | 4.02 us | 6.86 us |

### `benchmarks/class_list.py`

| Name                 | decode  | encode  |
| -------------------- | ------- | ------- |
| bstruct              | 8.54 us | 5.13 us |
| construct (compiled) | 34.4 us | 38.6 us |

### `benchmarks/nested.py`

| Name                 | decode  | encode  |
| -------------------- | ------- | ------- |
| bstruct              | 6.30 us | 4.47 us |
| construct (compiled) | 29.2 us | 29.2 us |

## Issues and Contributing

I am very happy to receive any kind of feedback or contribution.
Just open an issue and let me know.
