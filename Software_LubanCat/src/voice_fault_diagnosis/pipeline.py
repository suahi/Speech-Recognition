from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np

from voice_fault_diagnosis.audio_io import voltage_to_audio
from voice_fault_diagnosis.inference.legacy_cnn import LegacyCnnEngine
from voice_fault_diagnosis.legacy_format import voltage_to_legacy_bytes
from voice_fault_diagnosis.models import (
    AnalysisSource,
    CaptureResult,
    DenoiseConfig,
    DenoiseResult,
    DiagnosisProgress,
    HardwareConfig,
    PredictionResult,
)
from voice_fault_diagnosis.processing.denoise import apply_denoise
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


ProgressCallback = Callable[[DiagnosisProgress], None]


def run_denoise(
    capture: CaptureResult,
    hardware_config: HardwareConfig,
    denoise_config: DenoiseConfig,
    progress_callback: ProgressCallback | None = None,
) -> tuple[np.ndarray, DenoiseResult]:
    _emit(progress_callback, "audio", 1, "正在准备采样音频")
    raw_audio = voltage_to_audio(capture.raw_voltage, hardware_config.input_range_volts)
    processed, metadata = apply_denoise(
        raw_audio,
        capture.sample_rate,
        denoise_config,
        progress_callback=progress_callback,
    )
    metrics = {
        str(key): float(value)
        for key, value in dict(metadata.get("metrics") or {}).items()
        if isinstance(value, (int, float))
    }
    result = DenoiseResult(
        processed_audio=processed,
        config=denoise_config,
        metadata=metadata,
        metrics=metrics,
    )
    return raw_audio, result


def build_analysis_input(
    capture: CaptureResult,
    hardware_config: HardwareConfig,
    analysis_source: AnalysisSource,
    denoise_result: DenoiseResult | None = None,
) -> bytes:
    if analysis_source == "raw":
        if not capture.legacy_input:
            raise ValueError("原始 legacy 输入为空")
        return capture.legacy_input
    if analysis_source != "denoised":
        raise ValueError(f"unsupported analysis source: {analysis_source}")
    if denoise_result is None:
        raise ValueError("使用降噪结果分析前必须先完成降噪处理")
    if not bool(denoise_result.metadata.get("applied")):
        raise ValueError("当前结果没有真正执行任何降噪方法")

    processed_audio = np.asarray(denoise_result.processed_audio, dtype=np.float32).reshape(-1)
    raw_voltage = np.asarray(capture.raw_voltage, dtype=np.float32).reshape(-1)
    if processed_audio.size != raw_voltage.size:
        raise ValueError("降噪结果长度与原始采样不一致")
    denoised_voltage = processed_audio * float(hardware_config.input_range_volts)
    return voltage_to_legacy_bytes(denoised_voltage, gain=float(hardware_config.gain))


def run_analysis(
    capture: CaptureResult,
    hardware_config: HardwareConfig,
    engine: LegacyCnnEngine,
    store: LocalRecordStore,
    analysis_source: AnalysisSource = "raw",
    denoise_result: DenoiseResult | None = None,
    record_dir: str | Path | None = None,
    source_record_id: str | None = None,
    progress_callback: ProgressCallback | None = None,
) -> tuple[Path, PredictionResult]:
    _emit(progress_callback, "analysis_input", 10, "正在准备模型输入")
    analysis_input = build_analysis_input(
        capture=capture,
        hardware_config=hardware_config,
        analysis_source=analysis_source,
        denoise_result=denoise_result,
    )

    _emit(progress_callback, "inference", 35, "正在准备模型推理")
    prediction = engine.predict(analysis_input, progress_callback=progress_callback)
    prediction.metadata = dict(prediction.metadata)
    prediction.metadata.update(
        {
            "analysis_source": analysis_source,
            "denoise_applied": bool(denoise_result and denoise_result.metadata.get("applied")),
        }
    )

    _emit(progress_callback, "storage", 85, "正在保存诊断记录")
    raw_audio = voltage_to_audio(capture.raw_voltage, hardware_config.input_range_volts)
    completed_dir = store.complete_record(
        capture=capture,
        raw_audio=raw_audio,
        hardware_config=hardware_config,
        prediction=prediction,
        analysis_source=analysis_source,
        analysis_input=analysis_input,
        denoise_result=denoise_result,
        record_dir=record_dir,
        source_record_id=source_record_id,
    )
    _emit(progress_callback, "complete", 100, "诊断完成")
    return completed_dir, prediction


def run_diagnosis(
    capture: CaptureResult,
    hardware_config: HardwareConfig,
    denoise_config: DenoiseConfig,
    engine: LegacyCnnEngine,
    store: LocalRecordStore,
    progress_callback: ProgressCallback | None = None,
    analysis_source: AnalysisSource = "raw",
) -> tuple[Path, PredictionResult]:
    """Compatibility wrapper that still performs denoise, inference and storage in one call."""

    def mapped_denoise_progress(progress: DiagnosisProgress) -> None:
        mapped_percent = 5 + int(round(max(0, min(100, progress.percent)) * 0.25))
        _emit(progress_callback, progress.stage, mapped_percent, progress.message)

    def mapped_analysis_progress(progress: DiagnosisProgress) -> None:
        mapped_percent = 35 + int(round(max(0, min(100, progress.percent)) * 0.65))
        _emit(progress_callback, progress.stage, mapped_percent, progress.message)

    _, denoise_result = run_denoise(
        capture=capture,
        hardware_config=hardware_config,
        denoise_config=denoise_config,
        progress_callback=mapped_denoise_progress,
    )
    _emit(progress_callback, "inference", 35, "正在准备模型推理")
    return run_analysis(
        capture=capture,
        hardware_config=hardware_config,
        engine=engine,
        store=store,
        analysis_source=analysis_source,
        denoise_result=denoise_result,
        progress_callback=mapped_analysis_progress,
    )


def _emit(progress_callback: ProgressCallback | None, stage: str, percent: int, message: str) -> None:
    if progress_callback is not None:
        progress_callback(DiagnosisProgress(stage=stage, percent=percent, message=message))
