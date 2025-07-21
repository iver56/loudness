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
