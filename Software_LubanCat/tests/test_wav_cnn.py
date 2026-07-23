from __future__ import annotations

import importlib.util

import numpy as np
import pytest

from voice_fault_diagnosis.audio_io import save_wav
from voice_fault_diagnosis.config import load_light_config
from voice_fault_diagnosis.inference.wav_cnn import FIXED_FRAMES, N_COEFFICIENTS, WavCnnEngine, extract_wav_features


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("torch") is None or importlib.util.find_spec("librosa") is None,
    reason="torch and librosa are required for WAV CNN inference",
)


def test_reference_wav_feature_shape_and_six_class_prediction(tmp_path) -> None:
    sample_rate = 50000
    seconds = 1.0
    time_axis = np.arange(int(sample_rate * seconds), dtype=np.float32) / sample_rate
    wav_path = tmp_path / "capture.wav"
    save_wav(wav_path, 0.1 * np.sin(2.0 * np.pi * 1000.0 * time_axis), sample_rate)

    features, source_samples = extract_wav_features(wav_path)
    result = WavCnnEngine(load_light_config().model).predict(wav_path)

    assert source_samples == 16000
    assert features.shape == (5, N_COEFFICIENTS, FIXED_FRAMES)
    assert len(result.probabilities) == 6
    assert result.label in load_light_config().model.labels
    assert 0.0 <= result.confidence <= 1.0
    assert result.top_k[0]["label"] == result.label
    assert result.metadata["target_sample_rate"] == 16000
