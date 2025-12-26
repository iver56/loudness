# loudness

A Python package (battle-tested C++ under the hood) for calculating integrated loudness (LUFS) with the ITU BS.1770 loudness algorithm. Useful for EBU R 128 compliance. Takes NumPy arrays as input (supports mono and stereo/multichannel). Based on [libloudness](https://github.com/nomonosound/libloudness) (original implementation by Magnus Bro Kolstø, Nomono).

## Installation

[![PyPI version](https://img.shields.io/pypi/v/loudness.svg?style=flat)](https://pypi.org/project/loudness/)
![python 3.10, 3.11, 3.12, 3.13, 3.14](https://img.shields.io/badge/Python-3.10%20|%203.11%20|%203.12%20|%203.13%20|%203.14-blue)
![os: Linux, macOS, Windows](https://img.shields.io/badge/OS-Linux%20%28arm%20%26%20x86--64%29%20|%20macOS%20%28arm%29%20|%20Windows%20%28x86--64%29-blue)

`pip install loudness`

## Usage example

```python
import soundfile as sf
import loudness

audio, sr = sf.read("audio.wav", dtype="float32")  # shape (samples, channels)
lufs = loudness.integrated_loudness(audio, sr)
print(f"{lufs:.2f} LUFS")
```

## Performance

loudness is significantly faster than the alternatives when running on CPU:

![Execution time comparison: loudness 0.1.0: 0.056s, pyebur128 0.1.1: 0.096s, torchaudio 2.8.0: 0.282, pyloudnorm 0.1.1: 0.293s, pyloudness 1.1.2: 0.581s](https://raw.githubusercontent.com/iver56/loudness/main/images/execution_time_comparison.png)

## Changelog

## [0.2.0] - 2025-12-26

### Added

* Add support for Python 3.14

### Removed

* Remove support for Python 3.9

For the complete changelog, go to [CHANGELOG.md](CHANGELOG.md)

## Development setup

* Install CMake and a C++ compiler
* `pip install numpy pybind11 build scikit-build-core`
* `python -m build --wheel`
* Install the built wheel
* `pytest`

## Alternatives (Python)

| Name                                                    | Github stars                                                                | License                                                                  | Last commit                                                                      |
|---------------------------------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [jaxloudnorm](https://github.com/boris-kuz/jaxloudnorm) | ![Github stars](https://img.shields.io/github/stars/boris-kuz/jaxloudnorm)  | ![License](https://img.shields.io/github/license/boris-kuz/jaxloudnorm)  | ![Last commit](https://img.shields.io/github/last-commit/boris-kuz/jaxloudnorm)  |
| [loudness](https://github.com/iver56/loudness)          | ![Github stars](https://img.shields.io/github/stars/iver56/loudness)        | ![License](https://img.shields.io/github/license/iver56/loudness)        | ![Last commit](https://img.shields.io/github/last-commit/iver56/loudness)        |
| [PALA](https://github.com/HBB-ThinkTank/PALA)           | ![Github stars](https://img.shields.io/github/stars/HBB-ThinkTank/PALA)     | ![License](https://img.shields.io/github/license/HBB-ThinkTank/PALA)     | ![Last commit](https://img.shields.io/github/last-commit/HBB-ThinkTank/PALA)     |
| [pyebur128](https://github.com/jodhus/pyebur128)        | ![Github stars](https://img.shields.io/github/stars/jodhus/pyebur128)       | ![License](https://img.shields.io/github/license/jodhus/pyebur128)       | ![Last commit](https://img.shields.io/github/last-commit/jodhus/pyebur128)       |
| [pyloudness](https://github.com/mr-rigden/pyloudness)   | ![Github stars](https://img.shields.io/github/stars/mr-rigden/pyloudness)   | ![License](https://img.shields.io/github/license/mr-rigden/pyloudness)   | ![Last commit](https://img.shields.io/github/last-commit/mr-rigden/pyloudness)   |
| [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) | ![Github stars](https://img.shields.io/github/stars/csteinmetz1/pyloudnorm) | ![License](https://img.shields.io/github/license/csteinmetz1/pyloudnorm) | ![Last commit](https://img.shields.io/github/last-commit/csteinmetz1/pyloudnorm) |
| [torchaudio](https://github.com/pytorch/audio)          | ![Github stars](https://img.shields.io/github/stars/pytorch/audio)          | ![License](https://img.shields.io/github/license/pytorch/audio)          | ![Last commit](https://img.shields.io/github/last-commit/pytorch/audio)          |
