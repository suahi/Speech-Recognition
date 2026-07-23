from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
import uuid

import numpy as np

from voice_fault_diagnosis.audio_io import save_wav
from voice_fault_diagnosis.models import CaptureResult, HardwareConfig, PredictionResult
from voice_fault_diagnosis.paths import RECORDS_DIR


class LocalRecordStore:
    """Filesystem-only storage for one capture and its WAV classification result."""

    def __init__(self, records_dir: str | Path = RECORDS_DIR) -> None:
        self.records_dir = Path(records_dir).resolve()
        self.records_dir.mkdir(parents=True, exist_ok=True)

    def save_capture(
        self,
        capture: CaptureResult,
        raw_audio: np.ndarray,
        hardware_config: HardwareConfig,
    ) -> Path:
        record_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        record_dir = self.records_dir / record_id
        record_dir.mkdir(parents=True, exist_ok=False)
        voltage_path = record_dir / "raw_voltage.npy"
        wav_path = record_dir / "raw.wav"
        np.save(voltage_path, np.asarray(capture.raw_voltage, dtype=np.float32))
        save_wav(wav_path, raw_audio, capture.sample_rate)

        created_at = datetime.now().isoformat(timespec="seconds")
        _write_json(
            record_dir / "metadata.json",
            {
                "record_id": record_id,
                "created_at": created_at,
                "updated_at": created_at,
                "status": "captured",
                "sample_rate": int(capture.sample_rate),
                "hardware_config": hardware_config.to_dict(),
                "capture_metadata": dict(capture.metadata),
                "files": {
                    "raw_voltage": str(voltage_path),
                    "raw_wav": str(wav_path),
                },
            },
        )
        return record_dir

    def complete_record(self, record_dir: str | Path, prediction: PredictionResult) -> Path:
        record_dir = self._resolve_record_dir(record_dir)
        metadata = self._read_metadata(record_dir)
        wav_path = record_dir / "raw.wav"
        if not wav_path.is_file():
            raise FileNotFoundError(f"采集记录缺少 raw.wav：{record_dir}")
        result_path = record_dir / "result.json"
        result = prediction.to_dict()
        result["record_id"] = metadata["record_id"]
        result["created_at"] = metadata["created_at"]
        _write_json(result_path, result)
        files = dict(metadata.get("files") or {})
        files["result"] = str(result_path)
        metadata.update(
            {
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "status": "diagnosed",
                "model": dict(prediction.metadata),
                "files": files,
            }
        )
        _write_json(record_dir / "metadata.json", metadata)
        return record_dir

    def _resolve_record_dir(self, value: str | Path) -> Path:
        record_dir = Path(value).resolve()
        try:
            record_dir.relative_to(self.records_dir)
        except ValueError as exc:
            raise ValueError("记录目录不属于当前应用的数据目录。") from exc
        if not record_dir.is_dir():
            raise FileNotFoundError(f"记录目录不存在：{record_dir}")
        return record_dir

    @staticmethod
    def _read_metadata(record_dir: Path) -> dict[str, Any]:
        path = record_dir / "metadata.json"
        if not path.is_file():
            raise FileNotFoundError(f"记录缺少 metadata.json：{record_dir}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"metadata.json 内容无效：{record_dir}")
        return data


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
