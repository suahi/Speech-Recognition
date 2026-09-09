from __future__ import annotations

import os
from pathlib import Path
import time
import wave

import numpy as np
import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QFileDialog

from voice_fault_diagnosis.app.main_window import MainWindow
from voice_fault_diagnosis.config import EXPECTED_LABEL_CODES, load_pc_config
from voice_fault_diagnosis.models import PredictionResult
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


class FakeEngine:
    def predict(self, wav_path) -> PredictionResult:
        return PredictionResult(
            model_name="fake",
            class_index=4,
            label="C4",
            confidence=0.82,
            probabilities=[0.01, 0.02, 0.03, 0.05, 0.82, 0.07],
            top_k=[{"label": "C4", "display_name": "气流", "confidence": 0.82}],
            metadata={"display_name": "气流"},
        )


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_single_page_layout_prioritizes_result_and_exposes_load_button(app, tmp_path) -> None:
    window = MainWindow(load_pc_config(), engine=FakeEngine(), store=LocalRecordStore(tmp_path / "records"))
    window.show()
    app.processEvents()

    sizes = window.main_splitter.sizes()
    left_ratio = sizes[0] / sum(sizes)
    assert 0.36 <= left_ratio <= 0.44
    assert window.load_button.text() == "加载 WAV 并识别"
    assert window.start_button.isEnabled()
    assert window.load_button.isEnabled()
    assert not window.stop_button.isEnabled()
    assert window.waveform.maximumHeight() == 160
    assert tuple(window.probability_bars) == EXPECTED_LABEL_CODES
    assert len(window.probability_rows) == 6
    result_font = window.result_code_label.font()
    assert result_font.pixelSize() >= 30 or result_font.pointSize() >= 24
    assert not hasattr(window, "tabs")
    assert "border-radius" not in window.styleSheet()
    assert "gradient" not in window.styleSheet().lower()
    window.close()


def test_cancel_file_dialog_does_not_change_ui(app, tmp_path, monkeypatch) -> None:
    window = MainWindow(load_pc_config(), engine=FakeEngine(), store=LocalRecordStore(tmp_path / "records"))
    before = (window.source_label.text(), window.status_label.text(), window.progress.value())
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: ("", ""))

    window._choose_wav()

    assert (window.source_label.text(), window.status_label.text(), window.progress.value()) == before
    assert not window.is_busy
    window.close()


def test_import_runs_in_background_enforces_mutual_exclusion_and_renders_six_classes(app, tmp_path) -> None:
    source = tmp_path / "demo.wav"
    _write_wav(source)
    window = MainWindow(load_pc_config(), engine=FakeEngine(), store=LocalRecordStore(tmp_path / "records"))
    window._show_error = lambda message, details: None

    window._start_import(source)
    assert window.is_busy
    assert not window.start_button.isEnabled()
    assert not window.load_button.isEnabled()
    assert not window.stop_button.isEnabled()
    window._start_capture()
    assert window._capture_thread is None

    _wait_until_idle(app, window)

    assert window.start_button.isEnabled()
    assert window.load_button.isEnabled()
    assert not window.stop_button.isEnabled()
    assert window.result_code_label.text() == "C4  气流"
    assert window.confidence_label.text() == "置信度：82.00%"
    assert window.probability_bars["C4"].format() == "82.00%"
    assert window.probability_rows["C4"].property("winning") == "true"
    assert "模型输入：单声道 / 16000 Hz" in window.input_label.text()
    window.close()


def test_corrupt_import_reports_error_and_restores_buttons(app, tmp_path) -> None:
    source = tmp_path / "broken.wav"
    source.write_bytes(b"broken")
    window = MainWindow(load_pc_config(), engine=FakeEngine(), store=LocalRecordStore(tmp_path / "records"))
    errors: list[str] = []
    window._show_error = lambda message, details: errors.append(message)

    window._start_import(source)
    _wait_until_idle(app, window)

    assert errors
    assert "损坏" in errors[0] or "不受支持" in errors[0]
    assert window.status_label.text() == "任务失败"
    assert window.start_button.isEnabled()
    assert window.load_button.isEnabled()
    assert not window.stop_button.isEnabled()
    window.close()


def _wait_until_idle(app: QApplication, window: MainWindow, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while window.is_busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.005)
    app.processEvents()
    assert not window.is_busy


def _write_wav(path: Path) -> None:
    sample_rate = 22050
    time_axis = np.arange(sample_rate // 4, dtype=np.float32) / sample_rate
    pcm = (0.2 * np.sin(2.0 * np.pi * 440.0 * time_axis) * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
