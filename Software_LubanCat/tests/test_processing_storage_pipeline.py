from __future__ import annotations

import json

import numpy as np

from voice_fault_diagnosis.models import CaptureResult, HardwareConfig, PredictionResult
from voice_fault_diagnosis.pipeline import run_wav_diagnosis
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


class FakeWavEngine:
    def __init__(self) -> None:
        self.wav_paths = []

    def predict(self, wav_path) -> PredictionResult:
        self.wav_paths.append(wav_path)
        return PredictionResult(
            model_name="fake_wav_cnn",
            class_index=2,
            label="C2",
            confidence=0.75,
            probabilities=[0.05, 0.1, 0.75, 0.04, 0.03, 0.03],
            top_k=[{"class_index": 2, "label": "C2", "display_name": "敲击", "confidence": 0.75}],
            metadata={"display_name": "敲击", "source_revision": "test"},
        )


def test_pipeline_saves_wav_before_wav_inference_and_keeps_only_light_artifacts(tmp_path) -> None:
    hardware = HardwareConfig(sample_rate=50000, input_range_volts=5.0)
    capture = CaptureResult(
        raw_voltage=np.linspace(-0.5, 0.5, 5000, dtype=np.float32),
        sample_rate=hardware.sample_rate,
        metadata={"daq_ip": "fake"},
    )
    engine = FakeWavEngine()
    store = LocalRecordStore(tmp_path / "records")

    record_dir, prediction = run_wav_diagnosis(capture, hardware, engine, store)

    assert prediction.label == "C2"
    assert engine.wav_paths == [record_dir / "raw.wav"]
    assert (record_dir / "raw_voltage.npy").is_file()
    assert (record_dir / "raw.wav").is_file()
    assert (record_dir / "metadata.json").is_file()
    assert (record_dir / "result.json").is_file()
    assert not (record_dir / "legacy_input.bin").exists()
    assert not (record_dir / "analysis_input.bin").exists()
    assert not (record_dir / "denoised.wav").exists()

    metadata = json.loads((record_dir / "metadata.json").read_text(encoding="utf-8"))
    result = json.loads((record_dir / "result.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "diagnosed"
    assert metadata["model"]["display_name"] == "敲击"
    assert result["label"] == "C2"
    assert result["metadata"]["display_name"] == "敲击"
