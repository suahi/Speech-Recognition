from __future__ import annotations

import json
from pathlib import Path
import subprocess

import numpy as np
import pytest
import soundfile as sf

from voice_fault_diagnosis.audio_io import AudioDecodeError, load_audio
from voice_fault_diagnosis.config import load_bearing_config
from voice_fault_diagnosis.pipeline import run_bearing_diagnosis
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


def _write_wave(path: Path, *, sample_rate: int = 22_050, channels: int = 1) -> None:
    moments = np.arange(sample_rate * 2, dtype=np.float32) / sample_rate
    mono = (0.12 * np.sin(2 * np.pi * 230 * moments)).astype(np.float32)
    values = mono if channels == 1 else np.column_stack((mono, mono * 0.65))
    sf.write(path, values, sample_rate)


@pytest.mark.parametrize("channels", [1, 2])
def test_wav_is_downmixed_and_resampled(tmp_path: Path, channels: int) -> None:
    source = tmp_path / f"input_{channels}.wav"
    _write_wave(source, channels=channels)
    values, info = load_audio(source)
    assert info.format == "WAV"
    assert info.channels == channels
    assert info.sample_rate == 22_050
    assert info.decoded_sample_rate == 16_000
    assert values.dtype == np.float32
    assert len(values) == pytest.approx(32_000, abs=4)


def test_m4a_uses_project_decoder_without_system_ffmpeg(tmp_path: Path) -> None:
    wav_path = tmp_path / "source.wav"
    m4a_path = tmp_path / "source.m4a"
    _write_wave(wav_path, sample_rate=48_000, channels=2)
    import imageio_ffmpeg

    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(wav_path), "-c:a", "aac", str(m4a_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    values, info = load_audio(m4a_path)
    assert info.format == "M4A"
    assert info.channels == 2
    assert info.sample_rate == 48_000
    assert info.decoder == "imageio-ffmpeg"
    assert len(values) == pytest.approx(32_000, abs=100)


def test_empty_and_broken_audio_return_clear_errors(tmp_path: Path) -> None:
    empty = tmp_path / "empty.wav"
    empty.write_bytes(b"")
    broken = tmp_path / "broken.m4a"
    broken.write_bytes(b"not audio")
    with pytest.raises(AudioDecodeError, match="为空"):
        load_audio(empty)
    with pytest.raises(AudioDecodeError, match="无法解码"):
        load_audio(broken)


def test_pipeline_archives_original_audio_and_result(tmp_path: Path) -> None:
    source = tmp_path / "bearing.wav"
    _write_wave(source, sample_rate=16_000)
    store = LocalRecordStore(tmp_path / "records")
    record_dir, prediction = run_bearing_diagnosis(load_bearing_config(), source, store=store)
    assert (record_dir / "source.wav").is_file()
    metadata = json.loads((record_dir / "metadata.json").read_text(encoding="utf-8"))
    result = json.loads((record_dir / "result.json").read_text(encoding="utf-8"))
    assert metadata["source_type"] == "imported_bearing_audio"
    assert metadata["decode"]["decoded_sample_rate"] == 16_000
    assert metadata["segment_count"] == prediction.segment_count
    assert result["health_index"] == prediction.health_index
    assert "不能替代真实寿命" in result["health_index_disclaimer"]
