from __future__ import annotations

import json

import numpy as np
import pytest

from voice_fault_diagnosis.audio_io import voltage_to_audio
from voice_fault_diagnosis.legacy_format import voltage_to_legacy_bytes
from voice_fault_diagnosis.models import (
    CaptureResult,
    DenoiseConfig,
    DenoiseResult,
    DiagnosisProgress,
    HardwareConfig,
    PredictionResult,
)
from voice_fault_diagnosis.pipeline import build_analysis_input, run_analysis, run_diagnosis
from voice_fault_diagnosis.processing.denoise import apply_denoise
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


class FakeEngine:
    def __init__(self) -> None:
        self.inputs: list[bytes] = []

    def predict(self, legacy_input: bytes, progress_callback=None) -> PredictionResult:
        assert legacy_input
        self.inputs.append(legacy_input)
        if progress_callback is not None:
            progress_callback(DiagnosisProgress(stage="fake_model", percent=75, message="fake inference"))
        return _prediction()


def _prediction() -> PredictionResult:
    return PredictionResult(
        model_name="fake",
        class_index=2,
        label="class_2",
        confidence=0.75,
        probabilities=[0.05, 0.1, 0.75, 0.1],
        top_k=[{"class_index": 2, "label": "class_2", "confidence": 0.75}],
    )


def _capture(hardware: HardwareConfig, size: int = 5000) -> CaptureResult:
    voltage = np.linspace(-0.5, 0.5, size, dtype=np.float32)
    return CaptureResult(
        raw_voltage=voltage,
        legacy_input=voltage_to_legacy_bytes(voltage, gain=hardware.gain),
        sample_rate=hardware.sample_rate,
        metadata={"daq_ip": "fake"},
    )


def test_voltage_to_legacy_bytes_matches_old_queue_length() -> None:
    voltage = np.array([-10.0, -5.0, 0.0, 5.0, 10.0], dtype=np.float32)
    legacy = voltage_to_legacy_bytes(voltage, gain=0.668)

    assert isinstance(legacy, bytes)
    assert len(legacy) == voltage.size


def test_denoise_without_enabled_method_is_explicit_noop() -> None:
    audio = np.linspace(-0.1, 0.1, 1024, dtype=np.float32)

    processed, metadata = apply_denoise(audio, 50000, DenoiseConfig(enabled=True))

    assert np.array_equal(processed, audio)
    assert metadata["applied"] is False
    assert metadata["methods"] == []
    assert metadata["skip_reason"] == "no_method_enabled"
    assert metadata["metrics"]["difference_rms"] == 0.0


