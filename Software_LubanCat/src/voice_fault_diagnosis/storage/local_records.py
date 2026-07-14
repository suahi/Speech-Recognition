from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
import uuid

import numpy as np

from voice_fault_diagnosis.audio_io import save_wav
from voice_fault_diagnosis.models import (
    AnalysisSource,
    CaptureResult,
    DenoiseConfig,
    DenoiseResult,
    HardwareConfig,
    PredictionResult,
    StoredCapture,
)
from voice_fault_diagnosis.paths import RECORDS_DIR


class LocalRecordStore:
    def __init__(self, records_dir: str | Path = RECORDS_DIR) -> None:
        self.records_dir = Path(records_dir).resolve()
        self.records_dir.mkdir(parents=True, exist_ok=True)

    def save_capture(
        self,
        capture: CaptureResult,
        raw_audio: np.ndarray,
        hardware_config: HardwareConfig,
        existing_record_dir: str | Path | None = None,
        source_record_id: str | None = None,
    ) -> Path:
        if existing_record_dir is not None:
            record_dir = self._resolve_record_dir(existing_record_dir)
            self._validate_capture_files(record_dir)
            return record_dir

        record_dir = self._new_record_dir()
        np.save(record_dir / "raw_voltage.npy", np.asarray(capture.raw_voltage, dtype=np.float32))
        (record_dir / "legacy_input.bin").write_bytes(capture.legacy_input)
        save_wav(record_dir / "raw.wav", raw_audio, capture.sample_rate)

        record_id = record_dir.name
        created_at = datetime.now().isoformat(timespec="seconds")
        metadata: dict[str, Any] = {
            "record_id": record_id,
            "created_at": created_at,
            "updated_at": created_at,
            "status": "captured",
            "sample_rate": int(capture.sample_rate),
            "hardware_config": hardware_config.to_dict(),
            "capture_metadata": capture.metadata,
            "files": {
                "raw_voltage": str(record_dir / "raw_voltage.npy"),
                "raw_wav": str(record_dir / "raw.wav"),
                "legacy_input": str(record_dir / "legacy_input.bin"),
            },
        }
        if source_record_id:
            metadata["source_record_id"] = str(source_record_id)
        _write_json(record_dir / "metadata.json", metadata)
        return record_dir

    def complete_record(
        self,
        capture: CaptureResult,
        raw_audio: np.ndarray,
        hardware_config: HardwareConfig,
        prediction: PredictionResult,
        analysis_source: AnalysisSource,
        analysis_input: bytes,
        denoise_result: DenoiseResult | None = None,
        record_dir: str | Path | None = None,
        source_record_id: str | None = None,
    ) -> Path:
        target_dir: Path | None = None
        if record_dir is not None:
            candidate = self._resolve_record_dir(record_dir)
            self._validate_capture_files(candidate)
            metadata = self._read_metadata(candidate)
            if metadata.get("status") == "diagnosed":
                source_record_id = str(metadata.get("record_id") or candidate.name)
            else:
                target_dir = candidate

        if target_dir is None:
            target_dir = self.save_capture(
                capture=capture,
                raw_audio=raw_audio,
                hardware_config=hardware_config,
                source_record_id=source_record_id,
            )

        metadata = self._read_metadata(target_dir)
        files = dict(metadata.get("files") or {})
        analysis_input_path = target_dir / "analysis_input.bin"
        analysis_input_path.write_bytes(analysis_input)
        files["analysis_input"] = str(analysis_input_path)

        if denoise_result is not None:
            denoised_path = target_dir / "denoised.wav"
            save_wav(denoised_path, denoise_result.processed_audio, capture.sample_rate)
            files["denoised_wav"] = str(denoised_path)
            denoise_config = denoise_result.config.to_dict()
            denoise_metadata = dict(denoise_result.metadata)
            denoise_metadata["metrics"] = dict(denoise_result.metrics)
        else:
            denoise_config = DenoiseConfig(enabled=False).to_dict()
            denoise_metadata = {
                "enabled": False,
                "applied": False,
                "methods": [],
                "skip_reason": "direct_raw_analysis",
            }

        result_path = target_dir / "result.json"
        files["result"] = str(result_path)
        metadata.update(
            {
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "status": "diagnosed",
                "analysis_source": analysis_source,
                "denoise_config": denoise_config,
                "denoise_metadata": denoise_metadata,
                "files": files,
            }
        )
        if source_record_id:
            metadata["source_record_id"] = str(source_record_id)

        result = prediction.to_dict()
        result["record_id"] = metadata.get("record_id", target_dir.name)
        result["created_at"] = metadata.get("created_at", "")
        result["analysis_source"] = analysis_source
        _write_json(target_dir / "metadata.json", metadata)
        _write_json(result_path, result)
        return target_dir

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
        """Compatibility wrapper for callers that still complete a record in one step."""
        metrics = dict(denoise_metadata.get("metrics") or {})
        denoise_result = DenoiseResult(
            processed_audio=np.asarray(denoised_audio, dtype=np.float32),
            config=denoise_config,
            metadata=dict(denoise_metadata),
            metrics=metrics,
        )
        record_dir = self.save_capture(capture, raw_audio, hardware_config)
        return self.complete_record(
            capture=capture,
            raw_audio=raw_audio,
            hardware_config=hardware_config,
            prediction=prediction,
            analysis_source="raw",
            analysis_input=capture.legacy_input,
            denoise_result=denoise_result,
            record_dir=record_dir,
        )

    def load_capture_record(self, record_dir: str | Path) -> StoredCapture:
        resolved = self._resolve_record_dir(record_dir)
        metadata = self._read_metadata(resolved)
        self._validate_capture_files(resolved)

        hardware = HardwareConfig.from_dict(dict(metadata.get("hardware_config") or {}))
        raw_voltage = np.load(resolved / "raw_voltage.npy", allow_pickle=False).astype(np.float32)
        legacy_input = (resolved / "legacy_input.bin").read_bytes()
        if raw_voltage.size == 0 or not legacy_input:
            raise ValueError("采样记录中没有有效电压数据")
        sample_rate = int(metadata.get("sample_rate") or hardware.sample_rate)
        capture = CaptureResult(
            raw_voltage=raw_voltage,
            legacy_input=legacy_input,
            sample_rate=sample_rate,
            metadata=dict(metadata.get("capture_metadata") or {}),
        )
        return StoredCapture(
            capture=capture,
            hardware_config=hardware,
            record_dir=resolved,
            metadata=metadata,
        )

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
                    "status": metadata.get("status", "diagnosed" if result else "captured"),
                    "analysis_source": metadata.get("analysis_source", ""),
                    "source_record_id": metadata.get("source_record_id", ""),
                    "label": result.get("label", ""),
                    "class_index": result.get("class_index", ""),
                    "confidence": result.get("confidence", 0.0),
                    "record_dir": str(metadata_path.parent),
                    "metadata_path": str(metadata_path),
                    "result_path": str(result_path),
                }
            )
        return sorted(records, key=lambda item: str(item.get("created_at", "")), reverse=True)

    def _new_record_dir(self) -> Path:
        record_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        record_dir = self.records_dir / record_id
        record_dir.mkdir(parents=True, exist_ok=False)
        return record_dir

    def _resolve_record_dir(self, record_dir: str | Path) -> Path:
        resolved = Path(record_dir).resolve()
        try:
            resolved.relative_to(self.records_dir)
        except ValueError as exc:
            raise ValueError("记录目录不属于当前应用的数据目录") from exc
        if not resolved.is_dir():
            raise FileNotFoundError(f"记录目录不存在: {resolved}")
        return resolved

    @staticmethod
    def _read_metadata(record_dir: Path) -> dict[str, Any]:
        metadata_path = record_dir / "metadata.json"
        if not metadata_path.is_file():
            raise FileNotFoundError(f"记录缺少 metadata.json: {record_dir}")
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("metadata.json 内容无效")
        return data

    @staticmethod
    def _validate_capture_files(record_dir: Path) -> None:
        required = ["metadata.json", "raw_voltage.npy", "raw.wav", "legacy_input.bin"]
        missing = [name for name in required if not (record_dir / name).is_file()]
        if missing:
            raise FileNotFoundError(f"采样记录缺少文件: {', '.join(missing)}")


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
