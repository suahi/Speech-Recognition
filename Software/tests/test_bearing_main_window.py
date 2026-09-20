from __future__ import annotations

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QFileDialog  # noqa: E402

from voice_fault_diagnosis.app.main_window import MainWindow  # noqa: E402
from voice_fault_diagnosis.config import load_bearing_config  # noqa: E402
from voice_fault_diagnosis.models import CLASS_IDS  # noqa: E402


@pytest.fixture(scope="module")
def application() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_classic_industrial_layout_and_result_hierarchy(application: QApplication) -> None:
    window = MainWindow(load_bearing_config())
    window.show()
    application.processEvents()
    assert window.read_button.text() == "读取音频"
    assert window.findChild(type(window.probability_chart), "probability_chart") is not None
    assert set(window.probability_bars) == set(CLASS_IDS)
    assert window.health_index_label.text() == "-- %"
    assert window.health_group.geometry().x() > window.classification_group.geometry().x()
    assert window.chart_group.geometry().width() > window.audio_group.geometry().width()
    ratio = window.chart_group.geometry().width() / window.audio_group.geometry().width()
    assert 1.25 < ratio < 1.75
    assert "border-radius: 0" in window.styleSheet()
    window.close()


def test_cancel_keeps_view_and_failure_recovers_button(application: QApplication, monkeypatch) -> None:
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
