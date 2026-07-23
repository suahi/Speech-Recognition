from __future__ import annotations

from pathlib import Path

from voice_fault_diagnosis.audio_io import voltage_to_audio
from voice_fault_diagnosis.inference.wav_cnn import WavCnnEngine
from voice_fault_diagnosis.models import CaptureResult, HardwareConfig, PredictionResult
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


def run_wav_diagnosis(
    capture: CaptureResult,
    hardware_config: HardwareConfig,
    engine: WavCnnEngine,
    store: LocalRecordStore,
) -> tuple[Path, PredictionResult]:
    """Persist the captured WAV first, then use that exact file as model input."""

    raw_audio = voltage_to_audio(capture.raw_voltage, hardware_config.input_range_volts)
    record_dir = store.save_capture(capture, raw_audio, hardware_config)
    prediction = engine.predict(record_dir / "raw.wav")
    return store.complete_record(record_dir, prediction), prediction
