from __future__ import annotations

import subprocess
import sys

import pytest


def _desktop_dependencies():
    probe = subprocess.run(
        [sys.executable, "-c", "from PySide6.QtWidgets import QApplication"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip("当前 Python 环境无法加载 PySide6 Qt DLL。")
    try:
        from PySide6.QtWidgets import QApplication, QFileDialog
        from PySide6.QtTest import QTest
        from voice_fault_diagnosis.app.main_window import AudioWaveformWidget, MainWindow
        from voice_fault_diagnosis.config import load_bearing_config
    except ImportError:
        pytest.skip("当前 Python 环境无法加载 PySide6 Qt DLL。")
    return QApplication, QFileDialog, QTest, AudioWaveformWidget, MainWindow, load_bearing_config


@pytest.fixture(scope="module")
def application():
    QApplication, _, _, _, _, _ = _desktop_dependencies()
    return QApplication.instance() or QApplication([])


def test_classic_industrial_layout_and_result_hierarchy(application: QApplication) -> None:
    _, _, _, _, MainWindow, load_bearing_config = _desktop_dependencies()
    window = MainWindow(load_bearing_config())
    window.show()
    application.processEvents()
    assert window.read_button.text() == "读取音频"
    assert window.findChild(type(window.probability_chart), "probability_chart") is not None
    assert window.findChild(type(window.audio_waveform), "audio_waveform") is not None
    assert window.audio_waveform.playback_window_seconds == 5.0
    assert window.audio_waveform.scope_background == "#10202D"
    assert window.audio_waveform.scope_cursor == "#21D4FD"
    assert window.remaining_life_label.text() == "-- %"
    assert window.health_group.geometry().x() > window.waveform_group.geometry().x()
    assert window.chart_group.geometry().width() > window.audio_group.geometry().width()
    ratio = window.chart_group.geometry().width() / window.audio_group.geometry().width()
    assert 1.25 < ratio < 1.75
    assert "故障分类结果" not in window.centralWidget().findChild(type(window.waveform_group), "waveform_group").title()
    assert window.health_group.title() == "算法估计剩余寿命"
    assert "border-radius: 0" in window.styleSheet()
    window.close()


def test_cancel_keeps_view_and_failure_recovers_button(application: QApplication, monkeypatch) -> None:
    _, QFileDialog, _, _, MainWindow, load_bearing_config = _desktop_dependencies()
    window = MainWindow(load_bearing_config())
    before = window.file_path_label.text()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *args: ("", "")))
    window._choose_audio()
    assert window.file_path_label.text() == before
    window._show_error = lambda *args: None
    window.read_button.setEnabled(False)
    window._on_failed("损坏音频", "details")
    assert window.read_button.isEnabled()
    assert window.progress.value() == 0
    window.close()


def test_scope_autoplays_resets_and_stops_with_window(application: QApplication) -> None:
    import numpy as np

    _, _, QTest, AudioWaveformWidget, MainWindow, load_bearing_config = _desktop_dependencies()
    window = MainWindow(load_bearing_config())
    scope = window.audio_waveform
    scope.set_audio(np.sin(np.linspace(0, 100 * np.pi, 16_000 * 6, dtype=np.float32)), 16_000)
    assert scope.is_playing
    assert scope.playback_seconds == 0.0
    QTest.qWait(80)
    assert scope.playback_seconds > 0.0
    scope.set_audio(np.ones(16_000 * 2, dtype=np.float32), 16_000)
    assert scope.playback_seconds == 0.0
    window.close()
    assert not scope.is_playing
