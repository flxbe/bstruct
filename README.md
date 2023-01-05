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


@dataclass
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

| Name                 | decode  | encode   |
| -------------------- | ------- | -------- |
| struct               | 0.54 us | 0.23 us  |
| bstruct              | 2.51 us | 1.64 us  |
| construct (compiled) | 9.49 us | 10.00 us |

### `benchmarks/native_list.py`

| Name                 | decode  | encode  |
| -------------------- | ------- | ------- |
| struct               | 0.17 us | 0.33 us |
| bstruct              | 1.70 us | 0.59 us |
| construct (compiled) | 4.04 us | 6.61 us |

### `benchmarks/class_list.py`

| Name                 | decode  | encode  |
| -------------------- | ------- | ------- |
| bstruct              | 7.37 us | 4.81 us |
| construct (compiled) | 34.5 us | 36.6 us |

### `benchmarks/nested.py`

| Name                 | decode  | encode  |
| -------------------- | ------- | ------- |
| bstruct              | 6.05 us | 4.42 us |
| construct (compiled) | 27.6 us | 29.5 us |

## Issues and Contributing

I am very happy to receive any kind of feedback or contribution.
Just open an issue and let me know.
