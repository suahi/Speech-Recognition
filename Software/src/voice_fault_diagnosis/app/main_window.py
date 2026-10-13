from __future__ import annotations

import csv
import os
from pathlib import Path
from time import monotonic
import traceback

import numpy as np

try:
    from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
    from PySide6.QtGui import QColor, QFont, QPainter, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - exercised only without desktop extra
    raise RuntimeError("桌面界面依赖未安装，请运行：python -m pip install -e .[desktop]") from exc

from voice_fault_diagnosis.config import BearingAppConfig, BearingConfigError, load_bearing_config
from voice_fault_diagnosis.app.waveform_display import (
    calculate_playback_envelope,
    looped_playback_position,
    normalize_playback_samples,
)
from voice_fault_diagnosis.inference.bearing import BearingDiagnosticEngine
from voice_fault_diagnosis.models import CLASS_IDS
from voice_fault_diagnosis.paths import BEARING_MODEL_DIR
from voice_fault_diagnosis.pipeline import run_bearing_diagnosis
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


BLUE = "#0072BD"
BLUE_DARK = "#005A95"
ERROR_RED = "#A12622"
TEXT = "#202020"
MUTED = "#595959"
BACKGROUND = "#F0F0F0"
PANEL = "#F7F7F7"
BORDER = "#B7B7B7"
PROCESSING_STEPS = ("音频解码", "模型加载", "特征与分类", "寿命计算")


