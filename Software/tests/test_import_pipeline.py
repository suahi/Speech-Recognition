from __future__ import annotations

import json
from pathlib import Path
import wave

import numpy as np
import pytest

from voice_fault_diagnosis.config import load_pc_config
from voice_fault_diagnosis.models import PredictionResult
from voice_fault_diagnosis.pipeline import run_imported_wav
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


class FakeWavEngine:
    def __init__(self) -> None:
        self.wav_paths: list[Path] = []

    def predict(self, wav_path) -> PredictionResult:
        path = Path(wav_path)
        assert path.is_file()
        self.wav_paths.append(path)
        return PredictionResult(
            model_name="fake_wav_cnn",
            class_index=2,
            label="C2",
            confidence=0.75,
            probabilities=[0.05, 0.1, 0.75, 0.04, 0.03, 0.03],
            top_k=[{"class_index": 2, "label": "C2", "display_name": "敲击", "confidence": 0.75}],
            metadata={"display_name": "敲击", "source_revision": "test"},
        )


@pytest.mark.parametrize(("sample_rate", "channels"), [(8000, 1), (44100, 2)])
def test_import_archives_mono_or_stereo_wav_before_inference(tmp_path, sample_rate, channels) -> None:
    source = tmp_path / f"source_{sample_rate}_{channels}.wav"
    _write_pcm_wav(source, sample_rate=sample_rate, channels=channels, seconds=0.25)
    original_bytes = source.read_bytes()
    store = LocalRecordStore(tmp_path / "records")
    engine = FakeWavEngine()
    stages: list[int] = []

    record_dir, prediction = run_imported_wav(
        load_pc_config(),
        source,
        engine=engine,
        store=store,
        on_stage=lambda message, progress: stages.append(progress),
    )

    assert prediction.label == "C2"
    assert engine.wav_paths == [record_dir / "raw.wav"]
    assert (record_dir / "raw.wav").read_bytes() == original_bytes
    assert (record_dir / "metadata.json").is_file()
    assert (record_dir / "result.json").is_file()
    assert not (record_dir / "raw_voltage.npy").exists()
    assert stages == [10, 35, 60, 100]
    metadata = json.loads((record_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["source_type"] == "imported_wav"
    assert metadata["original_path"] == str(source.resolve())
    assert metadata["sample_rate"] == sample_rate
    assert metadata["channels"] == channels
    assert metadata["duration_seconds"] == pytest.approx(0.25, rel=0.01)
    assert metadata["status"] == "diagnosed"


@pytest.mark.parametrize("kind", ["empty", "corrupt"])
def test_invalid_wav_gives_clear_error_without_creating_record(tmp_path, kind) -> None:
    source = tmp_path / f"{kind}.wav"
    if kind == "empty":
        with wave.open(str(source), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(16000)
    else:
        source.write_bytes(b"not a wave file")
    records = tmp_path / "records"
    store = LocalRecordStore(records)

    with pytest.raises(ValueError, match="为空|损坏|不受支持"):
        run_imported_wav(load_pc_config(), source, engine=FakeWavEngine(), store=store)

    assert list(records.iterdir()) == []


def _write_pcm_wav(path: Path, *, sample_rate: int, channels: int, seconds: float) -> None:
    frame_count = int(sample_rate * seconds)
    time_axis = np.arange(frame_count, dtype=np.float32) / sample_rate
    mono = (0.2 * np.sin(2.0 * np.pi * 440.0 * time_axis) * 32767.0).astype("<i2")
    if channels == 2:
        pcm = np.column_stack((mono, -mono)).astype("<i2").reshape(-1)
    else:
        pcm = mono
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
