from pathlib import Path

import numpy as np
import loudness
import pytest
import soundfile

TEST_FIXTURES_PATH = Path(__file__).resolve().parent.parent / "test_fixtures"


def test_mono():
    audio, sample_rate = soundfile.read(
        TEST_FIXTURES_PATH / "p286_011.wav", dtype=np.float32
    )
    assert audio.ndim == 1
    lufs = loudness.integrated_loudness(audio, sample_rate)
    assert lufs == pytest.approx(-23.05, abs=0.1)


def test_stereo():
    audio, sample_rate = soundfile.read(
        TEST_FIXTURES_PATH / "perfect-alley1.ogg", dtype=np.float32
    )
    lufs = loudness.integrated_loudness(audio, sample_rate)
    assert lufs == pytest.approx(-20.82, abs=0.1)


def test_stereo_wrong_dimension_ordering():
    samples_channels_first = np.zeros((2, 5000), dtype=np.float32)
    with pytest.raises(ValueError):
        loudness.integrated_loudness(samples_channels_first, 44100)


def test_too_low_sample_rate():
    samples = np.zeros((5000,), dtype=np.float32)
    with pytest.raises(ValueError):
        loudness.integrated_loudness(samples, 4)


def test_too_high_sample_rate():
    samples = np.zeros((1_250_000,), dtype=np.float32)
    with pytest.raises(ValueError):
        loudness.integrated_loudness(samples, 3_000_000)


def test_too_short_audio_duration():
    sample_rate = 44100
    duration = 0.35
    num_samples = int(sample_rate * duration)
    samples = np.ones((num_samples,), dtype=np.float32)
    with pytest.raises(ValueError):
        loudness.integrated_loudness(samples, 44100)


def test_too_many_channels():
    samples = np.zeros((25000, 65), dtype=np.float32)
    with pytest.raises(ValueError):
        loudness.integrated_loudness(samples, 44100)


def _expected_num_windows(num_frames, sample_rate, window_duration, hop_duration):
    """Mirror the C++ window count: ms-quantised windows, trailing partial dropped."""
    window_frames = round(window_duration * 1000) * sample_rate // 1000
    hop_frames = round(hop_duration * 1000) * sample_rate // 1000
    return (num_frames - window_frames) // hop_frames + 1


def test_loudness_per_window_mono():
    audio, sample_rate = soundfile.read(
        TEST_FIXTURES_PATH / "p286_011.wav", dtype=np.float32
    )
    assert audio.ndim == 1

    window_duration = 0.5
    lufs_per_window = loudness.loudness_per_window(audio, sample_rate, window_duration)

    assert isinstance(lufs_per_window, np.ndarray)
    assert lufs_per_window.dtype == np.float64

    expected = _expected_num_windows(len(audio), sample_rate, window_duration, window_duration)
    assert len(lufs_per_window) == expected

    # This recording has signal throughout, so every window is finite and no
    # window exceeds digital full scale (0 LUFS).
    assert np.all(np.isfinite(lufs_per_window))
    assert np.all(lufs_per_window <= 0.0)


def test_loudness_per_window_stereo():
    audio, sample_rate = soundfile.read(
        TEST_FIXTURES_PATH / "perfect-alley1.ogg", dtype=np.float32
    )

    window_duration = 1.0
    lufs_per_window = loudness.loudness_per_window(audio, sample_rate, window_duration)

    assert isinstance(lufs_per_window, np.ndarray)
    expected = _expected_num_windows(len(audio), sample_rate, window_duration, window_duration)
    assert len(lufs_per_window) == expected


def test_loudness_per_window_matches_single_window():
    audio, sample_rate = soundfile.read(
        TEST_FIXTURES_PATH / "p286_011.wav", dtype=np.float32
    )

    window_duration = 0.5
    lufs_per_window = loudness.loudness_per_window(audio, sample_rate, window_duration)

    # The first window starts from a fresh filter state, exactly like measuring
    # that leading slice on its own with loudness_window().
    window_frames = round(window_duration * 1000) * sample_rate // 1000
    single = loudness.loudness_window(audio[:window_frames], sample_rate)
    assert lufs_per_window[0] == pytest.approx(single)


