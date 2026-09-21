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
        self.setMinimumHeight(220)
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

        top = QHBoxLayout()
        top.setSpacing(10)
        self.audio_group = self._build_audio_group()
        self.chart_group = self._build_chart_group()
        top.addWidget(self.audio_group, 4)
        top.addWidget(self.chart_group, 6)
        outer.addLayout(top, 4)

        bottom = QHBoxLayout()
        bottom.setSpacing(10)
        self.waveform_group = self._build_waveform_group()
        self.health_group = self._build_health_group()
        bottom.addWidget(self.waveform_group, 4)
        bottom.addWidget(self.health_group, 6)
        outer.addLayout(bottom, 5)

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
        layout.addWidget(_field_title("格式 / 时长 / 采样率"))
        self.audio_info_label = QLabel("--")
        self.audio_info_label.setObjectName("audio_info")
        layout.addWidget(self.audio_info_label)
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
        layout.addStretch(1)
        return group

    def _build_chart_group(self) -> QGroupBox:
        group = QGroupBox("类别概率")
        group.setObjectName("chart_group")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(13, 20, 13, 12)
        self.probability_chart = ProbabilityChartWidget(self.config.model.labels)
        layout.addWidget(self.probability_chart, 1)
        return group

    def _build_waveform_group(self) -> QGroupBox:
        group = QGroupBox("动态音频波形")
        group.setObjectName("waveform_group")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(13, 20, 13, 13)
        self.audio_waveform = AudioWaveformWidget()
        layout.addWidget(self.audio_waveform, 1)
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
            QLabel#file_path, QLabel#audio_info {{ color: {MUTED}; background: #FFFFFF; border: 1px solid #CDCDCD; padding: 5px; min-height: 18px; }}
            QLabel#status {{ color: {BLUE_DARK}; font-weight: bold; min-height: 22px; }}
            QLabel[fieldTitle="true"] {{ color: #454545; font-size: 12px; font-weight: bold; }}
            QProgressBar {{ min-height: 20px; border: 1px solid #A8A8A8; border-radius: 0; background: #FFFFFF; text-align: center; color: {TEXT}; }}
            QProgressBar::chunk {{ background: {BLUE}; }}
            QLabel#remaining_life_descriptor {{ color: #454545; font-size: 15px; font-weight: bold; }}
            QLabel#remaining_life {{ font-size: 44px; color: {BLUE_DARK}; font-weight: bold; min-height: 64px; }}
            QLabel#remaining_life_level {{ font-size: 17px; font-weight: bold; }}
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
        self.audio_info_label.setText("正在读取音频参数…")
        self.status_label.setStyleSheet(f"color: {BLUE_DARK};")
        self.status_label.setText("正在准备识别任务…")
        self.progress.setValue(0)
        self.record_label.setText("记录目录：任务完成后生成")

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

    @Slot(str, object)
    def _on_completed(self, record_dir: str, prediction) -> None:
        audio = dict(prediction.metadata.get("audio") or {})
        self.audio_info_label.setText(
            f"{audio.get('format', '--')}  |  {audio.get('duration_seconds', 0):.2f} 秒  |  "
            f"{audio.get('sample_rate', '--')} Hz  |  {audio.get('channels', '--')} 声道\n"
            f"模型输入：单声道 / {audio.get('decoded_sample_rate', self.config.target_sample_rate)} Hz"
        )
        self.status_label.setStyleSheet(f"color: {BLUE_DARK};")
        self.status_label.setText("识别完成")
        self.progress.setValue(100)
        self.probability_chart.set_probabilities(prediction.probabilities)
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
        duration = float(getattr(source_info, "duration_seconds", 0.0))
        self.audio_info_label.setText(
            f"{getattr(source_info, 'format', '--')}  |  {duration:.2f} 秒  |  "
            f"{getattr(source_info, 'sample_rate', '--')} Hz  |  {getattr(source_info, 'channels', '--')} 声道\n"
            f"模型输入：单声道 / {decoded_rate} Hz"
        )

    @Slot(str, str)
    def _on_failed(self, message: str, details: str) -> None:
        self.status_label.setStyleSheet(f"color: {ERROR_RED};")
        self.status_label.setText("识别失败")
        self.audio_info_label.setText(message)
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


def _field_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("fieldTitle", True)
    return label


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
