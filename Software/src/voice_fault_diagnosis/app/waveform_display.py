from __future__ import annotations

from dataclasses import dataclass

import numpy as np


MIN_DISPLAY_SPAN_VOLTS = 0.001
MIN_COMPARISON_HALF_SPAN_VOLTS = 0.0005


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


@dataclass(frozen=True)
class SharedWaveformScale:
    center_volts: float
    half_span_volts: float


@dataclass(frozen=True)
class PlaybackEnvelope:
    """One bounded, circular audio window ready for a scrolling scope."""

    y_min_values: np.ndarray
    y_max_values: np.ndarray
    center_seconds: float
    window_seconds: float
    source_duration_seconds: float


def calculate_shared_scale(raw_voltage: np.ndarray) -> SharedWaveformScale:
    raw = np.asarray(raw_voltage, dtype=np.float32).reshape(-1)
    if raw.size == 0:
        return SharedWaveformScale(center_volts=0.0, half_span_volts=1.0)
    center = float(np.mean(raw))
    centered = raw - center
    p1, p99 = np.percentile(centered, [1.0, 99.0])
    ac_rms = float(np.sqrt(np.mean(centered.astype(np.float64) ** 2)))
    half_span = max(
        abs(float(p1)),
        abs(float(p99)),
        ac_rms * 3.0,
        MIN_COMPARISON_HALF_SPAN_VOLTS,
    )
    return SharedWaveformScale(center_volts=center, half_span_volts=half_span)


def normalize_playback_samples(
    samples: np.ndarray,
    *,
    min_span: float = MIN_DISPLAY_SPAN_VOLTS,
) -> np.ndarray:
    """Normalize one decoded file once for efficient repeated scope rendering."""

    values = np.nan_to_num(
        np.asarray(samples, dtype=np.float32).reshape(-1),
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )
    if values.size == 0:
        return values
    center = float(np.mean(values))
    centered = values - center
    p1, p99 = np.percentile(centered, [1.0, 99.0])
    clipped = np.clip(centered, float(p1), float(p99))
    robust_rms = float(np.sqrt(np.mean(clipped * clipped)))
    half_span = max(abs(float(p1)), abs(float(p99)), robust_rms * 3.0, float(min_span) / 2.0)
    return np.clip(centered / half_span, -1.0, 1.0).astype(np.float32, copy=False)


def calculate_playback_envelope(
    normalized_samples: np.ndarray,
    *,
    sample_rate: int,
    center_seconds: float,
    window_seconds: float = 5.0,
    max_points: int = 600,
) -> PlaybackEnvelope:
    """Return a circular, pixel-bounded envelope centered on the playhead."""

    values = np.nan_to_num(
        np.asarray(normalized_samples, dtype=np.float32).reshape(-1),
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )
    rate = max(1, int(sample_rate))
    window = max(0.1, float(window_seconds))
    if values.size == 0:
        empty = np.zeros(0, dtype=np.float32)
        return PlaybackEnvelope(empty, empty, 0.0, window, 0.0)

    source_duration = values.size / float(rate)
    playhead = looped_playback_position(center_seconds, 0.0, source_duration)
    window_samples = max(2, int(round(window * rate)))
    center_index = int(round(playhead * rate))
    start_index = center_index - window_samples // 2
    indexes = np.mod(start_index + np.arange(window_samples, dtype=np.int64), values.size)
    viewport = values[indexes]
    bucket_size = int(np.ceil(viewport.size / float(max(2, int(max_points)))))
    bucket_count = int(np.ceil(viewport.size / float(bucket_size)))
    padded_size = bucket_count * bucket_size
    if padded_size > viewport.size:
        viewport = np.pad(viewport, (0, padded_size - viewport.size), mode="edge")
    buckets = viewport.reshape(bucket_count, bucket_size)
    return PlaybackEnvelope(
        y_min_values=np.min(buckets, axis=1).astype(np.float32),
        y_max_values=np.max(buckets, axis=1).astype(np.float32),
        center_seconds=playhead,
        window_seconds=window,
        source_duration_seconds=source_duration,
    )


def looped_playback_position(position_seconds: float, elapsed_seconds: float, duration_seconds: float) -> float:
    """Advance a visual-only playhead while continuously looping its source."""

    duration = max(0.0, float(duration_seconds))
    if duration <= 0.0:
        return 0.0
    return (max(0.0, float(position_seconds)) + max(0.0, float(elapsed_seconds))) % duration


def calculate_waveform_display(
    voltage: np.ndarray,
    *,
    adaptive: bool = True,
    full_scale_volts: float = 5.0,
    max_points: int = 5000,
    min_span_volts: float = MIN_DISPLAY_SPAN_VOLTS,
) -> WaveformDisplay:
    raw_samples = np.nan_to_num(
        np.asarray(voltage, dtype=np.float32).reshape(-1),
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

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

    bucket_size = int(np.ceil(samples.size / float(max_points)))
    bucket_count = int(np.ceil(samples.size / float(bucket_size)))
    padded_size = bucket_count * bucket_size
    pad_count = padded_size - samples.size
    if pad_count:
        padded_y = np.pad(y_values, (0, pad_count), mode="edge")
    else:
        padded_y = y_values
    buckets = padded_y.reshape(bucket_count, bucket_size)
    y_min = np.min(buckets, axis=1).astype(np.float32)
    y_max = np.max(buckets, axis=1).astype(np.float32)
    sample_indexes = np.minimum(np.arange(bucket_count) * bucket_size, samples.size - 1)
    display_samples = samples[sample_indexes].astype(np.float32, copy=False)

    interleaved = np.empty(bucket_count * 2, dtype=np.float32)
    interleaved[0::2] = y_min
    interleaved[1::2] = y_max
    return display_samples, interleaved, y_min, y_max, True
