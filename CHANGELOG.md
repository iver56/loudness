# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* Add `loudness_window`, the ungated K-weighted loudness (LUFS) of a buffer
* Add `loudness_per_window` for ungated windowed loudness over time, with an
  optional `hop_duration_sec` for overlapping windows

## [0.2.0] - 2025-12-26

### Added

* Add support for Python 3.14

### Removed

* Remove support for Python 3.9

## [0.1.0] - 2025-07-21

Initial release
