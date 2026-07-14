from __future__ import annotations

import importlib.util
import pickle

import numpy as np
import pytest

from voice_fault_diagnosis.inference.legacy_cnn import LegacyCnnEngine, extract_legacy_features
from voice_fault_diagnosis.legacy_format import voltage_to_legacy_bytes


@pytest.mark.skipif(
    importlib.util.find_spec("torch") is None or importlib.util.find_spec("librosa") is None,
    reason="torch and librosa are required for legacy CNN inference",
)
def test_legacy_cnn_outputs_ten_probabilities() -> None:
    sample_count = 50000
    t = np.arange(sample_count, dtype=np.float32) / 50000.0
    voltage = 0.2 * np.sin(2 * np.pi * 1000.0 * t)
    legacy_input = voltage_to_legacy_bytes(voltage)
    engine = LegacyCnnEngine()

    result = engine.predict(legacy_input)

    assert len(result.probabilities) == 10
    assert 0 <= result.class_index < 10
    assert 0.0 <= result.confidence <= 1.0
    assert result.top_k
    assert "timings" in result.metadata


@pytest.mark.skipif(
    importlib.util.find_spec("torch") is None or importlib.util.find_spec("librosa") is None,
    reason="torch and librosa are required for legacy CNN inference",
)
def test_legacy_cnn_prepare_is_idempotent(tmp_path, monkeypatch) -> None:
    (tmp_path / "manifest.json").write_text(
        """
        {
          "name": "fake",
          "model_path": "model.pt",
          "mean_std_path": "mean_std.pkl",
          "labels_path": "labels.json",
          "num_classes": 10
        }
        """,
        encoding="utf-8",
    )
    (tmp_path / "labels.json").write_text('["class_0"]', encoding="utf-8")
    with (tmp_path / "mean_std.pkl").open("wb") as handle:
        pickle.dump({"mean": np.zeros((36, 5), dtype=np.float32), "std": np.ones((36, 5), dtype=np.float32)}, handle)

    import torch

    calls = {"load": 0}

    class FakeModel:
        def eval(self) -> None:
            return None

    def fake_load(*args, **kwargs):
        calls["load"] += 1
        return FakeModel()

    monkeypatch.setattr(torch, "load", fake_load)

    engine = LegacyCnnEngine(model_dir=tmp_path)
    engine.prepare()
    engine.prepare()

    assert calls["load"] == 1


@pytest.mark.skipif(
    importlib.util.find_spec("librosa") is None,
    reason="librosa is required for legacy feature extraction",
)
def test_extract_legacy_features_computes_stft_once(monkeypatch) -> None:
    import librosa

    original_stft = librosa.stft
    calls = {"stft": 0}

    def counting_stft(*args, **kwargs):
        calls["stft"] += 1
        return original_stft(*args, **kwargs)

    monkeypatch.setattr(librosa, "stft", counting_stft)
    sample_count = 5000
    t = np.arange(sample_count, dtype=np.float32) / 50000.0
    voltage = 0.2 * np.sin(2 * np.pi * 1000.0 * t)
    legacy_input = voltage_to_legacy_bytes(voltage)

    features, raw_samples, real, imaginary = extract_legacy_features(legacy_input)

    assert features.shape == (36, 5)
    assert raw_samples.size == sample_count
    assert real.size == imaginary.size
    assert calls["stft"] == 1
