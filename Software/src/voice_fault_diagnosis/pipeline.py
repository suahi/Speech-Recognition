from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np

from voice_fault_diagnosis.audio_io import AudioSourceInfo, load_audio
from voice_fault_diagnosis.config import BearingAppConfig
from voice_fault_diagnosis.inference.bearing import BearingDiagnosticEngine
from voice_fault_diagnosis.models import PredictionResult
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


StageCallback = Callable[[str, int], None]
PreviewCallback = Callable[[np.ndarray, AudioSourceInfo], None]


def run_bearing_diagnosis(
    config: BearingAppConfig,
    source_path: str | Path,
    *,
    engine: BearingDiagnosticEngine | None = None,
    store: LocalRecordStore | None = None,
    on_stage: StageCallback | None = None,
    on_preview: PreviewCallback | None = None,
) -> tuple[Path, PredictionResult]:
    """Decode one imported file once, preview it, archive it and diagnose it."""

    active_engine = engine or BearingDiagnosticEngine(config)
    active_store = store or LocalRecordStore()
    original_path = Path(source_path).resolve()
    _report(on_stage, "正在解码音频…", 10)
    samples, source_info = load_audio(original_path, target_sample_rate=config.target_sample_rate)
    if on_preview is not None:
        on_preview(samples, source_info)
    _report(on_stage, "音频已解码，正在加载分类模型…", 25)
    active_engine.prepare()
    _report(on_stage, "正在归档原始音频…", 42)
    record_dir = active_store.begin_import(original_path, source_info)
    _report(on_stage, "正在提取特征并进行分类…", 62)
    prediction = active_engine.predict_samples(samples, source_info=source_info, source_path=original_path)
    _report(on_stage, "正在计算算法估计剩余寿命…", 88)
    active_store.complete_record(record_dir, prediction)
    _report(on_stage, "识别完成", 100)
    return record_dir, prediction


def _report(callback: StageCallback | None, message: str, progress: int) -> None:
    if callback is not None:
        callback(message, progress)