class ProbabilityChartWidget(QWidget):
    """A deliberately simple, MATLAB-like three-column probability chart."""

    def __init__(self, labels: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("probability_chart")
        self.setMinimumHeight(190)
        self._labels = labels
        self._probabilities = {class_id: 0.0 for class_id in CLASS_IDS}

    def set_probabilities(self, probabilities: dict[str, float]) -> None:
        self._probabilities = {class_id: float(probabilities.get(class_id, 0.0)) for class_id in CLASS_IDS}
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        plot = self.rect().adjusted(47, 16, -15, -38)
        painter.setPen(QPen(QColor("#D9D9D9"), 1))
        for value in range(0, 101, 25):
            y = plot.bottom() - int(plot.height() * value / 100)
            painter.drawLine(plot.left(), y, plot.right(), y)
            painter.setPen(QColor(MUTED))
            painter.drawText(4, y + 4, f"{value}%")
            painter.setPen(QPen(QColor("#D9D9D9"), 1))
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.drawLine(plot.left(), plot.bottom(), plot.right(), plot.bottom())
        painter.drawLine(plot.left(), plot.top(), plot.left(), plot.bottom())
        slot = plot.width() / len(CLASS_IDS)
        width = max(20, int(slot * 0.48))
        for index, class_id in enumerate(CLASS_IDS):
            value = max(0.0, min(1.0, self._probabilities[class_id]))
            center = int(plot.left() + slot * (index + 0.5))
            height = int(plot.height() * value)
            bar_rect = (center - width // 2, plot.bottom() - height, width, height)
            painter.fillRect(*bar_rect, QColor(BLUE))
            painter.setPen(QPen(QColor(BLUE_DARK), 1))
            painter.drawRect(*bar_rect)
            painter.setPen(QColor(TEXT))
            painter.drawText(center - 25, plot.bottom() + 19, 50, 15, Qt.AlignCenter, self._labels[class_id])
            if value > 0:
                painter.drawText(center - 27, plot.bottom() - height - 19, 54, 15, Qt.AlignCenter, f"{value * 100:.1f}%")


class AudioWaveformWidget(QWidget):
    """A visual-only, continuously looping five-second oscilloscope view."""

    playback_window_seconds = 5.0
    playback_interval_ms = 33
    scope_background = "#10202D"
    scope_trace = "#00A7D8"
    scope_cursor = "#21D4FD"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("audio_waveform")
        self.setFixedHeight(160)
        self._normalized_samples = np.zeros(0, dtype=np.float32)
        self._sample_rate = 16_000
        self._duration_seconds = 0.0
        self._playback_seconds = 0.0
        self._last_tick: float | None = None
        self._playback_timer = QTimer(self)
        self._playback_timer.setInterval(self.playback_interval_ms)
        self._playback_timer.timeout.connect(self._on_playback_tick)

    @property
    def is_playing(self) -> bool:
        return self._playback_timer.isActive()

    @property
    def playback_seconds(self) -> float:
        return self._playback_seconds

    def set_audio(self, samples: np.ndarray, sample_rate: int) -> None:
        self._normalized_samples = normalize_playback_samples(samples, min_span=1e-5)
        self._sample_rate = max(1, int(sample_rate))
        self._duration_seconds = self._normalized_samples.size / float(self._sample_rate)
        self._playback_seconds = 0.0
        self._last_tick = monotonic()
        if self._duration_seconds > 0.0:
            self._playback_timer.start()
        else:
            self._playback_timer.stop()
        self.update()

    def stop_playback(self, *, release_samples: bool = False) -> None:
        self._playback_timer.stop()
        self._last_tick = None
        if release_samples:
            self._normalized_samples = np.zeros(0, dtype=np.float32)
            self._duration_seconds = 0.0
            self._playback_seconds = 0.0

    @Slot()
    def _on_playback_tick(self) -> None:
        if self._duration_seconds <= 0.0:
            self.stop_playback()
            return
        now = monotonic()
        previous_tick = self._last_tick if self._last_tick is not None else now
        self._playback_seconds = looped_playback_position(
            self._playback_seconds,
            now - previous_tick,
            self._duration_seconds,
        )
        self._last_tick = now
        self.update()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.stop_playback(release_samples=True)
        super().closeEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.scope_background))
        painter.setPen(QPen(QColor("#536779"), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        if self._normalized_samples.size == 0:
            painter.setPen(QColor("#AABACA"))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待读取音频波形")
            return

        plot = self.rect().adjusted(48, 28, -14, -36)
        painter.setPen(QPen(QColor("#263B4C"), 1))
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = int(plot.top() + plot.height() * fraction)
            x = int(plot.left() + plot.width() * fraction)
            painter.drawLine(plot.left(), y, plot.right(), y)
            painter.drawLine(x, plot.top(), x, plot.bottom())
        painter.setPen(QPen(QColor("#6F8798"), 1))
        painter.drawLine(plot.left(), plot.top(), plot.left(), plot.bottom())
        painter.drawLine(plot.left(), plot.bottom(), plot.right(), plot.bottom())
        for value in (1.0, 0.5, 0.0, -0.5, -1.0):
            y = int(plot.center().y() - value * plot.height() / 2)
            painter.setPen(QColor("#AABACA"))
            painter.drawText(4, y + 4, f"{value:.1f}")

        envelope = calculate_playback_envelope(
            self._normalized_samples,
            sample_rate=self._sample_rate,
            center_seconds=self._playback_seconds,
            window_seconds=self.playback_window_seconds,
            max_points=max(64, plot.width()),
        )
        painter.setPen(QPen(QColor(self.scope_trace), 1))
        count = len(envelope.y_min_values)
        for index, (minimum, maximum) in enumerate(zip(envelope.y_min_values, envelope.y_max_values, strict=True)):
            x = int(plot.left() + plot.width() * index / max(1, count - 1))
            y_min = int(plot.center().y() - float(minimum) * plot.height() / 2)
            y_max = int(plot.center().y() - float(maximum) * plot.height() / 2)
            painter.drawLine(x, y_min, x, y_max)

        cursor_x = plot.center().x()
        painter.setPen(QPen(QColor(self.scope_cursor), 1))
        painter.drawLine(cursor_x, plot.top(), cursor_x, plot.bottom())
        painter.setPen(QColor("#B9D7E5"))
        painter.drawText(plot.left(), 18, "连续播放  ·  局部窗口 5.0 秒")
        painter.drawText(
            plot.right() - 116,
            18,
            f"{envelope.center_seconds:.2f} / {envelope.source_duration_seconds:.2f} 秒",
        )
        for fraction, label in ((0.0, "-2.5"), (0.5, "0.0"), (1.0, "+2.5")):
            x = int(plot.left() + plot.width() * fraction)
            painter.drawText(x - 21, plot.bottom() + 20, 42, 14, Qt.AlignCenter, label)
        painter.drawText(plot.center().x() - 35, self.height() - 4, "相对时间（秒）")


class ImportWorker(QObject):
    stage_changed = Signal(str, int)
    preview_ready = Signal(object, object)
    completed = Signal(str, object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(
        self,
        config: BearingAppConfig,
        source_path: str | Path,
        engine: BearingDiagnosticEngine,
        store: LocalRecordStore,
    ) -> None:
        super().__init__()
        self.config = config
        self.source_path = Path(source_path).resolve()
        self.engine = engine
        self.store = store

    @Slot()
    def run(self) -> None:
        try:
            record_dir, prediction = run_bearing_diagnosis(
                self.config,
                self.source_path,
                engine=self.engine,
                store=self.store,
                on_stage=lambda message, value: self.stage_changed.emit(message, value),
                on_preview=lambda samples, info: self.preview_ready.emit(samples, info),
            )
            self.completed.emit(str(record_dir), prediction)
        except Exception as exc:
            self.failed.emit(_friendly_error(exc), traceback.format_exc())
        finally:
            self.done.emit()


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: BearingAppConfig,
        *,
        engine: BearingDiagnosticEngine | None = None,
        store: LocalRecordStore | None = None,
    ) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle("轴承状态识别与剩余寿命预测系统")
        self.resize(1080, 760)
        self.setMinimumSize(960, 680)
        self._import_thread: QThread | None = None
        self._import_worker: ImportWorker | None = None
        self._active_path: Path | None = None
        self._engine = engine or BearingDiagnosticEngine(config)
        self._store = store or LocalRecordStore()
        self._build_page()
        self._apply_style()

    @property
    def is_busy(self) -> bool:
        return self._import_thread is not None

    def _build_page(self) -> None:
        page = QWidget()
        page.setObjectName("page")
        self.setCentralWidget(page)
        outer = QVBoxLayout(page)
        outer.setContentsMargins(14, 12, 14, 14)
        outer.setSpacing(8)

        heading = QLabel("轴承状态识别与剩余寿命预测系统")
        heading.setObjectName("heading")
        outer.addWidget(heading)
        separator = QWidget()
        separator.setObjectName("heading_separator")
        separator.setFixedHeight(1)
        outer.addWidget(separator)

        content = QGridLayout()
        content.setHorizontalSpacing(10)
        content.setVerticalSpacing(8)
        self.audio_group = self._build_audio_group()
        self.chart_group = self._build_chart_group()
        self.waveform_group = self._build_waveform_group()
        self.feature_group = self._build_feature_group()
        self.health_group = self._build_health_group()
        content.addWidget(self.audio_group, 0, 0)
        content.addWidget(self.chart_group, 0, 1)
        content.addWidget(self.waveform_group, 1, 0)
        content.addWidget(self.feature_group, 2, 0)
        content.addWidget(self.health_group, 1, 1, 2, 1)
        content.setColumnStretch(0, 4)
        content.setColumnStretch(1, 6)
        content.setRowStretch(0, 3)
        content.setRowStretch(1, 0)
        content.setRowStretch(2, 2)
        outer.addLayout(content, 1)

    def _build_audio_group(self) -> QGroupBox:
        group = QGroupBox("音频读取")
        group.setObjectName("audio_group")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(13, 20, 13, 12)
        layout.setSpacing(9)
        self.read_button = QPushButton("读取音频")
        self.read_button.setObjectName("read_audio_button")
        self.read_button.setMinimumWidth(130)
        self.read_button.clicked.connect(self._choose_audio)
        layout.addWidget(self.read_button, 0, Qt.AlignLeft)
        layout.addWidget(_field_title("文件路径"))
        self.file_path_label = QLabel("未选择音频文件")
        self.file_path_label.setObjectName("file_path")
        self.file_path_label.setWordWrap(True)
        self.file_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.file_path_label)
        self.audio_metric_labels: dict[str, QLabel] = {}
        audio_metrics = QGridLayout()
        audio_metrics.setHorizontalSpacing(6)
        audio_metrics.setVerticalSpacing(5)
        for index, (key, title) in enumerate(
            (
                ("format", "原始格式"),
                ("duration", "总时长"),
                ("sample_rate", "原始采样率"),
                ("channels", "声道数"),
                ("model_input", "模型输入"),
                ("segment_duration", "分段时长"),
            )
        ):
            card, value = _metric_card(title, f"audio_{key}_value")
            self.audio_metric_labels[key] = value
            audio_metrics.addWidget(card, index // 3, index % 3)
        layout.addLayout(audio_metrics)
        layout.addWidget(_field_title("执行状态"))
        self.status_label = QLabel("就绪：请选择 M4A 或 WAV 音频。")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setObjectName("diagnosis_progress")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        layout.addWidget(self.progress)
        layout.addWidget(_field_title("处理流程"))
        self.processing_step_labels: list[QLabel] = []
        steps = QGridLayout()
        steps.setHorizontalSpacing(5)
        for index, title in enumerate(PROCESSING_STEPS):
            label = QLabel()
            label.setObjectName("processing_step")
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumHeight(35)
            self.processing_step_labels.append(label)
            steps.addWidget(label, 0, index)
        layout.addLayout(steps)
        self._update_processing_steps(0, active=False)
        return group

    def _build_chart_group(self) -> QGroupBox:
        group = QGroupBox("类别概率")
        group.setObjectName("chart_group")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(13, 20, 13, 12)
        self.probability_chart = ProbabilityChartWidget(self.config.model.labels)
        layout.addWidget(self.probability_chart, 1)
        self.classification_metric_labels: dict[str, QLabel] = {}
        metrics = QGridLayout()
        metrics.setHorizontalSpacing(6)
        for index, (key, title) in enumerate(
            (
                ("category", "识别类别"),
                ("confidence", "最高置信度"),
                ("margin", "第一/第二差"),
            )
        ):
            card, value = _metric_card(title, f"classification_{key}_value")
            self.classification_metric_labels[key] = value
            metrics.addWidget(card, 0, index)
        layout.addLayout(metrics)
        return group

    def _build_waveform_group(self) -> QGroupBox:
        group = QGroupBox("动态音频波形")
        group.setObjectName("waveform_group")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(13, 20, 13, 13)
        self.audio_waveform = AudioWaveformWidget()
        layout.addWidget(self.audio_waveform, 1)
        return group

    def _build_feature_group(self) -> QGroupBox:
        group = QGroupBox("声学特征摘要")
        group.setObjectName("feature_group")
        layout = QGridLayout(group)
        layout.setContentsMargins(13, 20, 13, 13)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(6)
        self.feature_metric_labels: dict[str, QLabel] = {}
        for index, (key, title) in enumerate(
            (
                ("segments", "分析片段数"),
                ("rms", "RMS 能量"),
                ("centroid", "频谱重心"),
                ("flatness", "频谱平坦度"),
                ("zcr", "过零率"),
                ("kurtosis", "幅度峭度"),
            )
        ):
            card, value = _metric_card(title, f"feature_{key}_value")
            self.feature_metric_labels[key] = value
            layout.addWidget(card, index // 3, index % 3)
        return group

    def _build_health_group(self) -> QGroupBox:
        group = QGroupBox("算法估计剩余寿命")
        group.setObjectName("health_group")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 13)
        layout.setSpacing(9)
        descriptor = QLabel("声学退化特征与分类概率综合估计")
        descriptor.setObjectName("remaining_life_descriptor")
        descriptor.setAlignment(Qt.AlignCenter)
        layout.addWidget(descriptor)
        self.remaining_life_label = QLabel("-- %")
        self.remaining_life_label.setObjectName("remaining_life")
        self.remaining_life_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.remaining_life_label)
        self.remaining_life_bar = QProgressBar()
        self.remaining_life_bar.setObjectName("remaining_life_bar")
        self.remaining_life_bar.setRange(0, 10_000)
        self.remaining_life_bar.setValue(0)
        self.remaining_life_bar.setFormat("0.00%")
        layout.addWidget(self.remaining_life_bar)
        self.remaining_life_level_label = QLabel("状态等级：--")
        self.remaining_life_level_label.setObjectName("remaining_life_level")
        self.remaining_life_level_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.remaining_life_level_label)
        layout.addWidget(_field_title("风险分解"))
        self.risk_metric_labels: dict[str, QLabel] = {}
        risk_metrics = QGridLayout()
        risk_metrics.setHorizontalSpacing(6)
        for index, (key, title) in enumerate(
            (
                ("classification", "分类风险"),
                ("anomaly", "声学异常度"),
                ("anomaly_risk", "异常风险"),
                ("degradation", "综合退化度"),
            )
        ):
            card, value = _metric_card(title, f"risk_{key}_value")
            self.risk_metric_labels[key] = value
            risk_metrics.addWidget(card, 0, index)
        layout.addLayout(risk_metrics)
        self.processing_summary_label = QLabel("模型版本：--  |  本次处理：--")
        self.processing_summary_label.setObjectName("processing_summary")
        self.processing_summary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.processing_summary_label)
        self.record_label = QLabel("记录目录：--")
        self.record_label.setObjectName("record_path")
        self.record_label.setWordWrap(True)
        self.record_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.record_label)
        layout.addStretch(1)
        return group

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget#page {{ background: {BACKGROUND}; color: {TEXT}; }}
            QLabel#heading {{ color: {TEXT}; font-size: 21px; font-weight: bold; padding: 1px 2px; }}
            QWidget#heading_separator {{ background: #A0A0A0; }}
            QGroupBox {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 0; margin-top: 10px; font-size: 14px; font-weight: bold; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 9px; padding: 0 4px; color: #303030; }}
            QPushButton {{ background: #FFFFFF; border: 1px solid #9B9B9B; border-radius: 0; min-height: 31px; padding: 0 16px; color: {TEXT}; }}
            QPushButton:hover {{ border-color: {BLUE}; }}
            QPushButton:pressed {{ background: #E5E5E5; }}
            QPushButton:disabled {{ background: #E0E0E0; color: #888888; border-color: #BEBEBE; }}
            QLabel#file_path {{ color: {MUTED}; background: #FFFFFF; border: 1px solid #CDCDCD; padding: 5px; min-height: 18px; }}
            QLabel#status {{ color: {BLUE_DARK}; font-weight: bold; min-height: 22px; }}
            QLabel[fieldTitle="true"] {{ color: #454545; font-size: 12px; font-weight: bold; }}
            QWidget#metric_card {{ background: #FFFFFF; border: 1px solid #CDCDCD; border-radius: 0; }}
            QLabel[metricTitle="true"] {{ color: #5A5A5A; font-size: 10px; padding: 2px 4px 0 4px; }}
            QLabel[metricValue="true"] {{ color: {BLUE_DARK}; font-size: 13px; font-weight: bold; padding: 0 4px 2px 4px; }}
            QLabel#processing_step {{ background: #FFFFFF; border: 1px solid #CDCDCD; border-radius: 0; color: #666666; font-size: 10px; padding: 1px; }}
            QProgressBar {{ min-height: 20px; border: 1px solid #A8A8A8; border-radius: 0; background: #FFFFFF; text-align: center; color: {TEXT}; }}
            QProgressBar::chunk {{ background: {BLUE}; }}
            QLabel#remaining_life_descriptor {{ color: #454545; font-size: 15px; font-weight: bold; }}
            QLabel#remaining_life {{ font-size: 44px; color: {BLUE_DARK}; font-weight: bold; min-height: 64px; }}
            QLabel#remaining_life_level {{ font-size: 17px; font-weight: bold; }}
            QLabel#processing_summary {{ color: {MUTED}; background: #FFFFFF; border: 1px solid #CDCDCD; padding: 4px; font-size: 11px; }}
            QLabel#record_path {{ color: {MUTED}; font-size: 12px; border-top: 1px solid #D0D0D0; padding-top: 6px; }}
            """
        )

    @Slot()
    def _choose_audio(self) -> None:
        if self.is_busy:
            return
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择轴承音频",
            str(_initial_audio_directory()),
            "音频文件 (*.m4a *.M4A *.wav *.WAV)",
        )
        if not filename:
            return
        self._start_import(filename)

    def _start_import(self, source_path: str | Path) -> None:
        if self.is_busy:
            return
        self._active_path = Path(source_path).resolve()
        self.read_button.setEnabled(False)
        self.file_path_label.setText(str(self._active_path))
        self.status_label.setStyleSheet(f"color: {BLUE_DARK};")
        self.status_label.setText("正在准备识别任务…")
        self.progress.setValue(0)
        self._update_processing_steps(0, active=True)

        self._import_thread = QThread(self)
        self._import_worker = ImportWorker(self.config, self._active_path, self._engine, self._store)
        self._import_worker.moveToThread(self._import_thread)
        self._import_thread.started.connect(self._import_worker.run)
        self._import_worker.stage_changed.connect(self._on_stage)
        self._import_worker.preview_ready.connect(self._on_preview)
        self._import_worker.completed.connect(self._on_completed)
        self._import_worker.failed.connect(self._on_failed)
        self._import_worker.done.connect(self._import_thread.quit)
        self._import_worker.done.connect(self._import_worker.deleteLater)
        self._import_thread.finished.connect(self._clear_import_worker)
        self._import_thread.finished.connect(self._import_thread.deleteLater)
        self._import_thread.start()

    @Slot(str, int)
    def _on_stage(self, message: str, progress: int) -> None:
        self.status_label.setText(message)
        self.progress.setValue(max(self.progress.value(), int(progress)))
        self._update_processing_steps(int(progress))

    @Slot(str, object)
    def _on_completed(self, record_dir: str, prediction) -> None:
        audio = dict(prediction.metadata.get("audio") or {})
        self._set_audio_metrics(audio)
        self.status_label.setStyleSheet(f"color: {BLUE_DARK};")
        self.status_label.setText("识别完成")
        self.progress.setValue(100)
        self._update_processing_steps(100)
        self.probability_chart.set_probabilities(prediction.probabilities)
        self._set_classification_metrics(prediction)
        self._set_feature_metrics(prediction)
        self._set_risk_metrics(prediction)
        self.remaining_life_label.setText(f"{prediction.remaining_life_percent:.2f} %")
        self.remaining_life_bar.setValue(int(round(prediction.remaining_life_percent * 100)))
        self.remaining_life_bar.setFormat(f"{prediction.remaining_life_percent:.2f}%")
        self.remaining_life_level_label.setText(f"状态等级：{prediction.remaining_life_level}")
        self.record_label.setText(f"记录目录：{record_dir}")

    @Slot(object, object)
    def _on_preview(self, samples: object, source_info: object) -> None:
        values = np.asarray(samples, dtype=np.float32)
        decoded_rate = int(getattr(source_info, "decoded_sample_rate", self.config.target_sample_rate))
        self.audio_waveform.set_audio(values, decoded_rate)
        self._set_audio_metrics(source_info)

    @Slot(str, str)
    def _on_failed(self, message: str, details: str) -> None:
        failed_progress = self.progress.value()
        self.status_label.setStyleSheet(f"color: {ERROR_RED};")
        self.status_label.setText("识别失败")
        self._update_processing_steps(failed_progress, failed=True)
        self.progress.setValue(0)
        self._show_error(message, details)
        self.read_button.setEnabled(True)

    @Slot()
    def _clear_import_worker(self) -> None:
        self._import_worker = None
        self._import_thread = None
        self.read_button.setEnabled(True)

    def _show_error(self, message: str, details: str) -> None:
        QMessageBox.critical(self, "音频识别失败", message)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.audio_waveform.stop_playback(release_samples=True)
        super().closeEvent(event)

    def _set_audio_metrics(self, source: object) -> None:
        def get_value(name: str, default: object = "--") -> object:
            return source.get(name, default) if isinstance(source, dict) else getattr(source, name, default)

        decoded_rate = int(get_value("decoded_sample_rate", self.config.target_sample_rate))
        self.audio_metric_labels["format"].setText(str(get_value("format")))
        self.audio_metric_labels["duration"].setText(f"{float(get_value('duration_seconds', 0.0)):.2f} 秒")
        self.audio_metric_labels["sample_rate"].setText(f"{int(get_value('sample_rate', 0))} Hz")
        self.audio_metric_labels["channels"].setText(f"{int(get_value('channels', 0))} 声道")
        self.audio_metric_labels["model_input"].setText(f"单声道 / {decoded_rate} Hz")
        self.audio_metric_labels["segment_duration"].setText(f"{self.config.segment_seconds:.1f} 秒")

    def _set_classification_metrics(self, prediction: object) -> None:
        probabilities = dict(getattr(prediction, "probabilities", {}) or {})
        ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        margin = float(ranked[0][1] - ranked[1][1]) if len(ranked) > 1 else 0.0
        self.classification_metric_labels["category"].setText(str(getattr(prediction, "category_name", "--")))
        self.classification_metric_labels["confidence"].setText(f"{float(getattr(prediction, 'confidence', 0.0)) * 100:.2f}%")
        self.classification_metric_labels["margin"].setText(f"{margin * 100:.2f}%")

    def _set_feature_metrics(self, prediction: object) -> None:
        metadata = dict(getattr(prediction, "metadata", {}) or {})
        summary = dict(metadata.get("feature_summary") or {})
        self.feature_metric_labels["segments"].setText(f"{int(getattr(prediction, 'segment_count', 0))} 段")
        self.feature_metric_labels["rms"].setText(f"{float(summary.get('rms_mean', 0.0)):.5f}")
        self.feature_metric_labels["centroid"].setText(f"{float(summary.get('spectral_centroid_mean', 0.0)):.1f} Hz")
        self.feature_metric_labels["flatness"].setText(f"{float(summary.get('spectral_flatness_mean', 0.0)):.5f}")
        self.feature_metric_labels["zcr"].setText(f"{float(summary.get('zero_crossing_rate_mean', 0.0)):.5f}")
        self.feature_metric_labels["kurtosis"].setText(f"{float(summary.get('amplitude_kurtosis', 0.0)):.3f}")

    def _set_risk_metrics(self, prediction: object) -> None:
        metadata = dict(getattr(prediction, "metadata", {}) or {})
        self.risk_metric_labels["classification"].setText(f"{float(metadata.get('classification_risk', 0.0)) * 100:.2f}%")
        self.risk_metric_labels["anomaly"].setText(f"{float(metadata.get('acoustic_anomaly', 0.0)):.3f}")
        self.risk_metric_labels["anomaly_risk"].setText(f"{float(metadata.get('acoustic_anomaly_risk', 0.0)) * 100:.2f}%")
        self.risk_metric_labels["degradation"].setText(f"{float(metadata.get('total_degradation', 0.0)) * 100:.2f}%")
        duration_ms = metadata.get("processing_duration_ms")
        duration_text = "--" if duration_ms is None else f"{float(duration_ms):.1f} ms"
        self.processing_summary_label.setText(
            f"模型版本：{metadata.get('model_version', self.config.model.model_version)}  |  本次处理：{duration_text}"
        )

    def _update_processing_steps(self, progress: int, *, failed: bool = False, active: bool = True) -> None:
        value = max(0, min(100, int(progress)))
        if value >= 100:
            active_index = len(PROCESSING_STEPS)
        elif value >= 88:
            active_index = 3
        elif value >= 62:
            active_index = 2
        elif value >= 25:
            active_index = 1
        else:
            active_index = 0
        for index, (title, label) in enumerate(zip(PROCESSING_STEPS, self.processing_step_labels, strict=True)):
            if not active:
                state, color, border = "待执行", "#666666", "#CDCDCD"
            elif failed and index == active_index:
                state, color, border = "失败", ERROR_RED, ERROR_RED
            elif index < active_index or value >= 100:
                state, color, border = "完成", BLUE_DARK, BLUE
            elif index == active_index:
                state, color, border = "进行中", BLUE_DARK, BLUE
            else:
                state, color, border = "待执行", "#666666", "#CDCDCD"
            label.setText(f"{index + 1}. {title}\n{state}")
            label.setStyleSheet(f"color: {color}; border: 1px solid {border};")


def _field_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("fieldTitle", True)
    return label


def _metric_card(title: str, value_object_name: str) -> tuple[QWidget, QLabel]:
    """Create one compact industrial-style data card used by the dashboard."""

    card = QWidget()
    card.setObjectName("metric_card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(3, 2, 3, 2)
    layout.setSpacing(0)
    title_label = QLabel(title)
    title_label.setProperty("metricTitle", True)
    value_label = QLabel("--")
    value_label.setObjectName(value_object_name)
    value_label.setProperty("metricValue", True)
    value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    return card, value_label


def _initial_audio_directory() -> Path:
    configured = os.environ.get("BEARING_DATA_ROOT", "").strip()
    if configured:
        root = Path(configured).expanduser()
        if root.is_dir():
            manifest = BEARING_MODEL_DIR / "test_manifest.csv"
            try:
                with manifest.open(encoding="utf-8", newline="") as handle:
                    first = next(csv.DictReader(handle), None)
                if first and first.get("relative_path"):
                    candidate = root / str(first["relative_path"])
                    if candidate.parent.is_dir():
                        return candidate.parent
            except (OSError, csv.Error):
                pass
            return root
    return Path.home()


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, (ValueError, FileNotFoundError, RuntimeError)):
        return str(exc)
    return f"{type(exc).__name__}: {exc}"


def main() -> int:
    app = QApplication.instance() or QApplication([])
    try:
        config = load_bearing_config()
    except BearingConfigError as exc:
        QMessageBox.critical(None, "配置错误", str(exc))
        return 2
    window = MainWindow(config)
    window.show()
    return app.exec()
