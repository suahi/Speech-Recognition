from __future__ import annotations

import numpy as np
import pytest
import warnings

from voice_fault_diagnosis.app.waveform_display import (
    calculate_playback_envelope,
    calculate_waveform_display,
    looped_playback_position,
    normalize_playback_samples,
)


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


def test_non_divisible_envelope_has_no_nan_or_empty_tail_buckets() -> None:
    samples = np.linspace(-1.0, 1.0, 60_001, dtype=np.float32)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        display = calculate_waveform_display(samples, max_points=300)
    assert display.is_envelope
    assert len(display.y_min_values) <= 300
    assert np.isfinite(display.y_min_values).all()
    assert np.isfinite(display.y_max_values).all()


def test_playback_envelope_is_a_five_second_circular_local_window() -> None:
    samples = normalize_playback_samples(np.sin(np.linspace(0, 300 * np.pi, 16_000 * 8, dtype=np.float32)))
    envelope = calculate_playback_envelope(
        samples,
        sample_rate=16_000,
        center_seconds=7.8,
        window_seconds=5.0,
        max_points=320,
    )
    assert envelope.window_seconds == 5.0
    assert envelope.source_duration_seconds == 8.0
    assert len(envelope.y_min_values) <= 320
    assert np.isfinite(envelope.y_min_values).all()
    assert np.isfinite(envelope.y_max_values).all()


def test_playback_position_advances_and_wraps_at_the_end() -> None:
    assert looped_playback_position(1.5, 0.4, 2.0) == 1.9
    assert looped_playback_position(1.9, 0.4, 2.0) == pytest.approx(0.3)
    assert looped_playback_position(1.0, 1.0, 0.0) == 0.0
