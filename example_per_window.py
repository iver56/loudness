"""Example: Calculate percentage of audio above a loudness threshold."""
from pathlib import Path
import numpy as np
import soundfile
import loudness

TEST_FIXTURES_PATH = Path(__file__).parent / "test_fixtures"

audio, sr = soundfile.read(TEST_FIXTURES_PATH / "perfect-alley1.ogg", dtype=np.float32)
print(f"Audio duration: {len(audio) / sr:.2f} seconds")
print(f"Sample rate: {sr} Hz")
print()

window_duration = 0.5
lufs_per_window = loudness.loudness_per_window(audio, sr, window_duration_sec=window_duration)

print(f"Number of {window_duration}s windows: {len(lufs_per_window)}")
print(f"LUFS per window: {lufs_per_window}")
print()

threshold = -30
percentage_above = (lufs_per_window > threshold).mean() * 100

# Fully silent windows report -inf; keep only finite windows for the summary stats.
finite = lufs_per_window[np.isfinite(lufs_per_window)]

print(f"Percentage of windows above {threshold} LUFS: {percentage_above:.1f}%")
print(f"Min LUFS: {finite.min():.2f}")
print(f"Max LUFS: {finite.max():.2f}")
print(f"Mean LUFS: {finite.mean():.2f}")
print()

overall_lufs = loudness.integrated_loudness(audio, sr)
print(f"Overall integrated loudness: {overall_lufs:.2f} LUFS")
