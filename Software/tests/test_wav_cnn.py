from __future__ import annotations

import importlib.util
from pathlib import Path
import wave

import numpy as np
import pytest

from voice_fault_diagnosis.config import load_pc_config
from voice_fault_diagnosis.inference.wav_cnn import FIXED_FRAMES, N_COEFFICIENTS, WavCnnEngine, extract_wav_features


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("torch") is None or importlib.util.find_spec("librosa") is None,
    reason="torch and librosa are required for WAV CNN inference",
)


@pytest.mark.parametrize(("sample_rate", "channels"), [(8000, 1), (44100, 2)])
def test_wav_features_resample_and_mix_to_mono(tmp_path, sample_rate, channels) -> None:
    wav_path = tmp_path / "input.wav"
    _write_test_wav(wav_path, sample_rate, channels)

    features, source_samples = extract_wav_features(wav_path)

    assert source_samples == 16000
    assert features.shape == (5, N_COEFFICIENTS, FIXED_FRAMES)


def test_six_class_model_prediction(tmp_path) -> None:
    wav_path = tmp_path / "capture.wav"
    _write_test_wav(wav_path, 50000, 1)
    config = load_pc_config()

    result = WavCnnEngine(config.model).predict(wav_path)

    assert len(result.probabilities) == 6
    assert result.label in config.model.labels
    assert 0.0 <= result.confidence <= 1.0
    assert result.top_k[0]["label"] == result.label
    assert result.metadata["target_sample_rate"] == 16000


def _write_test_wav(path: Path, sample_rate: int, channels: int) -> None:
    time_axis = np.arange(sample_rate, dtype=np.float32) / sample_rate
    mono = (0.1 * np.sin(2.0 * np.pi * 1000.0 * time_axis) * 32767.0).astype("<i2")
    pcm = np.column_stack((mono, mono // 2)).astype("<i2").reshape(-1) if channels == 2 else mono
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
