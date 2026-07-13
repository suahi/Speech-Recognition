from __future__ import annotations

from pathlib import Path
import wave

import numpy as np


def voltage_to_audio(voltage: np.ndarray, input_range_volts: float) -> np.ndarray:
    arr = np.asarray(voltage, dtype=np.float32)
    if input_range_volts <= 0:
        raise ValueError("input_range_volts must be positive")
    return np.clip(arr / float(input_range_volts), -1.0, 1.0).astype(np.float32)


def save_wav(path: str | Path, audio: np.ndarray, sample_rate: int) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(audio, dtype=np.float32)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    pcm = (np.clip(arr, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(pcm.tobytes())
