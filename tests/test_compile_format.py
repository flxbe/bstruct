import bstruct


def test_should_correctly_compile_the_format_string() -> None:
    format = bstruct.compile_format(
        [
            bstruct.Encodings.u8,
            bstruct.Encodings.i8,
            bstruct.Encodings.u16,
            bstruct.Encodings.i16,
            bstruct.Encodings.u32,
            bstruct.Encodings.i32,
            bstruct.Encodings.u64,
            bstruct.Encodings.i64,
            bstruct.Bytes(size=16),
        ]
    )

    assert format == "BbHhIiQq16s"
