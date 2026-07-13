from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
import uuid

import numpy as np

from voice_fault_diagnosis.audio_io import save_wav
from voice_fault_diagnosis.models import CaptureResult, DenoiseConfig, HardwareConfig, PredictionResult
from voice_fault_diagnosis.paths import RECORDS_DIR


class LocalRecordStore:
    def __init__(self, records_dir: str | Path = RECORDS_DIR) -> None:
        self.records_dir = Path(records_dir).resolve()
        self.records_dir.mkdir(parents=True, exist_ok=True)

    def create_record(
        self,
        capture: CaptureResult,
        raw_audio: np.ndarray,
        denoised_audio: np.ndarray,
        hardware_config: HardwareConfig,
        denoise_config: DenoiseConfig,
        denoise_metadata: dict[str, Any],
        prediction: PredictionResult,
    ) -> Path:
        record_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        record_dir = self.records_dir / record_id
        record_dir.mkdir(parents=True, exist_ok=False)

        np.save(record_dir / "raw_voltage.npy", np.asarray(capture.raw_voltage, dtype=np.float32))
        (record_dir / "legacy_input.bin").write_bytes(capture.legacy_input)
        save_wav(record_dir / "raw.wav", raw_audio, capture.sample_rate)
        save_wav(record_dir / "denoised.wav", denoised_audio, capture.sample_rate)

        metadata = {
            "record_id": record_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "sample_rate": int(capture.sample_rate),
            "hardware_config": hardware_config.to_dict(),
            "capture_metadata": capture.metadata,
            "denoise_config": denoise_config.to_dict(),
            "denoise_metadata": denoise_metadata,
            "files": {
                "raw_voltage": str(record_dir / "raw_voltage.npy"),
                "raw_wav": str(record_dir / "raw.wav"),
                "legacy_input": str(record_dir / "legacy_input.bin"),
                "denoised_wav": str(record_dir / "denoised.wav"),
                "result": str(record_dir / "result.json"),
            },
        }
        result = prediction.to_dict()
        result["record_id"] = record_id
        result["created_at"] = metadata["created_at"]

        _write_json(record_dir / "metadata.json", metadata)
        _write_json(record_dir / "result.json", result)
        return record_dir

    def list_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for metadata_path in self.records_dir.glob("*/metadata.json"):
            result_path = metadata_path.parent / "result.json"
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
            except Exception:
                continue
            records.append(
                {
                    "record_id": metadata.get("record_id", metadata_path.parent.name),
                    "created_at": metadata.get("created_at", ""),
                    "label": result.get("label", ""),
                    "class_index": result.get("class_index", ""),
                    "confidence": result.get("confidence", 0.0),
                    "record_dir": str(metadata_path.parent),
                    "metadata_path": str(metadata_path),
                    "result_path": str(result_path),
                }
            )
        return sorted(records, key=lambda item: str(item.get("created_at", "")), reverse=True)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
