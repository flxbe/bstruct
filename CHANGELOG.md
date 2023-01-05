# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2022-01-05

### Added

- Introduce `bstruct.derive` to create encodings for generic type expressions.
- Add `read`, `read_many`, `write`, and `write_many`.
- Make `CustomEncoding` public.
- Add support for Python 3.9.
- Improve error messages.

### Removed

- Remove `bstruct.patch`.
- Remove native support for `NewType` in favor for Python 3.9.

## [0.4.0] - 2022-12-31

### Added

- Support for `byteorder='big'`
- Handle `struct.error`

## [0.3.0] - 2022-12-18

### Changed

- Use `bstruct.Struct` baseclass instead of the decorator `bstruct.derive`

[unreleased]: https://github.com/flxbe/bstruct/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/flxbe/bstruct/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/flxbe/bstruct/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/flxbe/bstruct/compare/v0.2.0...v0.3.0
