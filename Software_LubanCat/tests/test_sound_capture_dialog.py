from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from voice_fault_diagnosis.app.main_window import SoundCaptureCheckDialog
from voice_fault_diagnosis.diagnostics.sound_capture import CaptureCheckResult, analyze_capture_pair
from voice_fault_diagnosis.models import HardwareConfig, MultiChannelCaptureResult


def test_sound_check_dialog_requires_two_stages_and_recheck_after_applying(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    sample_rate = 8000
    sample_count = sample_rate
    rng = np.random.default_rng(13)
    quiet = rng.normal(0.0, 0.0001, size=(sample_count, 4)).astype(np.float32)
    noise = rng.normal(0.0, 0.0001, size=(sample_count, 4)).astype(np.float32)
    time_axis = np.arange(sample_count, dtype=np.float32) / sample_rate
    noise[:, 1] += 0.003 * np.sin(2.0 * np.pi * 750.0 * time_axis)
    hardware = HardwareConfig(sample_rate=sample_rate, adc_channel=1, input_range_volts=0.1)
    dialog = SoundCaptureCheckDialog(hardware)

    assert dialog.quiet_button.isEnabled()
    assert not dialog.noise_button.isEnabled()
    dialog._on_stage_completed(
        "quiet",
        MultiChannelCaptureResult(quiet, sample_rate, {"stage": "quiet"}),
    )
    dialog._update_controls()
    assert dialog.noise_button.isEnabled()

    report = analyze_capture_pair(quiet, noise, sample_rate, 0.1, selected_channel=1)
    (tmp_path / "summary.txt").write_text("synthetic report", encoding="utf-8")
    dialog._on_analysis_completed(CaptureCheckResult(report=report, output_dir=tmp_path))
    dialog._update_controls()
    assert dialog.apply_button.isEnabled()
    assert dialog.table.rowCount() == 4

    applied: list[tuple[int, float]] = []
    dialog.recommendation_applied.connect(
        lambda channel, input_range: applied.append((int(channel), float(input_range)))
    )
    dialog._apply_recommendation()

    assert applied == [(2, 0.02)]
    assert hardware.adc_channel == 2
    assert hardware.input_range_volts == 0.02
    assert not dialog.noise_button.isEnabled()
    assert not dialog.apply_button.isEnabled()
    dialog.close()
    app.processEvents()
