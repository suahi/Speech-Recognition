from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from voice_fault_diagnosis.config import BearingConfigError, load_bearing_config
from voice_fault_diagnosis.inference.bearing import BearingDiagnosticEngine, estimate_remaining_life
from voice_fault_diagnosis.models import CLASS_IDS
from voice_fault_diagnosis.paths import BEARING_CONFIG_PATH, BEARING_MODEL_DIR, SOFTWARE_ROOT


def test_default_config_resolves_project_relative_model_paths() -> None:
    config = load_bearing_config()
    assert config.source_path == BEARING_CONFIG_PATH.resolve()
    assert config.target_sample_rate == 16_000
    assert config.segment_seconds == 5.0
    for path in (
        config.model.classifier_path,
        config.model.feature_config_path,
    ):
        assert path.is_file()
        assert path.is_relative_to(SOFTWARE_ROOT)


def test_config_rejects_outside_project_model_path(tmp_path: Path) -> None:
    config_data = json.loads(BEARING_CONFIG_PATH.read_text(encoding="utf-8"))
    config_data["model"]["classifier_path"] = "C:\\outside-project\\outside.joblib"
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(config_data), encoding="utf-8")
    with pytest.raises(BearingConfigError, match="项目目录"):
        load_bearing_config(path)


def test_training_outputs_and_file_level_test_split_are_committed() -> None:
    metrics = json.loads((BEARING_MODEL_DIR / "training_metrics.json").read_text(encoding="utf-8"))
    manifest = (BEARING_MODEL_DIR / "test_manifest.csv").read_text(encoding="utf-8")
    assert (BEARING_MODEL_DIR / "bearing_classifier.joblib").is_file()
    assert not (BEARING_MODEL_DIR / "bearing_health_index.joblib").exists()
    assert metrics["file_counts"]["train"]["total"] == 42
    assert metrics["file_counts"]["test"]["total"] == 11
    assert "D:\\" not in manifest
    assert "间隙异常" in "\n".join(metrics["limitations"])


def test_engine_returns_three_probabilities_and_deterministic_remaining_life() -> None:
    engine = BearingDiagnosticEngine(load_bearing_config())
    samples = np.sin(np.linspace(0, 2_000 * np.pi, 16_000 * 5, dtype=np.float32)) * 0.1
    from voice_fault_diagnosis.audio_io import AudioSourceInfo

    info = AudioSourceInfo("WAV", 16_000, 1, len(samples), 5.0, "test")
    first = engine.predict_samples(samples, source_info=info)
    second = engine.predict_samples(samples, source_info=info)
    assert set(first.probabilities) == set(CLASS_IDS)
    assert sum(first.probabilities.values()) == pytest.approx(1.0, abs=1e-6)
    assert first.remaining_life_percent == second.remaining_life_percent
    assert 3.00 <= first.remaining_life_percent <= 99.80
    assert round(first.remaining_life_percent, 2) == first.remaining_life_percent
    assert first.remaining_life_level in {"健康", "预警", "检修"}
    assert first.segment_count == 1


def test_remaining_life_algorithm_is_bounded_deterministic_and_uses_thresholds() -> None:
    config = {"healthy_anomaly_reference": 2.0}
    healthy = estimate_remaining_life({"healthy": 1.0}, 0.0, config)
    warning = estimate_remaining_life({"bearing_damage": 1.0}, 1.0, config)
    maintenance = estimate_remaining_life({"clearance": 1.0}, 20.0, config)
    assert healthy[0] == pytest.approx(98.56)
    assert healthy[1] == "健康"
    assert warning[1] == "预警"
    assert 3.00 <= maintenance[0] < 40.00
    assert maintenance[1] == "检修"
