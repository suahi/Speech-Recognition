from __future__ import annotations

import numpy as np

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import QWidget
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PySide6 is required to render waveform comparisons") from exc

from voice_fault_diagnosis.app.waveform_display import calculate_shared_scale


class ComparisonWaveformWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(390)
        self._raw = np.zeros(0, dtype=np.float32)
        self._processed: np.ndarray | None = None
        self._sample_rate = 50000
        self._start_sample = 0
        self._window_samples = self._sample_rate
        self._scale = calculate_shared_scale(self._raw)

    @property
    def sample_count(self) -> int:
        return int(self._raw.size)

    @property
    def sample_rate(self) -> int:
        return int(self._sample_rate)

    @property
    def max_start_sample(self) -> int:
        return max(0, self.sample_count - self._window_samples)

    def set_signals(
        self,
        raw_voltage: np.ndarray,
        processed_voltage: np.ndarray | None,
        sample_rate: int,
    ) -> None:
        raw = np.asarray(raw_voltage, dtype=np.float32).reshape(-1)
        processed = None if processed_voltage is None else np.asarray(processed_voltage, dtype=np.float32).reshape(-1)
        if processed is not None and processed.size != raw.size:
            raise ValueError("raw and processed waveforms must have the same length")
        self._raw = raw
        self._processed = processed
        self._sample_rate = max(1, int(sample_rate))
        self._scale = calculate_shared_scale(raw)
        self._window_samples = min(max(1, self._window_samples), max(1, raw.size))
        self._start_sample = min(self._start_sample, self.max_start_sample)
        self.update()

    def set_window(self, start_sample: int, window_seconds: float) -> None:
        self._window_samples = max(1, int(round(max(0.01, float(window_seconds)) * self._sample_rate)))
        self._window_samples = min(self._window_samples, max(1, self.sample_count))
        self._start_sample = max(0, min(int(start_sample), self.max_start_sample))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        outer = self.rect().adjusted(1, 1, -1, -1)
        painter.fillRect(outer, QColor("#101820"))

        gap = 12
        panel_height = max(1, (outer.height() - gap) // 2)
        raw_rect = outer.adjusted(0, 0, 0, -(panel_height + gap))
        processed_rect = outer.adjusted(0, panel_height + gap, 0, 0)
        self._paint_panel(painter, raw_rect, "原始电压波形", self._raw, QColor("#55d6be"))
        self._paint_panel(painter, processed_rect, "降噪后电压波形", self._processed, QColor("#f4b860"))

    def _paint_panel(
        self,
        painter: QPainter,
        panel_rect,
        title: str,
        values: np.ndarray | None,
        color: QColor,
    ) -> None:
        plot = panel_rect.adjusted(88, 24, -14, -24)
        painter.setPen(QColor("#d7e1ec"))
        painter.drawText(panel_rect.adjusted(12, 2, -8, 0), Qt.AlignTop | Qt.AlignLeft, title)

        painter.setPen(QPen(QColor("#263848"), 1))
        for index in range(1, 4):
            y = plot.top() + index * plot.height() / 4
            painter.drawLine(plot.left(), int(y), plot.right(), int(y))
        for index in range(1, 6):
            x = plot.left() + index * plot.width() / 6
            painter.drawLine(int(x), plot.top(), int(x), plot.bottom())

        center = self._scale.center_volts
        half_span = self._scale.half_span_volts
        painter.setPen(QColor("#aebed0"))
        painter.drawText(panel_rect.left() + 8, plot.top() + 10, _format_volts(center + half_span))
        painter.drawText(panel_rect.left() + 8, plot.center().y() + 4, _format_volts(center))
        painter.drawText(panel_rect.left() + 8, plot.bottom(), _format_volts(center - half_span))

        start_seconds = self._start_sample / float(self._sample_rate)
        end_sample = min(self.sample_count, self._start_sample + self._window_samples)
        end_seconds = end_sample / float(self._sample_rate)
        painter.drawText(plot.left(), panel_rect.bottom() - 5, f"{start_seconds:.3f} s")
        painter.drawText(plot, Qt.AlignRight | Qt.AlignBottom, f"{end_seconds:.3f} s")

        painter.setPen(QPen(QColor("#426177"), 1.1))
        painter.drawLine(plot.left(), plot.center().y(), plot.right(), plot.center().y())
        if values is None:
            painter.setPen(QColor("#8fa2b6"))
            painter.drawText(plot, Qt.AlignCenter, "尚未应用降噪")
            return
        if values.size < 2:
            painter.setPen(QColor("#8fa2b6"))
            painter.drawText(plot, Qt.AlignCenter, "暂无波形数据")
            return

        segment = values[self._start_sample : end_sample]
        if segment.size < 2:
            return
        normalized = np.clip((segment - center) / half_span, -1.0, 1.0)
        y_min, y_max = _downsample_envelope(normalized, max(2, plot.width() - 8))
        width = max(1, plot.width() - 8)
        center_y = plot.center().y()
        y_scale = plot.height() * 0.5
        painter.setPen(QPen(color, 1.0))
        midpoints: list[tuple[int, int]] = []
        for index, (minimum, maximum) in enumerate(zip(y_min, y_max)):
            x = plot.left() + 4 + index * width / max(1, y_min.size - 1)
            top = center_y - float(maximum) * y_scale
            bottom = center_y - float(minimum) * y_scale
            painter.drawLine(int(x), int(top), int(x), int(bottom))
            midpoints.append((int(x), int((top + bottom) * 0.5)))
        painter.setPen(QPen(color.lighter(125), 0.8))
        for left, right in zip(midpoints, midpoints[1:]):
            painter.drawLine(left[0], left[1], right[0], right[1])


def _downsample_envelope(values: np.ndarray, max_points: int) -> tuple[np.ndarray, np.ndarray]:
    source = np.asarray(values, dtype=np.float32).reshape(-1)
    max_points = max(2, int(max_points))
    if source.size <= max_points:
        return source, source
    bucket_size = int(np.ceil(source.size / float(max_points)))
    bucket_count = int(np.ceil(source.size / float(bucket_size)))
    padded_size = bucket_count * bucket_size
    if padded_size != source.size:
        source = np.pad(source, (0, padded_size - source.size), mode="constant", constant_values=np.nan)
    buckets = source.reshape(bucket_count, bucket_size)
    return np.nanmin(buckets, axis=1), np.nanmax(buckets, axis=1)


def _format_volts(value: float) -> str:
    absolute = abs(float(value))
    if absolute >= 1.0:
        return f"{value:.3f} V"
    if absolute >= 0.001:
        return f"{value * 1000.0:.2f} mV"
    return f"{value * 1_000_000.0:.1f} uV"
