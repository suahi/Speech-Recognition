from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from voice_fault_diagnosis.config import load_pc_config
from voice_fault_diagnosis.pipeline import run_imported_wav
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("torch") is None or importlib.util.find_spec("librosa") is None,
    reason="torch and librosa are required for the repository WAV demonstration",
)


def test_repository_ten_second_wav_creates_complete_demo_record(tmp_path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    source = repository_root / "CodeSource" / "python_continuous_sampling" / "_ch1.wav"
    assert source.is_file()

    record_dir, prediction = run_imported_wav(
        load_pc_config(),
        source,
        store=LocalRecordStore(tmp_path / "records"),
    )

    assert prediction.label in {"C0", "C1", "C2", "C3", "C4", "C5"}
    assert (record_dir / "raw.wav").is_file()
    assert (record_dir / "metadata.json").is_file()
    assert (record_dir / "result.json").is_file()
    metadata = json.loads((record_dir / "metadata.json").read_text(encoding="utf-8"))
    result = json.loads((record_dir / "result.json").read_text(encoding="utf-8"))
    assert metadata["source_type"] == "imported_wav"
    assert metadata["sample_rate"] == 50000
    assert metadata["channels"] == 1
    assert 9.5 <= metadata["duration_seconds"] <= 10.5
    assert metadata["status"] == "diagnosed"
    assert len(result["probabilities"]) == 6
