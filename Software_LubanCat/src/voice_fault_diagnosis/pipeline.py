from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from voice_fault_diagnosis.audio_io import voltage_to_audio
from voice_fault_diagnosis.inference.legacy_cnn import LegacyCnnEngine
from voice_fault_diagnosis.models import (
    CaptureResult,
    DenoiseConfig,
    DiagnosisProgress,
    HardwareConfig,
    PredictionResult,
)
from voice_fault_diagnosis.processing.denoise import apply_denoise
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


ProgressCallback = Callable[[DiagnosisProgress], None]


def run_diagnosis(
    capture: CaptureResult,
    hardware_config: HardwareConfig,
    denoise_config: DenoiseConfig,
    engine: LegacyCnnEngine,
    store: LocalRecordStore,
    progress_callback: ProgressCallback | None = None,
) -> tuple[Path, PredictionResult]:
    def emit(stage: str, percent: int, message: str) -> None:
        if progress_callback is not None:
            progress_callback(DiagnosisProgress(stage=stage, percent=percent, message=message))

    emit("audio", 5, "正在转换电压信号")
    raw_audio = voltage_to_audio(capture.raw_voltage, hardware_config.input_range_volts)

    emit("denoise", 20, "正在执行降噪处理")
    denoised_audio, denoise_metadata = apply_denoise(raw_audio, capture.sample_rate, denoise_config)

    emit("inference", 35, "正在准备模型推理")
    prediction = engine.predict(capture.legacy_input, progress_callback=progress_callback)

    emit("storage", 85, "正在保存诊断记录")
    record_dir = store.create_record(
        capture=capture,
        raw_audio=raw_audio,
        denoised_audio=denoised_audio,
        hardware_config=hardware_config,
        denoise_config=denoise_config,
        denoise_metadata=denoise_metadata,
        prediction=prediction,
    )
    emit("complete", 100, "诊断完成")
    return record_dir, prediction
