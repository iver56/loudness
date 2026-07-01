#include <cmath>
#include <string>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/warnings.h>

#include "loudness/meter.hpp"

namespace py = pybind11;
using Mode  = loudness::Mode;

constexpr double kMinDurationSec       = 0.4;
constexpr int    kMillisecondsInSecond = 1000;
/** EBU momentary integration time; windows below this are noisy and non-standard. */
constexpr double kMomentaryWindowSec = 0.4;

namespace {

    /**
     * Lightweight view over a validated NumPy audio buffer.
     *
     * data points at the first sample of a C-contiguous float32 array that is
     * either mono (shape (frames,)) or interleaved (shape (frames, channels)).
     * stride is the number of samples between consecutive frames.
     */
    struct AudioView {
        const float* data;
        std::size_t  frames;
        unsigned int channels;
        std::size_t  stride;
    };

    /** Validate dimensionality and return a view over the buffer. */
    AudioView viewAudio(const py::buffer_info& buf)
    {
        if (buf.ndim != 1 && buf.ndim != 2)
            throw std::runtime_error("samples must be 1D (mono) or 2D (samples, channels)");

        const auto channels = (buf.ndim == 2) ? static_cast<unsigned int>(buf.shape[1]) : 1U;
        return AudioView{.data     = static_cast<const float*>(buf.ptr),
                         .frames   = static_cast<std::size_t>(buf.shape[0]),
                         .channels = channels,
                         .stride   = (buf.ndim == 2) ? channels : 1U};
    }

    /** Convert a duration in seconds to whole milliseconds, rounding to nearest. */
    unsigned long toMilliseconds(double seconds)
    {
        return static_cast<unsigned long>(std::lround(seconds * kMillisecondsInSecond));
    }

    /** Number of frames spanned by window_ms, matching Meter::loudnessWindow(). */
    std::size_t windowFrames(unsigned long window_ms, int sample_rate)
    {
        return (static_cast<std::size_t>(sample_rate) * window_ms) / kMillisecondsInSecond;
    }

    /**
     * Emit a Python UserWarning when an analysis window is shorter than the EBU
     * momentary integration time. The measurement is still returned; the warning
     * only flags that sub-400 ms windows yield noisier, non-standard values.
     */
    void warnIfShortWindow(double window_sec, const char* what)
    {
        if (window_sec < kMomentaryWindowSec) {
            py::warnings::warn((std::string(what)
                                + " is shorter than the EBU momentary integration time (0.4 s); "
                                  "loudness values will be noisier and non-standard")
                                   .c_str(),
                               PyExc_UserWarning);
        }
    }

}  // namespace

/**
 * Compute integrated loudness (LUFS) for a mono or interleaved buffer.
 *
 * samples: float32 NumPy array with shape (samples,) or (samples, channels)
 * sample_rate: sample rate in Hz
 *
 * Returns LUFS as double
 */
double integrated_loudness(
    const py::array_t<float, py::array::c_style | py::array::forcecast>& samples,
    int                                                                  sample_rate)
{
    const AudioView audio = viewAudio(samples.request());

    const double duration_sec = static_cast<double>(audio.frames) / sample_rate;
    if (duration_sec < kMinDurationSec)
        throw py::value_error("audio too short: need at least " + std::to_string(kMinDurationSec * 1000)
                              + " ms, got " + std::to_string(duration_sec * 1000) + " ms");

    loudness::Meter<Mode::EBU_I | Mode::Histogram> meter(
        loudness::NumChannels(audio.channels), loudness::Samplerate(static_cast<long>(sample_rate)));

    meter.addFrames(audio.data, audio.frames);
    return meter.loudnessGlobal();
}

/**
 * Compute the ungated K-weighted loudness (LUFS) over an entire buffer.
 *
 * This is the BS.1770 "window" measure: the K-weighted mean square of every
 * sample, expressed in LUFS. Unlike integrated_loudness it applies no gating,
 * so the whole buffer contributes and adjacent measurements are directly
 * comparable. It is the building block used by loudness_per_window.
 *
 * samples: float32 NumPy array with shape (samples,) or (samples, channels)
 * sample_rate: sample rate in Hz
 *
 * Returns LUFS as double, or -inf for a fully silent buffer.
 */
double loudness_window(
    const py::array_t<float, py::array::c_style | py::array::forcecast>& samples,
    int                                                                  sample_rate)
{
    const AudioView audio = viewAudio(samples.request());

    const unsigned long window_ms = toMilliseconds(static_cast<double>(audio.frames) / sample_rate);
    if (window_ms == 0)
        throw py::value_error("audio too short: buffer rounds to 0 ms");

    warnIfShortWindow(static_cast<double>(audio.frames) / sample_rate, "samples duration");

    loudness::Meter<Mode::EBU_M> meter(loudness::NumChannels(audio.channels),
                                       loudness::Samplerate(static_cast<long>(sample_rate)));
    meter.setMaxWindow(window_ms);
    meter.addFrames(audio.data, audio.frames);
    return meter.loudnessWindow(window_ms);
}

/**
 * Compute the ungated loudness (LUFS) for a sliding window across the audio.
 *
 * The K-filter runs continuously over the whole signal (as a hardware meter
 * would), and loudnessWindow() is sampled once per hop. With the default hop
 * the windows tile the audio without overlap; a smaller hop yields overlapping
 * windows. Every value is ungated, so windows are directly comparable.
 *
 * samples: float32 NumPy array with shape (samples,) or (samples, channels)
 * sample_rate: sample rate in Hz
 * window_duration_sec: duration of each window in seconds
 * hop_duration_sec: step between window starts in seconds; <= 0 means "equal to
 *                   window_duration_sec" (non-overlapping windows)
 *
 * Returns NumPy array of LUFS values, one per window (-inf for silent windows).
 */
