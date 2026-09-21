from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import shutil
from typing import Any
import uuid

from voice_fault_diagnosis.audio_io import AudioSourceInfo, is_supported_audio
from voice_fault_diagnosis.models import BearingPredictionResult
from voice_fault_diagnosis.paths import RECORDS_DIR


class LocalRecordStore:
    """Filesystem-only storage for imported bearing audio diagnoses."""

    def __init__(self, records_dir: str | Path = RECORDS_DIR) -> None:
        self.records_dir = Path(records_dir).resolve()
        self.records_dir.mkdir(parents=True, exist_ok=True)

    def begin_import(self, source_path: str | Path, source_info: AudioSourceInfo) -> Path:
        original_path = Path(source_path).resolve()
        if not original_path.is_file():
            raise FileNotFoundError(f"音频文件不存在：{original_path}")
        if not is_supported_audio(original_path):
            raise ValueError("仅支持 M4A 或 WAV 音频文件。")
        record_id, record_dir = self._new_record_dir()
        archived_path = record_dir / f"source{original_path.suffix.lower()}"
        shutil.copy2(original_path, archived_path)
        created_at = datetime.now().isoformat(timespec="seconds")
        _write_json(
            record_dir / "metadata.json",
            {
                "record_id": record_id,
                "created_at": created_at,
                "updated_at": created_at,
                "status": "archived",
                "source_type": "imported_bearing_audio",
                "original_path": str(original_path),
                "decode": source_info.to_dict(),
                "files": {"source_audio": str(archived_path)},
            },
        )
        return record_dir

    def complete_record(self, record_dir: str | Path, prediction: BearingPredictionResult) -> Path:
        resolved = self._resolve_record_dir(record_dir)
        metadata = self.read_metadata(resolved)
        source_path = Path(str(metadata.get("files", {}).get("source_audio", "")))
        if not source_path.is_file():
            raise FileNotFoundError(f"记录缺少已归档音频：{resolved}")
        result_path = resolved / "result.json"
        result = prediction.to_dict()
        result.update(
            {
                "record_id": metadata["record_id"],
                "created_at": metadata["created_at"],
            }
        )
        _write_json(result_path, result)
        files = dict(metadata.get("files") or {})
        files["result"] = str(result_path)
        metadata.update(
            {
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "status": "diagnosed",
                "segment_count": prediction.segment_count,
                "model": dict(prediction.metadata),
                "files": files,
            }
        )
        _write_json(resolved / "metadata.json", metadata)
        return resolved

    def read_metadata(self, record_dir: str | Path) -> dict[str, Any]:
        path = self._resolve_record_dir(record_dir) / "metadata.json"
        if not path.is_file():
            raise FileNotFoundError(f"记录缺少 metadata.json：{path.parent}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"metadata.json 内容无效：{path.parent}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"metadata.json 内容无效：{path.parent}")
        return data

    def source_audio_path(self, record_dir: str | Path) -> Path:
        metadata = self.read_metadata(record_dir)
        source = Path(str(metadata.get("files", {}).get("source_audio", "")))
        if not source.is_file():
            raise FileNotFoundError(f"记录缺少已归档音频：{Path(record_dir)}")
        return source

    def _new_record_dir(self) -> tuple[str, Path]:
        record_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        record_dir = self.records_dir / record_id
        record_dir.mkdir(parents=True, exist_ok=False)
        return record_id, record_dir

    def _resolve_record_dir(self, value: str | Path) -> Path:
        record_dir = Path(value).resolve()
        try:
            record_dir.relative_to(self.records_dir)
        except ValueError as exc:
            raise ValueError("记录目录不属于当前应用的数据目录。") from exc
        if not record_dir.is_dir():
            raise FileNotFoundError(f"记录目录不存在：{record_dir}")
        return record_dir


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
