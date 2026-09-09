from __future__ import annotations

from pathlib import Path
import threading
from typing import Callable

import numpy as np

from voice_fault_diagnosis.audio_io import inspect_wav, voltage_to_audio
from voice_fault_diagnosis.capture.vk701n import Vk701nCaptureSession
from voice_fault_diagnosis.config import PcAppConfig
from voice_fault_diagnosis.inference.wav_cnn import WavCnnEngine
from voice_fault_diagnosis.models import CaptureResult, HardwareConfig, PredictionResult
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


ChunkCallback = Callable[[np.ndarray, dict[str, object]], None]
StageCallback = Callable[[str, int], None]


def run_realtime_capture(
    config: PcAppConfig,
    *,
    engine: WavCnnEngine | None = None,
    store: LocalRecordStore | None = None,
    on_chunk: ChunkCallback | None = None,
    stop_event: threading.Event | None = None,
    on_stage: StageCallback | None = None,
) -> tuple[Path, PredictionResult]:
    """Capture from the Windows SDK, archive a WAV, and classify it."""

    _report(on_stage, "正在连接 VK701N-SD 采集卡…", 5)
    # Constructing the session is intentionally deferred to this worker entrypoint.
    session = Vk701nCaptureSession(config.hardware)
    _report(on_stage, "正在采集麦克风电压…", 10)
    capture = session.capture(on_chunk=on_chunk, stop_event=stop_event)
    if np.asarray(capture.raw_voltage).size == 0:
        raise RuntimeError("未采集到有效声纹电压数据，未生成 WAV 或执行识别。")
    _report(on_stage, "正在生成 WAV 并执行六类识别…", 72)
    outcome = run_wav_diagnosis(
        capture,
        config.hardware,
        engine or WavCnnEngine(config.model),
        store or LocalRecordStore(),
    )
    _report(on_stage, "识别完成", 100)
    return outcome


def run_imported_wav(
    config: PcAppConfig,
    source_path: str | Path,
    *,
    engine: WavCnnEngine | None = None,
    store: LocalRecordStore | None = None,
    on_stage: StageCallback | None = None,
) -> tuple[Path, PredictionResult]:
    """Validate and archive a WAV, then classify the archived copy."""

    original_path = Path(source_path).resolve()
    _report(on_stage, "正在校验 WAV 文件…", 10)
    source_info = inspect_wav(original_path)
    active_store = store or LocalRecordStore()
    _report(on_stage, "正在归档 WAV 文件…", 35)
    record_dir = active_store.save_imported_wav(original_path, source_info)
    _report(on_stage, "正在执行六类识别…", 60)
    prediction = (engine or WavCnnEngine(config.model)).predict(record_dir / "raw.wav")
    outcome = active_store.complete_record(record_dir, prediction), prediction
    _report(on_stage, "识别完成", 100)
    return outcome


def run_wav_diagnosis(
    capture: CaptureResult,
    hardware_config: HardwareConfig,
    engine: WavCnnEngine,
    store: LocalRecordStore,
) -> tuple[Path, PredictionResult]:
    """Persist a real-time capture before using that exact WAV for inference."""

    raw_audio = voltage_to_audio(capture.raw_voltage, hardware_config.input_range_volts)
    record_dir = store.save_capture(capture, raw_audio, hardware_config)
    prediction = engine.predict(record_dir / "raw.wav")
    return store.complete_record(record_dir, prediction), prediction


def _report(callback: StageCallback | None, message: str, progress: int) -> None:
    if callback is not None:
        callback(message, progress)
