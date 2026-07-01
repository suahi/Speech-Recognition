from __future__ import annotations

from pathlib import Path

from voice_fault_diagnosis.audio_io import voltage_to_audio
from voice_fault_diagnosis.inference.legacy_cnn import LegacyCnnEngine
from voice_fault_diagnosis.models import CaptureResult, DenoiseConfig, HardwareConfig, PredictionResult
from voice_fault_diagnosis.processing.denoise import apply_denoise
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


def run_diagnosis(
    capture: CaptureResult,
    hardware_config: HardwareConfig,
    denoise_config: DenoiseConfig,
    engine: LegacyCnnEngine,
    store: LocalRecordStore,
) -> tuple[Path, PredictionResult]:
    raw_audio = voltage_to_audio(capture.raw_voltage, hardware_config.input_range_volts)
    denoised_audio, denoise_metadata = apply_denoise(raw_audio, capture.sample_rate, denoise_config)
    prediction = engine.predict(capture.legacy_input)
    record_dir = store.create_record(
        capture=capture,
        raw_audio=raw_audio,
        denoised_audio=denoised_audio,
        hardware_config=hardware_config,
        denoise_config=denoise_config,
        denoise_metadata=denoise_metadata,
        prediction=prediction,
    )
    return record_dir, prediction
