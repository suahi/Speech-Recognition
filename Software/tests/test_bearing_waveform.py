from __future__ import annotations

import numpy as np

from voice_fault_diagnosis.app.waveform_display import calculate_waveform_display


def test_full_audio_waveform_is_envelope_downsampled_and_normalized() -> None:
    samples = np.sin(np.linspace(0, 200 * np.pi, 64_000, dtype=np.float32))
    display = calculate_waveform_display(samples, adaptive=True, full_scale_volts=1.0, max_points=300, min_span_volts=1e-5)
    assert display.is_envelope
    assert len(display.y_min_values) == 300
    assert len(display.y_max_values) == 300
    assert np.max(np.abs(display.y_values)) <= 1.0


def test_empty_audio_waveform_has_no_points() -> None:
    display = calculate_waveform_display(np.asarray([], dtype=np.float32), max_points=300)
    assert display.samples.size == 0
    assert display.y_values.size == 0
