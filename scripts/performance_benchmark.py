import os
import time

import loudness
import numpy as np
import pyebur128
import pyloudness
import pyloudnorm
from pyebur128 import R128State, MeasurementMode
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


if __name__ == "__main__":
    sample_rate = 48000
    audio = np.random.uniform(-1, 1, (48000 * 3600,)).astype("float32")

    with timer("loudness"):
        lufs_loudness = loudness.integrated_loudness(audio, sample_rate)

    with timer("pyebur128"):
        state = R128State(1, sample_rate, MeasurementMode.MODE_I)
        state.add_frames(audio, audio.shape[-1])
        lufs_pyebur128 = pyebur128.get_loudness_global(state)

    with timer("pyloudnorm"):
        meter = pyloudnorm.Meter(sample_rate)
        lufs_pyloudnorm = meter.integrated_loudness(audio)

    with timer("pyloudness"):
        write("tmp.wav", sample_rate, audio)
        loudness_stats = pyloudness.get_loudness("tmp.wav")
        os.unlink("tmp.wav")
