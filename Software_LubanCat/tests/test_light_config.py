from __future__ import annotations

import json

import pytest

from voice_fault_diagnosis.config import EXPECTED_LABEL_CODES, LightConfigError, load_light_config
from voice_fault_diagnosis.paths import LIGHT_CONFIG_PATH


def test_single_light_config_loads_default_hardware_model_and_six_labels() -> None:
    config = load_light_config()

    assert config.source_path == LIGHT_CONFIG_PATH.resolve()
    assert config.capture_duration_seconds == 10.0
    assert config.hardware.capture_seconds == 10.0
    assert tuple(config.model.labels) == EXPECTED_LABEL_CODES
    assert config.model.model_path.is_file()
    assert config.model.mean_std_path.is_file()


def test_light_config_rejects_missing_model_asset(tmp_path) -> None:
    data = json.loads(LIGHT_CONFIG_PATH.read_text(encoding="utf-8"))
    data["model"]["model_path"] = "models/wav_cnn/missing.pt"
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(LightConfigError, match="缺少 WAV 模型文件"):
        load_light_config(path)


def test_light_config_rejects_invalid_adc_channel(tmp_path) -> None:
    data = json.loads(LIGHT_CONFIG_PATH.read_text(encoding="utf-8"))
    data["hardware"]["adc_channel"] = 5
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(LightConfigError, match="adc_channel"):
        load_light_config(path)
