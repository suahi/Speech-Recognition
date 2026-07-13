from __future__ import annotations

import numpy as np

from voice_fault_diagnosis.app.waveform_display import calculate_waveform_display


def test_adaptive_display_expands_small_ac_signal_with_dc_bias() -> None:
    phase = np.linspace(0.0, 2.0 * np.pi, 2000, dtype=np.float32)
    voltage = -0.046 + 0.001 * np.sin(phase)

    display = calculate_waveform_display(voltage, adaptive=True, full_scale_volts=5.0)

    assert display.mode_name == "adaptive-ac"
    assert abs(display.center_volts + 0.046) < 1e-4
    assert display.upper_volts - display.lower_volts < 0.01
    assert display.display_scale > 1000.0
    assert float(np.max(display.y_values)) > 0.2
    assert float(np.min(display.y_values)) < -0.2


def test_full_scale_display_keeps_absolute_voltage_range() -> None:
    voltage = np.array([-0.046, -0.045, -0.044], dtype=np.float32)

    display = calculate_waveform_display(voltage, adaptive=False, full_scale_volts=5.0)

    assert display.mode_name == "full-scale"
    assert display.lower_volts == -5.0
    assert display.center_volts == 0.0
    assert display.upper_volts == 5.0
    assert display.display_scale == 1.0


def test_adaptive_display_uses_minimum_span_for_constant_signal() -> None:
    voltage = np.full(256, 0.123, dtype=np.float32)

    display = calculate_waveform_display(voltage, adaptive=True, full_scale_volts=5.0)

    assert display.upper_volts > display.lower_volts
    assert display.upper_volts - display.lower_volts >= 0.001
    assert np.all(np.isfinite(display.y_values))
    assert np.allclose(display.y_values, 0.0)


def test_adaptive_display_is_not_flattened_by_single_spike() -> None:
    phase = np.linspace(0.0, 2.0 * np.pi, 2000, dtype=np.float32)
    voltage = -0.046 + 0.001 * np.sin(phase)
    voltage[0] = 1.0

    display = calculate_waveform_display(voltage, adaptive=True, full_scale_volts=5.0)

    assert display.upper_volts - display.lower_volts < 0.02
    assert float(np.max(display.y_values)) == 1.0
    assert float(np.min(display.y_values[1:])) < -0.2


def test_large_display_uses_min_max_envelope_instead_of_simple_decimation() -> None:
    voltage = np.tile(np.array([-0.001, 0.001], dtype=np.float32), 5000)

    display = calculate_waveform_display(voltage, adaptive=True, full_scale_volts=5.0, max_points=100)

    assert display.is_envelope
    assert display.y_min_values.size == 100
    assert display.y_max_values.size == 100
    assert float(np.min(display.y_min_values)) < -0.2
    assert float(np.max(display.y_max_values)) > 0.2
