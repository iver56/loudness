# loudness

A Python lib (C++ under the hood) for calculating loudness (in LUFS) with the ITU BS.1770 loudness algorithm. Useful for EBU R 128 compliance. Based on [libloudness](https://github.com/nomonosound/libloudness) (original implementation by Magnus Bro Kolstø, Nomono).

## Installation

`pip install loudness`

## Usage example

```python
import soundfile as sf
import loudness

audio, sr = sf.read("audio.wav", dtype="float32")  # shape (samples, channels)
lufs = loudness.integrated_loudness(audio, sr)
print(f"{lufs:.2f} LUFS")
```

## Dev setup

* Install CMake and a C++ compiler
* `pip install numpy pybind11 build scikit-build-core`
* `python -m build --wheel`
* `pytest`
