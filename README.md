# loudness

A Python package (battle-tested C++ under the hood) for calculating integrated loudness (LUFS) with the ITU BS.1770 loudness algorithm. Useful for EBU R 128 compliance. Takes NumPy arrays as input (support mono and stereo/multichannel). Based on [libloudness](https://github.com/nomonosound/libloudness) (original implementation by Magnus Bro Kolstø, Nomono).

## Installation

[![PyPI version](https://img.shields.io/pypi/v/loudness.svg?style=flat)](https://pypi.org/project/loudness/)
![python 3.9, 3.10, 3.11, 3.12, 3.13](https://img.shields.io/badge/Python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-blue)
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

loudness is _significantly_ faster than the alternatives:

![Execution time comparison](images/execution_time_comparison.png)

## Dev setup

* Install CMake and a C++ compiler
* `pip install numpy pybind11 build scikit-build-core`
* `python -m build --wheel`
* Install the built wheel
* `pytest`
