from pathlib import Path

import numpy as np
import loudness
import pytest
import soundfile

TEST_FIXTURES_PATH = Path(__file__).resolve().parent.parent / "test_fixtures"


def test_stereo():
    audio, sample_rate = soundfile.read(
        TEST_FIXTURES_PATH / "perfect-alley1.ogg", dtype=np.float32
    )
    lufs = loudness.integrated_loudness(audio, sample_rate)
    print(f"{lufs:.2f} LUFS")


def test_stereo_wrong_dimension_ordering():
    samples_channels_first = np.zeros((2, 5000), dtype=np.float32)
    with pytest.raises(ValueError):
        loudness.integrated_loudness(samples_channels_first, 44100)
