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
    id: bstruct.u64
    value: bstruct.i32

class Sequence(bstruct.Struct):
    items: Annotated[list[Item], bstruct.Length(3)]

sequence = Sequence(
    items=[
        Item(id=0, value=-1),
        Item(id=1, value=0),
        Item(id=2, value=1),
    ]
)

encoded = bstruct.encode(sequence)
decoded = bstruct.decode(Sequence, encoded)

assert decoded == sequence
```

The helper type `bstruct.u64` is just an annotated int: `Annotated[int, Encodings.u64]`.
Both `id` and `value` are just plain `int` values.

<!-- end quickstart -->

See the [documentation](https://bstruct.readthedocs.io/) for more information.

## Benchmarks

Please see the source of the benchmarks in the `benchmarks` directory.
Feel free to create an issue or PR should there be a problem with the methodology.
The benchmarks where executed using Python 3.11.1 and
[construct](https://pypi.org/project/construct/) 2.10.68
on a MacBook Pro 2018 with a 2.3GHz i5 processor.

### `benchmarks/builtins.py`

| Name                 | decode   | encode   |
| -------------------- | -------- | -------- |
| struct               | 0.62 us  | 0.23 us  |
| bstruct              | 1.97 us  | 1.67 us  |
| construct            | 23.10 us | 22.11 us |
| construct (compiled) | 24.90 us | 25.43 us |

### `benchmarks/native_list.py`

| Name      | decode  | encode  |
| --------- | ------- | ------- |
| struct    | 0.18 us | 0.34 us |
| bstruct   | 2.03 us | 1.04 us |
| construct | 8.99 us | 8.34 us |

### `benchmarks/class_list.py`

| Name      | decode   | encode   |
| --------- | -------- | -------- |
| bstruct   | 7.28 us  | 5.19 us  |
| construct | 88.78 us | 84.85 us |

### `benchmarks/nested.py`

| Name      | decode   | encode   |
| --------- | -------- | -------- |
| bstruct   | 5.36 us  | 4.44 us  |
| construct | 70.48 us | 70.93 us |