def test_bandpass_denoise_keeps_shape_and_emits_progress() -> None:
    sample_rate = 50000
    t = np.arange(sample_rate // 10, dtype=np.float32) / sample_rate
    audio = (0.1 * np.sin(2 * np.pi * 1000 * t) + 0.02 * np.sin(2 * np.pi * 12000 * t)).astype(np.float32)
    config = DenoiseConfig(
        enabled=True,
        bandpass_enabled=True,
        bandpass_low_hz=100.0,
        bandpass_high_hz=5000.0,
    )
    events: list[DiagnosisProgress] = []

    processed, metadata = apply_denoise(audio, sample_rate, config, progress_callback=events.append)

    assert processed.shape == audio.shape
    assert processed.dtype == np.float32
    assert not np.array_equal(processed, audio)
    assert metadata["applied"] is True
    assert metadata["methods"] == ["bandpass"]
    assert [event.stage for event in events] == [
        "denoise_prepare",
        "denoise_bandpass",
        "denoise_metrics",
        "denoise_complete",
    ]
    assert events[-1].percent == 100


def test_wavelet_denoise_keeps_shape_and_records_method() -> None:
    rng = np.random.default_rng(7)
    audio = rng.normal(0.0, 0.05, 4096).astype(np.float32)
    config = DenoiseConfig(enabled=True, wavelet_enabled=True, wavelet="db4", wavelet_level=3)

    processed, metadata = apply_denoise(audio, 50000, config)

    assert processed.shape == audio.shape
    assert processed.dtype == np.float32
    assert metadata["methods"] == ["wavelet"]
    assert metadata["wavelet"]["threshold"] == "soft"


def test_invalid_bandpass_is_rejected_before_processing() -> None:
    config = DenoiseConfig(
        enabled=True,
        bandpass_enabled=True,
        bandpass_low_hz=10000.0,
        bandpass_high_hz=30000.0,
    )

    with pytest.raises(ValueError, match="Nyquist"):
        apply_denoise(np.ones(2048, dtype=np.float32), 50000, config)


def test_analysis_input_uses_exact_raw_or_regenerated_denoised_bytes() -> None:
    hardware = HardwareConfig(sample_rate=50000, input_range_volts=5.0, gain=0.668)
    capture = _capture(hardware)
    raw_audio = voltage_to_audio(capture.raw_voltage, hardware.input_range_volts)
    denoise_result = DenoiseResult(
        processed_audio=raw_audio * 0.5,
        config=DenoiseConfig(enabled=True, bandpass_enabled=True),
        metadata={"applied": True, "methods": ["bandpass"]},
    )

    raw_input = build_analysis_input(capture, hardware, "raw")
    denoised_input = build_analysis_input(capture, hardware, "denoised", denoise_result)

    assert raw_input is capture.legacy_input
    assert raw_input == capture.legacy_input
    assert denoised_input != capture.legacy_input
    assert len(denoised_input) == len(capture.legacy_input)


def test_pipeline_saves_local_files_without_sqlite(tmp_path) -> None:
    hardware = HardwareConfig(sample_rate=50000, input_range_volts=5.0)
    capture = _capture(hardware)
    store = LocalRecordStore(tmp_path / "records")

    record_dir, prediction = run_diagnosis(
        capture=capture,
        hardware_config=hardware,
        denoise_config=DenoiseConfig(enabled=False),
        engine=FakeEngine(),
        store=store,
    )

    assert prediction.label == "class_2"
    for filename in [
        "raw_voltage.npy",
        "raw.wav",
        "legacy_input.bin",
        "analysis_input.bin",
        "denoised.wav",
        "metadata.json",
        "result.json",
    ]:
        assert (record_dir / filename).exists()
    assert not (tmp_path / "history.db").exists()
    result = json.loads((record_dir / "result.json").read_text(encoding="utf-8"))
    metadata = json.loads((record_dir / "metadata.json").read_text(encoding="utf-8"))
    assert result["confidence"] == 0.75
    assert result["analysis_source"] == "raw"
    assert metadata["status"] == "diagnosed"
    assert store.list_records()[0]["label"] == "class_2"


def test_capture_save_is_idempotent_and_diagnosis_can_be_completed(tmp_path) -> None:
    hardware = HardwareConfig(sample_rate=50000, input_range_volts=5.0)
    capture = _capture(hardware)
    raw_audio = voltage_to_audio(capture.raw_voltage, hardware.input_range_volts)
    store = LocalRecordStore(tmp_path / "records")

    first = store.save_capture(capture, raw_audio, hardware)
    second = store.save_capture(capture, raw_audio, hardware, existing_record_dir=first)

    assert first == second
    assert len(store.list_records()) == 1
    assert store.list_records()[0]["status"] == "captured"
    assert not (first / "result.json").exists()

    completed = store.complete_record(
        capture=capture,
        raw_audio=raw_audio,
        hardware_config=hardware,
        prediction=_prediction(),
        analysis_source="raw",
        analysis_input=capture.legacy_input,
        record_dir=first,
    )

    assert completed == first
    assert store.list_records()[0]["status"] == "diagnosed"
    assert (completed / "analysis_input.bin").read_bytes() == capture.legacy_input


def test_reanalyzing_diagnosed_record_creates_linked_record(tmp_path) -> None:
    hardware = HardwareConfig(sample_rate=50000, input_range_volts=5.0)
    capture = _capture(hardware)
    raw_audio = voltage_to_audio(capture.raw_voltage, hardware.input_range_volts)
    store = LocalRecordStore(tmp_path / "records")
    original = store.save_capture(capture, raw_audio, hardware)
    store.complete_record(
        capture=capture,
        raw_audio=raw_audio,
        hardware_config=hardware,
        prediction=_prediction(),
        analysis_source="raw",
        analysis_input=capture.legacy_input,
        record_dir=original,
    )

    derived = store.complete_record(
        capture=capture,
        raw_audio=raw_audio,
        hardware_config=hardware,
        prediction=_prediction(),
        analysis_source="raw",
        analysis_input=capture.legacy_input,
        record_dir=original,
    )

    assert derived != original
    metadata = json.loads((derived / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["source_record_id"] == original.name
    assert len(store.list_records()) == 2


def test_saved_capture_can_be_loaded_with_original_hardware_metadata(tmp_path) -> None:
    hardware = HardwareConfig(sample_rate=32000, input_range_volts=2.5, gain=0.7)
    capture = _capture(hardware, size=2048)
    store = LocalRecordStore(tmp_path / "records")
    record_dir = store.save_capture(
        capture,
        voltage_to_audio(capture.raw_voltage, hardware.input_range_volts),
        hardware,
    )

    stored = store.load_capture_record(record_dir)

    assert stored.record_dir == record_dir
    assert stored.hardware_config.input_range_volts == 2.5
    assert stored.hardware_config.gain == 0.7
    assert stored.capture.sample_rate == 32000
    assert np.array_equal(stored.capture.raw_voltage, capture.raw_voltage)
    assert stored.capture.legacy_input == capture.legacy_input


def test_record_loader_rejects_paths_outside_application_store(tmp_path) -> None:
    store = LocalRecordStore(tmp_path / "records")
    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(ValueError, match="不属于"):
        store.load_capture_record(outside)


def test_denoised_analysis_records_input_source_and_actual_bytes(tmp_path) -> None:
    hardware = HardwareConfig(sample_rate=50000, input_range_volts=5.0)
    capture = _capture(hardware)
    raw_audio = voltage_to_audio(capture.raw_voltage, hardware.input_range_volts)
    denoise_result = DenoiseResult(
        processed_audio=raw_audio * 0.25,
        config=DenoiseConfig(enabled=True, bandpass_enabled=True),
        metadata={"enabled": True, "applied": True, "methods": ["bandpass"]},
        metrics={"difference_rms": 0.01},
    )
    engine = FakeEngine()

    record_dir, prediction = run_analysis(
        capture=capture,
        hardware_config=hardware,
        engine=engine,
        store=LocalRecordStore(tmp_path / "records"),
        analysis_source="denoised",
        denoise_result=denoise_result,
    )

    assert prediction.metadata["analysis_source"] == "denoised"
    assert engine.inputs[0] != capture.legacy_input
    assert (record_dir / "analysis_input.bin").read_bytes() == engine.inputs[0]
    metadata = json.loads((record_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["analysis_source"] == "denoised"
    assert metadata["denoise_metadata"]["applied"] is True


def test_pipeline_emits_monotonic_progress_events(tmp_path) -> None:
    hardware = HardwareConfig(sample_rate=50000, input_range_volts=5.0)
    events: list[DiagnosisProgress] = []

    run_diagnosis(
        capture=_capture(hardware),
        hardware_config=hardware,
        denoise_config=DenoiseConfig(enabled=False),
        engine=FakeEngine(),
        store=LocalRecordStore(tmp_path / "records"),
        progress_callback=events.append,
    )

    stages = [event.stage for event in events]
    percentages = [event.percent for event in events]
    assert "denoise_prepare" in stages
    assert "inference" in stages
    assert "fake_model" in stages
    assert stages[-2:] == ["storage", "complete"]
    assert percentages == sorted(percentages)
    assert percentages[-1] == 100