def test_loudness_per_window_overlap():
    audio, sample_rate = soundfile.read(
        TEST_FIXTURES_PATH / "p286_011.wav", dtype=np.float32
    )

    non_overlapping = loudness.loudness_per_window(audio, sample_rate, 0.5)
    overlapping = loudness.loudness_per_window(audio, sample_rate, 0.5, hop_duration_sec=0.25)

    assert len(overlapping) > len(non_overlapping)
    # A window start shared by both sweeps yields the same measurement.
    assert overlapping[0] == pytest.approx(non_overlapping[0])


def test_loudness_per_window_silence_is_neg_inf():
    sample_rate = 48000
    samples = np.zeros((sample_rate * 2,), dtype=np.float32)
    lufs_per_window = loudness.loudness_per_window(samples, sample_rate, 0.5)
    assert np.all(np.isneginf(lufs_per_window))


def test_loudness_per_window_too_short():
    sample_rate = 44100
    duration = 0.5
    num_samples = int(sample_rate * duration)
    samples = np.ones((num_samples,), dtype=np.float32)

    window_duration = 1.0
    with pytest.raises(ValueError):
        loudness.loudness_per_window(samples, sample_rate, window_duration)


def test_loudness_per_window_nonpositive_window():
    sample_rate = 44100
    samples = np.ones((sample_rate * 2,), dtype=np.float32)

    with pytest.raises(ValueError):
        loudness.loudness_per_window(samples, sample_rate, window_duration_sec=0.0)


def test_loudness_per_window_short_window_warns():
    sample_rate = 48000
    samples = np.ones((sample_rate * 2,), dtype=np.float32)

    # Windows below the EBU momentary integration time are allowed but noisy, so
    # they warn instead of failing, and still return a value per window.
    with pytest.warns(UserWarning):
        lufs_per_window = loudness.loudness_per_window(samples, sample_rate, 0.1)
    assert len(lufs_per_window) > 0


def test_loudness_per_window_normal_window_does_not_warn(recwarn):
    sample_rate = 48000
    samples = np.ones((sample_rate * 2,), dtype=np.float32)

    loudness.loudness_per_window(samples, sample_rate, 0.5)
    assert len(recwarn) == 0


def test_loudness_window_matches_integrated_for_stationary_signal():
    sample_rate = 48000
    t = np.arange(sample_rate * 3) / sample_rate
    sine = (0.5 * np.sin(2 * np.pi * 997 * t)).astype(np.float32)

    # For a stationary signal every gating block has equal energy, so gating
    # removes nothing and the ungated window loudness matches integrated loudness.
    assert loudness.loudness_window(sine, sample_rate) == pytest.approx(
        loudness.integrated_loudness(sine, sample_rate), abs=0.1
    )


def test_loudness_window_stereo_is_mono_plus_3db():
    sample_rate = 48000
    t = np.arange(sample_rate * 2) / sample_rate
    sine = (0.5 * np.sin(2 * np.pi * 997 * t)).astype(np.float32)

    mono = loudness.loudness_window(sine, sample_rate)
    dual_mono = loudness.loudness_window(np.stack([sine, sine], axis=1), sample_rate)
    assert dual_mono - mono == pytest.approx(3.01, abs=0.05)


def test_loudness_window_silence_is_neg_inf():
    sample_rate = 48000
    samples = np.zeros((sample_rate,), dtype=np.float32)
    assert np.isneginf(loudness.loudness_window(samples, sample_rate))


def test_loudness_window_short_buffer_warns():
    sample_rate = 48000
    samples = np.ones((int(sample_rate * 0.2),), dtype=np.float32)

    with pytest.warns(UserWarning):
        loudness.loudness_window(samples, sample_rate)
