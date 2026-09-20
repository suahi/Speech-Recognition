from __future__ import annotations

from pathlib import Path
from typing import Callable

from voice_fault_diagnosis.audio_io import inspect_audio
from voice_fault_diagnosis.config import BearingAppConfig
from voice_fault_diagnosis.inference.bearing import BearingDiagnosticEngine
from voice_fault_diagnosis.models import PredictionResult
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


StageCallback = Callable[[str, int], None]


def run_bearing_diagnosis(
    config: BearingAppConfig,
    source_path: str | Path,
    *,
    engine: BearingDiagnosticEngine | None = None,
    store: LocalRecordStore | None = None,
    on_stage: StageCallback | None = None,
) -> tuple[Path, PredictionResult]:
    """Validate, archive and diagnose one imported M4A/WAV file in that order."""

    active_engine = engine or BearingDiagnosticEngine(config)
    active_store = store or LocalRecordStore()
    original_path = Path(source_path).resolve()
    _report(on_stage, "正在检查模型文件…", 5)
    active_engine.prepare()
    _report(on_stage, "正在解码并校验音频…", 20)
    source_info = inspect_audio(original_path, target_sample_rate=config.target_sample_rate)
    _report(on_stage, "正在归档原始音频…", 42)
    record_dir = active_store.begin_import(original_path, source_info)
    _report(on_stage, "正在提取特征并进行分类…", 62)
    prediction = active_engine.predict(active_store.source_audio_path(record_dir))
    _report(on_stage, "正在生成健康指数…", 88)
    active_store.complete_record(record_dir, prediction)
    _report(on_stage, "识别完成", 100)
    return record_dir, prediction


def _report(callback: StageCallback | None, message: str, progress: int) -> None:
    if callback is not None:
        callback(message, progress)
