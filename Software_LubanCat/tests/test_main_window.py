from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from voice_fault_diagnosis.app.main_window import MainWindow
from voice_fault_diagnosis.config import load_light_config


def test_main_window_exposes_only_capture_and_result_controls() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(load_light_config())

    assert window.start_button.isEnabled()
    assert not window.stop_button.isEnabled()
    assert "完成采集后" in window.result_label.text()
    assert not hasattr(window, "tabs")
    window.close()
    app.processEvents()
