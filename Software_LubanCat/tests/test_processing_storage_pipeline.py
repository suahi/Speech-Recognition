from __future__ import annotations

import json

import numpy as np

from voice_fault_diagnosis.audio_io import voltage_to_audio
from voice_fault_diagnosis.legacy_format import voltage_to_legacy_bytes
from voice_fault_diagnosis.models import CaptureResult, DenoiseConfig, HardwareConfig, PredictionResult
from voice_fault_diagnosis.pipeline import run_diagnosis
from voice_fault_diagnosis.processing.denoise import apply_denoise
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


class FakeEngine:
    def predict(self, legacy_input: bytes) -> PredictionResult:
        assert legacy_input
        return PredictionResult(
            model_name="fake",
            class_index=2,
            label="class_2",
            confidence=0.75,
            probabilities=[0.05, 0.1, 0.75, 0.1],
            top_k=[{"class_index": 2, "label": "class_2", "confidence": 0.75}],
        )


def test_voltage_to_legacy_bytes_matches_old_queue_length() -> None:
    voltage = np.array([-10.0, -5.0, 0.0, 5.0, 10.0], dtype=np.float32)
    legacy = voltage_to_legacy_bytes(voltage, gain=0.668)

    assert isinstance(legacy, bytes)
    assert len(legacy) == voltage.size


def test_denoise_keeps_shape_and_float32() -> None:
    sample_rate = 50000
    t = np.arange(sample_rate // 10, dtype=np.float32) / sample_rate
    audio = (0.1 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    config = DenoiseConfig(enabled=True, bandpass_enabled=True, bandpass_low_hz=100.0, bandpass_high_hz=5000.0)

    processed, metadata = apply_denoise(audio, sample_rate, config)

    assert processed.shape == audio.shape
    assert processed.dtype == np.float32
    assert metadata["bandpass"]["low_hz"] == 100.0


def test_pipeline_saves_local_files_without_sqlite(tmp_path) -> None:
    hardware = HardwareConfig(sample_rate=50000, input_range_volts=5.0)
    voltage = np.linspace(-0.5, 0.5, 5000, dtype=np.float32)
    capture = CaptureResult(
        raw_voltage=voltage,
        legacy_input=voltage_to_legacy_bytes(voltage),
        sample_rate=hardware.sample_rate,
        metadata={"daq_ip": "fake"},
    )
    store = LocalRecordStore(tmp_path / "records")

    record_dir, prediction = run_diagnosis(
        capture=capture,
        hardware_config=hardware,
        denoise_config=DenoiseConfig(enabled=False),
        engine=FakeEngine(),
        store=store,
    )

    assert prediction.label == "class_2"
    assert (record_dir / "raw_voltage.npy").exists()
    assert (record_dir / "raw.wav").exists()
    assert (record_dir / "legacy_input.bin").exists()
    assert (record_dir / "denoised.wav").exists()
    assert (record_dir / "metadata.json").exists()
    assert (record_dir / "result.json").exists()
    assert not (tmp_path / "history.db").exists()
    result = json.loads((record_dir / "result.json").read_text(encoding="utf-8"))
    assert result["confidence"] == 0.75
    assert store.list_records()[0]["label"] == "class_2"
