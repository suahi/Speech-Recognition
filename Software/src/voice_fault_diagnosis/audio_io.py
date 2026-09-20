from __future__ import annotations

from dataclasses import asdict, dataclass
from math import gcd
from pathlib import Path
import re
import subprocess
from typing import Final

import numpy as np


TARGET_SAMPLE_RATE: Final = 16_000
SUPPORTED_AUDIO_SUFFIXES: Final = (".m4a", ".wav")


class AudioDecodeError(ValueError):
    """A selected audio file cannot be decoded into model input."""


@dataclass(frozen=True)
class AudioSourceInfo:
    format: str
    sample_rate: int
    channels: int
    frames: int
    duration_seconds: float
    decoder: str
    decoded_sample_rate: int = TARGET_SAMPLE_RATE
    decoded_channels: int = 1

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def is_supported_audio(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_AUDIO_SUFFIXES


def load_audio(path: str | Path, *, target_sample_rate: int = TARGET_SAMPLE_RATE) -> tuple[np.ndarray, AudioSourceInfo]:
    """Decode M4A/WAV to a finite mono float32 signal at the requested rate.

    M4A is decoded with the executable packaged by ``imageio-ffmpeg``. This
    keeps the desktop app independent from a separately installed FFmpeg.
    """

    source_path = Path(path).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"音频文件不存在：{source_path}")
    suffix = source_path.suffix.lower()
    if suffix not in SUPPORTED_AUDIO_SUFFIXES:
        raise AudioDecodeError("仅支持 M4A 或 WAV 音频文件。")
    if source_path.stat().st_size == 0:
        raise AudioDecodeError("音频文件为空，无法识别。")
    if suffix == ".wav":
        return _load_wav(source_path, target_sample_rate)
    return _load_m4a(source_path, target_sample_rate)


def inspect_audio(path: str | Path, *, target_sample_rate: int = TARGET_SAMPLE_RATE) -> AudioSourceInfo:
    """Decode once for a trustworthy validation and source description."""

    _, info = load_audio(path, target_sample_rate=target_sample_rate)
    return info


def _load_wav(source_path: Path, target_sample_rate: int) -> tuple[np.ndarray, AudioSourceInfo]:
    try:
        import soundfile as sf

        details = sf.info(str(source_path))
        sample_rate = int(details.samplerate)
        channels = int(details.channels)
        frames = int(details.frames)
        values, decoded_rate = sf.read(str(source_path), dtype="float32", always_2d=True)
    except Exception as exc:
        raise AudioDecodeError(f"WAV 文件损坏或格式不受支持：{source_path.name}") from exc
    if sample_rate <= 0 or channels <= 0 or frames <= 0 or values.size == 0:
        raise AudioDecodeError("WAV 文件为空，无法识别。")
    mono = np.mean(np.asarray(values, dtype=np.float32), axis=1)
    samples = _resample(mono, int(decoded_rate), target_sample_rate)
    return samples, AudioSourceInfo(
        format="WAV",
        sample_rate=sample_rate,
        channels=channels,
        frames=frames,
        duration_seconds=frames / float(sample_rate),
        decoder="soundfile",
        decoded_sample_rate=target_sample_rate,
    )


def _load_m4a(source_path: Path, target_sample_rate: int) -> tuple[np.ndarray, AudioSourceInfo]:
    executable = _bundled_ffmpeg()
    command = [
        executable,
        "-hide_banner",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(target_sample_rate),
        "-f",
        "f32le",
        "pipe:1",
    ]
    try:
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as exc:
        raise AudioDecodeError("内置 M4A 解码器无法启动，请重新安装 imageio-ffmpeg 依赖。") from exc
    stderr = completed.stderr.decode("utf-8", errors="replace")
    if completed.returncode != 0:
        detail = _compact_decoder_error(stderr)
        raise AudioDecodeError(f"M4A 文件无法解码：{source_path.name}。{detail}")
    raw = completed.stdout
    if len(raw) < 4:
        raise AudioDecodeError("M4A 文件为空或未包含可识别的音频帧。")
    samples = np.frombuffer(raw, dtype="<f4").astype(np.float32, copy=True)
    if not np.isfinite(samples).all():
        samples = np.nan_to_num(samples, nan=0.0, posinf=0.0, neginf=0.0)
    if samples.size == 0:
        raise AudioDecodeError("M4A 文件未解码出有效音频。")
    sample_rate, channels = _parse_m4a_stream_info(stderr)
    duration = samples.size / float(target_sample_rate)
    source_rate = sample_rate or target_sample_rate
    source_channels = channels or 1
    return np.clip(samples, -1.0, 1.0), AudioSourceInfo(
        format="M4A",
        sample_rate=source_rate,
        channels=source_channels,
        frames=max(1, int(round(duration * source_rate))),
        duration_seconds=duration,
        decoder="imageio-ffmpeg",
        decoded_sample_rate=target_sample_rate,
    )


def _bundled_ffmpeg() -> str:
    try:
        import imageio_ffmpeg

        executable = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise AudioDecodeError("缺少 M4A 解码器，请安装项目依赖 imageio-ffmpeg。") from exc
    if not executable or not Path(executable).is_file():
        raise AudioDecodeError("内置 M4A 解码器不可用，请重新安装 imageio-ffmpeg。")
    return executable


def _parse_m4a_stream_info(stderr: str) -> tuple[int | None, int | None]:
    match = re.search(r"Audio:.*?(\d+)\s*Hz,\s*(mono|stereo|\d+\s*channels)", stderr, re.IGNORECASE)
    if match is None:
        return None, None
    sample_rate = int(match.group(1))
    channel_text = match.group(2).lower().replace(" ", "")
    if channel_text == "mono":
        channels = 1
    elif channel_text == "stereo":
        channels = 2
    else:
        numeric = re.search(r"\d+", channel_text)
        channels = int(numeric.group()) if numeric else None
    return sample_rate, channels


def _compact_decoder_error(stderr: str) -> str:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    return " " + lines[-1][:180] if lines else ""


def _resample(samples: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if source_rate == target_rate:
        return np.clip(samples, -1.0, 1.0).astype(np.float32, copy=False)
    try:
        from scipy.signal import resample_poly

        divisor = gcd(source_rate, target_rate)
        output = resample_poly(samples, target_rate // divisor, source_rate // divisor)
    except Exception as exc:
        raise AudioDecodeError("无法将 WAV 重采样为模型所需的 16 kHz。") from exc
    return np.clip(np.asarray(output, dtype=np.float32), -1.0, 1.0)
