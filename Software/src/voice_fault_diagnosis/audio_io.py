from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import wave

import numpy as np


@dataclass(frozen=True)
class WavSourceInfo:
    sample_rate: int
    channels: int
    frames: int
    duration_seconds: float


def inspect_wav(path: str | Path) -> WavSourceInfo:
    source_path = Path(path).resolve()
    if source_path.suffix.lower() != ".wav":
        raise ValueError("仅支持 WAV 文件。")
    if not source_path.is_file():
        raise FileNotFoundError(f"WAV 文件不存在：{source_path}")
    try:
        import soundfile as sf

        details = sf.info(str(source_path))
    except Exception as exc:
        raise ValueError(f"WAV 文件损坏或格式不受支持：{source_path}") from exc
    sample_rate = int(details.samplerate)
    channels = int(details.channels)
    frames = int(details.frames)
    if sample_rate <= 0 or frames <= 0:
        raise ValueError("WAV 文件为空，无法识别。")
    if channels not in (1, 2):
        raise ValueError(f"WAV 必须是单声道或双声道，当前为 {channels} 声道。")
    return WavSourceInfo(
        sample_rate=sample_rate,
        channels=channels,
        frames=frames,
        duration_seconds=frames / float(sample_rate),
    )


def load_wav_preview(path: str | Path, *, max_seconds: float = 0.2) -> tuple[np.ndarray, WavSourceInfo]:
    source_path = Path(path).resolve()
    info = inspect_wav(source_path)
    frame_limit = max(1, min(info.frames, int(info.sample_rate * max_seconds)))
    try:
        import soundfile as sf

        values, _ = sf.read(str(source_path), frames=frame_limit, dtype="float32", always_2d=True)
    except Exception as exc:
        raise ValueError(f"无法读取 WAV 波形：{source_path}") from exc
    mono = np.mean(np.asarray(values, dtype=np.float32), axis=1)
    return mono, info


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
