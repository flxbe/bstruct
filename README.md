# bstruct

[![ci](https://github.com/flxbe/bstruct/actions/workflows/ci.yml/badge.svg)](https://github.com/flxbe/bstruct/actions/workflows/ci.yml)
[![pypi](https://img.shields.io/pypi/v/bstruct)](https://pypi.org/project/bstruct/)

<!-- start elevator-pitch -->

Simple and efficient binary parsing using regular type annotations.
Supports easy fallback to Python's built-in `struct` library for maximum performance.

<!-- end elevator-pitch -->

## ⚠️ DISCLAIMER

This project is still a work in progress. Use at your own risk.

## Getting Started

<!-- start quickstart -->

```bash
pip install bstruct
```

```python
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
