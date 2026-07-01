from __future__ import annotations

import importlib.util

import numpy as np
import pytest

from voice_fault_diagnosis.inference.legacy_cnn import LegacyCnnEngine
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
