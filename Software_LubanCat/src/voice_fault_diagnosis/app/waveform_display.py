from __future__ import annotations

from dataclasses import dataclass

import numpy as np


MIN_DISPLAY_SPAN_VOLTS = 0.001


@dataclass(frozen=True)
class WaveformDisplay:
    samples: np.ndarray
    y_values: np.ndarray
    y_min_values: np.ndarray
    y_max_values: np.ndarray
    lower_volts: float
    center_volts: float
    upper_volts: float
    mean_volts: float
    ac_rms_volts: float
    peak_to_peak_volts: float
    display_scale: float
    mode_name: str
    is_envelope: bool = False


def calculate_waveform_display(
    voltage: np.ndarray,
    *,
    adaptive: bool = True,
    full_scale_volts: float = 5.0,
    max_points: int = 5000,
    min_span_volts: float = MIN_DISPLAY_SPAN_VOLTS,
) -> WaveformDisplay:
    raw_samples = np.asarray(voltage, dtype=np.float32).reshape(-1)

    if raw_samples.size == 0:
        full_scale = max(float(full_scale_volts), float(min_span_volts) / 2.0)
        empty = np.zeros(0, dtype=np.float32)
        return WaveformDisplay(
            samples=empty,
            y_values=empty,
            y_min_values=empty,
            y_max_values=empty,
            lower_volts=-full_scale,
            center_volts=0.0,
            upper_volts=full_scale,
            mean_volts=0.0,
            ac_rms_volts=0.0,
            peak_to_peak_volts=0.0,
            display_scale=1.0,
            mode_name="full-scale" if not adaptive else "adaptive-ac",
        )

    mean = float(np.mean(raw_samples))
    centered = raw_samples - mean
    ac_rms = float(np.sqrt(np.mean(centered * centered)))
    peak_to_peak = float(np.max(raw_samples) - np.min(raw_samples))
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
        y_all = np.zeros_like(raw_samples, dtype=np.float32)
    else:
        y_all = np.clip((raw_samples - center) / half_span, -1.0, 1.0).astype(np.float32)
    display_scale = max(1.0, full_scale / half_span) if adaptive else 1.0

    samples, y_values, y_min_values, y_max_values, is_envelope = _prepare_display_series(
        raw_samples,
        y_all,
        max_points=max_points,
    )

    return WaveformDisplay(
        samples=samples,
        y_values=y_values,
        y_min_values=y_min_values,
        y_max_values=y_max_values,
        lower_volts=float(lower),
        center_volts=float(center),
        upper_volts=float(upper),
        mean_volts=mean,
        ac_rms_volts=ac_rms,
        peak_to_peak_volts=peak_to_peak,
        display_scale=float(display_scale),
        mode_name=mode_name,
        is_envelope=is_envelope,
    )


def _prepare_display_series(
    samples: np.ndarray,
    y_values: np.ndarray,
    *,
    max_points: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, bool]:
    max_points = max(2, int(max_points))
    if samples.size <= max_points:
        display_samples = samples.astype(np.float32, copy=False)
        display_y = y_values.astype(np.float32, copy=False)
        return display_samples, display_y, display_y, display_y, False

    bucket_count = max_points
    bucket_size = int(np.ceil(samples.size / float(bucket_count)))
    padded_size = bucket_count * bucket_size
    pad_count = padded_size - samples.size
    if pad_count:
        padded_y = np.pad(y_values, (0, pad_count), mode="constant", constant_values=np.nan)
    else:
        padded_y = y_values
    buckets = padded_y.reshape(bucket_count, bucket_size)
    y_min = np.nanmin(buckets, axis=1).astype(np.float32)
    y_max = np.nanmax(buckets, axis=1).astype(np.float32)
    sample_indexes = np.minimum(np.arange(bucket_count) * bucket_size, samples.size - 1)
    display_samples = samples[sample_indexes].astype(np.float32, copy=False)

    interleaved = np.empty(bucket_count * 2, dtype=np.float32)
    interleaved[0::2] = y_min
    interleaved[1::2] = y_max
    return display_samples, interleaved, y_min, y_max, True
