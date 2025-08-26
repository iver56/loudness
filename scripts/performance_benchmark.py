import importlib.metadata as metadata
import os
import time
from pathlib import Path

import loudness
import matplotlib.pyplot as plt
import numpy as np
import pyebur128
import pyloudness
import pyloudnorm
import torch
import torchaudio
from pyebur128 import MeasurementMode, R128State
from scipy.io.wavfile import write


class timer(object):
    """
    timer: A class used to measure the execution time of a block of code that is
    inside a "with" statement.

    Example:

    ```
    with timer("Count to 500000"):
        x = 0
        for i in range(500000):
            x += 1
        print(x)
    ```

    Will output:
    500000
    Count to 500000: 0.04 s

    Warning: The time resolution used here may be limited to 1 ms
    """

    def __init__(self, description="Execution time", verbose=True):
        self.description = description
        self.verbose = verbose
        self.execution_time = None

    def __enter__(self):
        self.t = time.time()
        return self

    def __exit__(self, type, value, traceback):
        self.execution_time = time.time() - self.t
        if self.verbose:
            print("{}: {:.3f} s".format(self.description, self.execution_time))


def get_version(pkg_name, module):
    try:
        return metadata.version(pkg_name)
    except metadata.PackageNotFoundError:
        return getattr(module, "__version__", "unknown")



if __name__ == "__main__":
    sample_rate = 48000
    audio = np.random.uniform(-1, 1, (48000 * 300,)).astype("float32")

    times = {}

    with timer("loudness") as t:
        lufs_loudness = loudness.integrated_loudness(audio, sample_rate)
    times["loudness"] = t.execution_time

    with timer("pyebur128") as t:
        state = R128State(1, sample_rate, MeasurementMode.MODE_I)
        state.add_frames(audio, audio.shape[-1])
        lufs_pyebur128 = pyebur128.get_loudness_global(state)
    times["pyebur128"] = t.execution_time

    with timer("pyloudnorm") as t:
        meter = pyloudnorm.Meter(sample_rate)
        lufs_pyloudnorm = meter.integrated_loudness(audio)
    times["pyloudnorm"] = t.execution_time

    with timer("pyloudness") as t:
        write("tmp.wav", sample_rate, audio)
        loudness_stats = pyloudness.get_loudness("tmp.wav")
        os.unlink("tmp.wav")
    times["pyloudness"] = t.execution_time

    with timer("torchaudio") as t:
        audio_tensor = torch.from_numpy(audio).unsqueeze(0)
        lufs_torchaudio = torchaudio.functional.loudness(audio_tensor, sample_rate)
    times["torchaudio"] = t.execution_time

    # Plot the results
    versions = {
        "loudness": get_version("loudness", loudness),
        "pyebur128": get_version("pyebur128", pyebur128),
        "pyloudnorm": get_version("pyloudnorm", pyloudnorm),
        "pyloudness": get_version("pyloudness", pyloudness),
        "torchaudio": (get_version("torchaudio", torchaudio)),
    }

    sorted_items = sorted(times.items(), key=lambda kv: kv[1])
    methods, execution_times = zip(*sorted_items)
    methods = [f"{method} {versions[method]}" for method in methods]

    fastest_time = min(execution_times)
    colors = []
    for time in execution_times:
        color = "#FFAF00" if time == fastest_time else "#A0A0A0"
        colors.append(color)

    plt.figure(figsize=(9, 5))
    bars = plt.bar(methods, execution_times, color=colors)
    plt.ylabel("Execution time (s)")
    plt.title("Execution times for 5 minutes of mono 48 kHz audio")

    for bar, time in zip(bars, execution_times):
        weight = "bold" if time == fastest_time else "normal"
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{time:.3f}s",
            ha="center",
            va="bottom",
            fontweight=weight,
        )

    plt.tight_layout()
    plot_file_path = (
        Path(__file__).resolve().parent.parent
        / "images"
        / "execution_time_comparison.png"
    )
    plt.savefig(plot_file_path, dpi=200)
