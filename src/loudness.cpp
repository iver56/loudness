#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "loudness/meter.hpp"

namespace py = pybind11;
using Mode  = loudness::Mode;

constexpr double kMinDurationSec = 0.4;

/**
 * Compute integrated loudness (LUFS) for a mono or interleaved buffer.
 *
 * samples: float32 NumPy array with shape (samples,) or (samples, channels)
 * sample_rate: sample rate in Hz
 *
 * Returns LUFS as double
 */
double integrated_loudness(
    const py::array_t<float,
        py::array::c_style | py::array::forcecast> &samples,
    int sample_rate)
{
    const auto buf = samples.request();

    if (buf.ndim != 1 && buf.ndim != 2)
        throw std::runtime_error(
            "samples must be 1D (mono) or 2D (samples, channels)");

    const std::size_t frames   = static_cast<std::size_t>(buf.shape[0]);
    const unsigned int channels =
        (buf.ndim == 2) ? static_cast<unsigned int>(buf.shape[1]) : 1U;

    const double duration_sec = static_cast<double>(frames) / sample_rate;
    if (duration_sec < kMinDurationSec)
        throw py::value_error("audio too short: need at least "
                              + std::to_string(kMinDurationSec*1000) + " ms, got "
                              + std::to_string(duration_sec*1000) + " ms");

    const float *data = static_cast<const float *>(buf.ptr);

    loudness::Meter<Mode::EBU_I | Mode::Histogram> meter(
        loudness::NumChannels(channels),
        loudness::Samplerate(static_cast<long>(sample_rate)));

    meter.addFrames(data, frames);
    return meter.loudnessGlobal();
}

PYBIND11_MODULE(loudness, m)
{
    m.doc() = "Python bindings for libloudness, for calculating integrated loudness in LUFS (ITU BS.1770 / EBU R 128).";
    m.def("integrated_loudness", &integrated_loudness,
          py::arg("samples"), py::arg("sample_rate"),
          R"pbdoc(
Compute EBU‑R128 integrated loudness (LUFS).

Parameters
----------
samples: numpy.ndarray float32
    Mono 1D array (n_samples) or
    interleaved 2D array (n_samples, n_channels).
sample_rate: int
    Sample rate in hertz.

Returns
-------
float
    Integrated loudness in LUFS.

Raises
------
ValueError
    If the audio is too short (<400 ms), has too many channels (>64), or the sample_rate is outside the supported range (16-2822400 Hz).
)pbdoc");
}