py::array_t<double> loudness_per_window(
    const py::array_t<float, py::array::c_style | py::array::forcecast>& samples,
    int                                                                  sample_rate,
    double                                                               window_duration_sec,
    double                                                               hop_duration_sec)
{
    const AudioView audio = viewAudio(samples.request());

    if (window_duration_sec <= 0.0)
        throw py::value_error("window_duration_sec must be positive");
    if (hop_duration_sec <= 0.0)
        hop_duration_sec = window_duration_sec;

    warnIfShortWindow(window_duration_sec, "window_duration_sec");

    const unsigned long window_ms   = toMilliseconds(window_duration_sec);
    const unsigned long hop_ms      = toMilliseconds(hop_duration_sec);
    const std::size_t   window_span = windowFrames(window_ms, sample_rate);
    const std::size_t   hop_span    = windowFrames(hop_ms, sample_rate);

    if (window_ms == 0 || window_span == 0)
        throw py::value_error("window_duration_sec too short to span a sample");
    if (hop_ms == 0 || hop_span == 0)
        throw py::value_error("hop_duration_sec too short to span a sample");

    if (audio.frames < window_span)
        throw py::value_error("audio too short: need at least "
                              + std::to_string(window_duration_sec * 1000) + " ms, got "
                              + std::to_string(static_cast<double>(audio.frames) / sample_rate * 1000) + " ms");

    const std::size_t num_windows = (audio.frames - window_span) / hop_span + 1;

    loudness::Meter<Mode::EBU_M> meter(loudness::NumChannels(audio.channels),
                                       loudness::Samplerate(static_cast<long>(sample_rate)));
    meter.setMaxWindow(window_ms);

    std::vector<double> lufs_values;
    lufs_values.reserve(num_windows);

    std::size_t fed = 0;
    for (std::size_t i = 0; i < num_windows; ++i) {
        // Feed audio up to the end of window i, then sample the trailing window.
        const std::size_t window_end = i * hop_span + window_span;
        meter.addFrames(audio.data + fed * audio.stride, window_end - fed);
        fed = window_end;
        lufs_values.push_back(meter.loudnessWindow(window_ms));
    }

    return py::array_t<double>(lufs_values.size(), lufs_values.data());
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

    m.def("loudness_window", &loudness_window,
          py::arg("samples"), py::arg("sample_rate"),
          R"pbdoc(
Compute the ungated K-weighted loudness (LUFS) over an entire buffer.

This is the BS.1770 windowed loudness measure: the K-weighted mean square of
every sample, expressed in LUFS. Unlike :func:`integrated_loudness` no gating is
applied, so the whole buffer contributes to the result. Pass a short slice to
measure a single window, or use :func:`loudness_per_window` to sweep a longer
signal.

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
    Ungated loudness in LUFS. ``-inf`` for a fully silent buffer.

Warns
-----
UserWarning
    If the buffer is shorter than the EBU momentary integration time (0.4 s),
    where the loudness value is noisier and non-standard.

Raises
------
ValueError
    If the buffer is empty, has too many channels (>64), or the sample_rate is
    outside the supported range (16-2822400 Hz).
)pbdoc");

    m.def("loudness_per_window", &loudness_per_window,
          py::arg("samples"), py::arg("sample_rate"), py::arg("window_duration_sec"),
          py::arg("hop_duration_sec") = 0.0,
          R"pbdoc(
Compute the ungated loudness (LUFS) for a sliding window across the audio.

The K-filter runs continuously over the whole signal, as a hardware loudness
meter would, and the windowed loudness is sampled once per hop. Every value is
ungated (see :func:`loudness_window`), so windows are directly comparable and a
threshold statistic such as "percentage of time above -30 LUFS" is meaningful.

Parameters
----------
samples: numpy.ndarray float32
    Mono 1D array (n_samples) or
    interleaved 2D array (n_samples, n_channels).
sample_rate: int
    Sample rate in hertz.
window_duration_sec: float
    Duration of each window in seconds. 0.4 s matches the EBU momentary
    integration time; shorter windows are permitted but emit a UserWarning
    because their loudness values are noisier and non-standard.
hop_duration_sec: float, optional
    Step between window starts in seconds. Defaults to window_duration_sec,
    giving non-overlapping windows; a smaller hop yields overlapping windows.

Returns
-------
numpy.ndarray float64
    Ungated loudness in LUFS, one value per window. ``-inf`` for silent windows.
    Window and hop durations are quantised to whole milliseconds, and audio in a
    trailing partial window is discarded.

Raises
------
ValueError
    If window_duration_sec or hop_duration_sec is non-positive, the audio is too
    short for a single window, the buffer has too many channels (>64), or the
    sample_rate is outside the supported range (16-2822400 Hz).

Examples
--------
>>> import soundfile as sf
>>> import loudness
>>> audio, sr = sf.read("audio.wav", dtype="float32")
>>> lufs_per_window = loudness.loudness_per_window(audio, sr, window_duration_sec=0.5)
>>> percentage_loud = (lufs_per_window > -30).mean() * 100
>>> print(f"{percentage_loud:.1f}% of windows are above -30 LUFS")
)pbdoc");
}
