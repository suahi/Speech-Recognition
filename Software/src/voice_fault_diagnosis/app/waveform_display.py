from __future__ import annotations

from dataclasses import dataclass

import numpy as np


MIN_DISPLAY_SPAN_VOLTS = 0.001


@dataclass(frozen=True)
class WaveformDisplay:
    samples: np.ndarray
    y_values: np.ndarray
    lower_volts: float
    center_volts: float
    upper_volts: float
    mean_volts: float
    ac_rms_volts: float
    peak_to_peak_volts: float
    display_scale: float
    mode_name: str


def calculate_waveform_display(
    voltage: np.ndarray,
    *,
    adaptive: bool = True,
    full_scale_volts: float = 5.0,
    max_points: int = 5000,
    min_span_volts: float = MIN_DISPLAY_SPAN_VOLTS,
) -> WaveformDisplay:
    samples = np.asarray(voltage, dtype=np.float32)
    if samples.size > max_points:
        samples = samples[:: max(1, samples.size // max_points)]
    samples = samples.astype(np.float32, copy=False)

    if samples.size == 0:
        full_scale = max(float(full_scale_volts), float(min_span_volts) / 2.0)
        return WaveformDisplay(
            samples=samples,
            y_values=np.zeros(0, dtype=np.float32),
            lower_volts=-full_scale,
            center_volts=0.0,
            upper_volts=full_scale,
            mean_volts=0.0,
            ac_rms_volts=0.0,
            peak_to_peak_volts=0.0,
            display_scale=1.0,
            mode_name="full-scale" if not adaptive else "adaptive-ac",
        )

    mean = float(np.mean(samples))
    centered = samples - mean
    ac_rms = float(np.sqrt(np.mean(centered * centered)))
    peak_to_peak = float(np.max(samples) - np.min(samples))
    full_scale = max(float(full_scale_volts), float(min_span_volts) / 2.0)

    if adaptive:
        p1, p99 = np.percentile(centered, [1.0, 99.0])
        clipped_centered = np.clip(centered, float(p1), float(p99))
        robust_rms = float(np.sqrt(np.mean(clipped_centered * clipped_centered)))
        robust_half_span = max(abs(float(p1)), abs(float(p99)), robust_rms * 3.0)
        half_span = max(robust_half_span, float(min_span_volts) / 2.0)
        center = mean
        mode_name = "adaptive-ac"
    else:
        half_span = full_scale
        center = 0.0
        mode_name = "full-scale"

    lower = center - half_span
    upper = center + half_span
    if peak_to_peak <= max(float(min_span_volts) * 1e-6, 1e-12):
        y_values = np.zeros_like(samples, dtype=np.float32)
    else:
        y_values = np.clip((samples - center) / half_span, -1.0, 1.0).astype(np.float32)
    display_scale = max(1.0, full_scale / half_span) if adaptive else 1.0

    return WaveformDisplay(
        samples=samples,
        y_values=y_values,
        lower_volts=float(lower),
        center_volts=float(center),
        upper_volts=float(upper),
        mean_volts=mean,
        ac_rms_volts=ac_rms,
        peak_to_peak_volts=peak_to_peak,
        display_scale=float(display_scale),
        mode_name=mode_name,
    )
