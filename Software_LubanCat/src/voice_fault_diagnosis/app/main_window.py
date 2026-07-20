from __future__ import annotations

from pathlib import Path
import threading
import traceback

import numpy as np

try:
    from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
    from PySide6.QtGui import QColor, QFont, QPainter, QPen
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QSlider,
        QSpinBox,
        QStyle,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PySide6 is required to run the desktop app") from exc

from voice_fault_diagnosis.app.denoise_comparison import ComparisonWaveformWidget
from voice_fault_diagnosis.app.waveform_display import WaveformDisplay, calculate_waveform_display
from voice_fault_diagnosis.audio_io import voltage_to_audio
from voice_fault_diagnosis.capture.vk701n import (
    SUPPORTED_INPUT_RANGES,
    Vk701nCaptureSession,
    resolve_sdk_library,
)
from voice_fault_diagnosis.config import load_json, save_json
from voice_fault_diagnosis.diagnostics.sound_capture import (
    CaptureCheckReport,
    CaptureCheckResult,
    save_capture_check,
)
from voice_fault_diagnosis.inference.legacy_cnn import LegacyCnnEngine
from voice_fault_diagnosis.models import (
    AnalysisSource,
    CaptureResult,
    DenoiseConfig,
    DenoiseResult,
    DiagnosisProgress,
    HardwareConfig,
    MultiChannelCaptureResult,
    StoredCapture,
    WorkflowState,
)
from voice_fault_diagnosis.paths import CAPTURE_CHECKS_DIR, CONFIG_DIR, LEGACY_MODEL_DIR
from voice_fault_diagnosis.pipeline import run_analysis, run_denoise
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


PREVIEW_WINDOW_SECONDS = 0.2
PLAYBACK_INTERVAL_MS = 50
TAB_HARDWARE = 0
TAB_CAPTURE = 1
TAB_DENOISE = 2
TAB_RESULT = 3
TAB_HISTORY = 4
TAB_MODEL = 5


class WaveformWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(240)
        self._audio = np.zeros(0, dtype=np.float32)
        self._adaptive = True
        self._full_scale_volts = 5.0
        self._display = calculate_waveform_display(self._audio)

    @property
    def display_scale(self) -> float:
        return self._display.display_scale

    @property
    def display_stats(self) -> WaveformDisplay:
        return self._display

    def set_display_mode(self, adaptive: bool, full_scale_volts: float) -> None:
        self._adaptive = bool(adaptive)
        self._full_scale_volts = max(float(full_scale_volts), 1e-6)
        self._recalculate_display()

    def set_audio(self, audio: np.ndarray) -> None:
        self._audio = np.asarray(audio, dtype=np.float32)
        self._recalculate_display()

    def _recalculate_display(self) -> None:
        self._display = calculate_waveform_display(
            self._audio,
            adaptive=self._adaptive,
            full_scale_volts=self._full_scale_volts,
        )
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        rect = self.rect().adjusted(1, 1, -1, -1)
        plot_rect = rect.adjusted(82, 12, -12, -28)
        painter.fillRect(rect, QColor("#101820"))
        painter.setPen(QPen(QColor("#243443"), 1))
        for index in range(1, 5):
            y = plot_rect.top() + index * plot_rect.height() / 5
            painter.drawLine(plot_rect.left(), int(y), plot_rect.right(), int(y))
        for index in range(1, 7):
            x = plot_rect.left() + index * plot_rect.width() / 7
            painter.drawLine(int(x), plot_rect.top(), int(x), plot_rect.bottom())

        display = self._display
        painter.setPen(QColor("#b7c6d8"))
        painter.drawText(rect.left() + 8, plot_rect.top() + 10, _format_volts(display.upper_volts))
        painter.drawText(rect.left() + 8, plot_rect.center().y() + 4, _format_volts(display.center_volts))
        painter.drawText(rect.left() + 8, plot_rect.bottom(), _format_volts(display.lower_volts))
        painter.setPen(QPen(QColor("#49687f"), 1.2))
        painter.drawLine(plot_rect.left(), plot_rect.center().y(), plot_rect.right(), plot_rect.center().y())

        if display.samples.size < 2:
            painter.setPen(QColor("#b7c6d8"))
            painter.drawText(plot_rect, Qt.AlignCenter, "暂无声纹电压数据")
            return

        painter.setRenderHint(QPainter.Antialiasing)
        center_y = plot_rect.center().y()
        y_scale = plot_rect.height() * 0.5
        width = max(1, plot_rect.width() - 8)
        if display.is_envelope and display.y_min_values.size:
            count = display.y_min_values.size
            painter.setPen(QPen(QColor("#2ed3a6"), 1.0))
            for index, (y_min, y_max) in enumerate(zip(display.y_min_values, display.y_max_values)):
                x = plot_rect.left() + 4 + index * width / max(1, count - 1)
                y_top = center_y - float(y_max) * y_scale
                y_bottom = center_y - float(y_min) * y_scale
                painter.drawLine(int(x), int(y_top), int(x), int(y_bottom))
            return

        points: list[tuple[int, int]] = []
        for index, display_value in enumerate(display.y_values):
            x = plot_rect.left() + 4 + index * width / max(1, display.y_values.size - 1)
            y = center_y - float(display_value) * y_scale
            points.append((int(x), int(y)))
        painter.setPen(QPen(QColor("#2ed3a6"), 1.6))
        for left, right in zip(points, points[1:]):
            painter.drawLine(left[0], left[1], right[0], right[1])


class ModelWarmupWorker(QObject):
    status_changed = Signal(str)
    failed = Signal(str, str)
    done = Signal()

    def __init__(self, engine: LegacyCnnEngine) -> None:
        super().__init__()
        self.engine = engine

    @Slot()
    def run(self) -> None:
        try:
            self.status_changed.emit("正在预热模型，首次诊断会更快...")
            self.engine.prepare()
            self.status_changed.emit("模型已预热，可以开始采集")
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}", traceback.format_exc())
        finally:
            self.done.emit()


class CaptureWorker(QObject):
    chunk_ready = Signal(object, object)
    status_changed = Signal(str)
    completed = Signal(object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(self, hardware: HardwareConfig) -> None:
        super().__init__()
        self.hardware = hardware
        self.stop_event = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            self.status_changed.emit("正在连接采集卡...")
            session = Vk701nCaptureSession(self.hardware)

            def on_chunk(voltage: np.ndarray, info: dict[str, object]) -> None:
                self.chunk_ready.emit(voltage.copy(), dict(info))

            self.status_changed.emit("正在采集声纹电压...")
            capture = session.capture(on_chunk=on_chunk, stop_event=self.stop_event)
            if capture.raw_voltage.size == 0:
                raise RuntimeError("未采集到有效声纹电压数据")
            self.status_changed.emit("采集结束，请选择后续操作")
            self.completed.emit(capture)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}", traceback.format_exc())
        finally:
            self.done.emit()

    def stop(self) -> None:
        self.stop_event.set()


class SoundCheckCaptureWorker(QObject):
    progress_changed = Signal(int, str)
    completed = Signal(object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(self, hardware: HardwareConfig, duration_seconds: float, stage_label: str) -> None:
        super().__init__()
        self.hardware = hardware
        self.duration_seconds = float(duration_seconds)
        self.stage_label = stage_label

    @Slot()
    def run(self) -> None:
        try:
            session = Vk701nCaptureSession(self.hardware)

            def on_chunk(_voltage: np.ndarray, info: dict[str, object]) -> None:
                received = int(info.get("received_samples") or 0)
                target = max(1, int(info.get("target_samples") or 1))
                percent = min(100, int(round(received / target * 100)))
                self.progress_changed.emit(percent, f"{self.stage_label}：已采集 {received}/{target} 点")

            result = session.capture_all_channels(self.duration_seconds, on_chunk=on_chunk)
            if result.raw_voltage.shape[0] == 0:
                raise RuntimeError("未采集到四通道电压数据")
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}", traceback.format_exc())
        finally:
            self.done.emit()


class SoundCheckAnalysisWorker(QObject):
    progress_changed = Signal(int, str)
    completed = Signal(object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(
        self,
        quiet: MultiChannelCaptureResult,
        noise: MultiChannelCaptureResult,
        hardware: HardwareConfig,
    ) -> None:
        super().__init__()
        self.quiet = quiet
        self.noise = noise
        self.hardware = hardware

    @Slot()
    def run(self) -> None:
        try:
            result = save_capture_check(
                self.quiet.raw_voltage,
                self.noise.raw_voltage,
                self.hardware,
                quiet_metadata=self.quiet.metadata,
                noise_metadata=self.noise.metadata,
                output_root=CAPTURE_CHECKS_DIR,
                progress_callback=self.progress_changed.emit,
            )
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}", traceback.format_exc())
        finally:
            self.done.emit()


class DenoiseWorker(QObject):
    progress_changed = Signal(object)
    completed = Signal(object, object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(
        self,
        capture: CaptureResult,
        hardware: HardwareConfig,
        config: DenoiseConfig,
    ) -> None:
        super().__init__()
        self.capture = capture
        self.hardware = hardware
        self.config = config

    @Slot()
    def run(self) -> None:
        try:
            raw_audio, result = run_denoise(
                capture=self.capture,
                hardware_config=self.hardware,
                denoise_config=self.config,
                progress_callback=self.progress_changed.emit,
            )
            self.completed.emit(raw_audio, result)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}", traceback.format_exc())
        finally:
            self.done.emit()


class AnalysisWorker(QObject):
    progress_changed = Signal(object)
    completed = Signal(str, object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(
        self,
        capture: CaptureResult,
        hardware: HardwareConfig,
        engine: LegacyCnnEngine,
        store: LocalRecordStore,
        analysis_source: AnalysisSource,
        denoise_result: DenoiseResult | None,
        record_dir: Path | None,
        source_record_id: str | None,
    ) -> None:
        super().__init__()
        self.capture = capture
        self.hardware = hardware
        self.engine = engine
        self.store = store
        self.analysis_source = analysis_source
        self.denoise_result = denoise_result
        self.record_dir = record_dir
        self.source_record_id = source_record_id

    @Slot()
    def run(self) -> None:
        try:
            record_dir, prediction = run_analysis(
                capture=self.capture,
                hardware_config=self.hardware,
                engine=self.engine,
                store=self.store,
                analysis_source=self.analysis_source,
                denoise_result=self.denoise_result,
                record_dir=self.record_dir,
                source_record_id=self.source_record_id,
                progress_callback=self.progress_changed.emit,
            )
            self.completed.emit(str(record_dir), prediction)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}", traceback.format_exc())
        finally:
            self.done.emit()


class SoundCaptureCheckDialog(QDialog):
    recommendation_applied = Signal(int, float)

    def __init__(self, hardware: HardwareConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hardware = hardware
        self.quiet_result: MultiChannelCaptureResult | None = None
        self.noise_result: MultiChannelCaptureResult | None = None
        self.check_result: CaptureCheckResult | None = None
        self._thread: QThread | None = None
        self._worker: QObject | None = None
        self._analyze_when_idle = False

        self.setWindowTitle("声音采集链路自检")
        self.resize(980, 680)
        layout = QVBoxLayout(self)
        title = QLabel("先证明采到了声音，再进入模型流程")
        title.setObjectName("DialogTitle")
        instructions = QLabel(
            "自检会分别采集 5 秒安静基线和 5 秒机械噪声，并同时比较 CH1 至 CH4。"
            "请在第二阶段持续制造可重复的机械声。"
        )
        instructions.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(instructions)

        self.status_label = QLabel("第 1 步：保持现场安静，点击“采集安静基线”。")
        self.status_label.setObjectName("StatusLabel")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFormat("自检进度 %p%")
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["通道", "结论", "安静 AC RMS", "噪声 AC RMS", "AC 增量", "频带增量", "噪声峰值", "削波"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.table)

        self.summary = QPlainTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setMinimumHeight(145)
        self.summary.setPlainText(
            "自检完成后会显示通道和量程建议。monitor.wav 只用于电脑试听，不会进入模型。"
        )
        layout.addWidget(self.summary)

        self.output_label = QLabel("报告目录：尚未生成")
        self.output_label.setObjectName("MutedLabel")
        self.output_label.setWordWrap(True)
        layout.addWidget(self.output_label)

        actions = QHBoxLayout()
        self.quiet_button = QPushButton("1. 采集安静基线")
        self.quiet_button.setProperty("role", "secondary")
        self.noise_button = QPushButton("2. 采集机械噪声")
        self.noise_button.setProperty("role", "secondary")
        self.apply_button = QPushButton("应用推荐通道和量程")
        self.close_button = QPushButton("关闭")
        self.close_button.setProperty("role", "secondary")
        self.quiet_button.clicked.connect(lambda: self._start_capture_stage("quiet"))
        self.noise_button.clicked.connect(lambda: self._start_capture_stage("noise"))
        self.apply_button.clicked.connect(self._apply_recommendation)
        self.close_button.clicked.connect(self.accept)
        actions.addWidget(self.quiet_button)
        actions.addWidget(self.noise_button)
        actions.addStretch(1)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.close_button)
        layout.addLayout(actions)
        self._update_controls()

    def reject(self) -> None:
        if self._thread is not None:
            QMessageBox.warning(self, "自检正在运行", "请等待当前采集或报告生成完成。")
            return
        super().reject()

    def _start_capture_stage(self, stage: str) -> None:
        if self._thread is not None:
            return
        if stage == "noise" and self.quiet_result is None:
            return
        if stage == "quiet":
            self.quiet_result = None
            self.noise_result = None
            self.check_result = None
            self.table.setRowCount(0)
            self.output_label.setText("报告目录：尚未生成")
            self.summary.setPlainText("正在采集安静基线，请保持现场安静。")
            label = "安静基线"
        else:
            self.noise_result = None
            self.check_result = None
            self.summary.setPlainText("正在采集机械噪声，请在整个阶段持续制造可重复的机械声。")
            label = "机械噪声"
        self.progress_bar.setValue(0)
        self.status_label.setText(f"正在连接采集卡并采集{label}...")
        worker = SoundCheckCaptureWorker(self.hardware, 5.0, label)
        worker.progress_changed.connect(self._on_progress)
        worker.completed.connect(lambda result, current_stage=stage: self._on_stage_completed(current_stage, result))
        worker.failed.connect(self._on_failed)
        self._launch_worker(worker)

    def _on_stage_completed(self, stage: str, result_obj: object) -> None:
        if not isinstance(result_obj, MultiChannelCaptureResult):
            self._on_failed("采集结果格式无效", "Expected MultiChannelCaptureResult")
            return
        self.progress_bar.setValue(100)
        if stage == "quiet":
            self.quiet_result = result_obj
            self.status_label.setText("安静基线已完成。第 2 步：准备持续制造机械噪声。")
        else:
            self.noise_result = result_obj
            self.status_label.setText("两阶段采集已完成，正在分析四通道并生成试听文件...")
            self._analyze_when_idle = True

    def _start_analysis(self) -> None:
        if self.quiet_result is None or self.noise_result is None or self._thread is not None:
            return
        self.progress_bar.setValue(0)
        worker = SoundCheckAnalysisWorker(self.quiet_result, self.noise_result, self.hardware)
        worker.progress_changed.connect(self._on_progress)
        worker.completed.connect(self._on_analysis_completed)
        worker.failed.connect(self._on_failed)
        self._launch_worker(worker)

    def _on_analysis_completed(self, result_obj: object) -> None:
        if not isinstance(result_obj, CaptureCheckResult):
            self._on_failed("分析结果格式无效", "Expected CaptureCheckResult")
            return
        self.check_result = result_obj
        self.progress_bar.setValue(100)
        self.status_label.setText(result_obj.report.overall_message)
        self.output_label.setText(f"报告目录：{result_obj.output_dir}")
        self.summary.setPlainText(
            (result_obj.output_dir / "summary.txt").read_text(encoding="utf-8")
        )
        self._populate_table(result_obj.report)

    def _populate_table(self, report: CaptureCheckReport) -> None:
        self.table.setRowCount(len(report.channels))
        for row, comparison in enumerate(report.channels):
            values = [
                f"CH{comparison.channel}",
                _capture_check_status_text(comparison.status),
                _format_volts(comparison.quiet.ac_rms_volts),
                _format_volts(comparison.noise.ac_rms_volts),
                f"{comparison.ac_rms_increase_db:.2f} dB",
                f"{comparison.band_power_increase_db:.2f} dB",
                _format_volts(comparison.noise.peak_abs_volts),
                f"{comparison.noise.clipping_ratio * 100.0:.4f}%",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if comparison.channel == report.recommended_channel:
                    item.setBackground(QColor("#dff5ef"))
                self.table.setItem(row, column, item)

    def _apply_recommendation(self) -> None:
        if self.check_result is None:
            return
        report = self.check_result.report
        self.hardware.adc_channel = int(report.recommended_channel)
        self.hardware.input_range_volts = float(report.recommended_input_range_volts)
        self.recommendation_applied.emit(
            self.hardware.adc_channel,
            self.hardware.input_range_volts,
        )
        self.quiet_result = None
        self.noise_result = None
        self.check_result = None
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.status_label.setText("推荐参数已应用。请从安静基线开始重新自检，确认新量程不削波。")
        self.summary.setPlainText(
            f"已应用 CH{self.hardware.adc_channel}、{self.hardware.input_range_volts:g} V。"
            "参数尚未自动保存，重新自检通过后再关闭窗口并保存硬件设置。"
        )
        self._update_controls()

    def _on_progress(self, percent: int, message: str) -> None:
        self.progress_bar.setValue(max(0, min(100, int(percent))))
        self.status_label.setText(message)

    def _on_failed(self, message: str, details: str) -> None:
        self._analyze_when_idle = False
        self.status_label.setText(f"自检失败：{message}")
        self.summary.setPlainText(details)
        QMessageBox.critical(self, "声音采集自检失败", message)

    def _launch_worker(self, worker: QObject) -> None:
        thread = QThread(self)
        self._thread = thread
        self._worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.done.connect(thread.quit)
        worker.done.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_worker)
        thread.start()
        self._update_controls()

    def _clear_worker(self) -> None:
        self._thread = None
        self._worker = None
        should_analyze = self._analyze_when_idle
        self._analyze_when_idle = False
        self._update_controls()
        if should_analyze:
            QTimer.singleShot(0, self._start_analysis)

    def _update_controls(self) -> None:
        busy = self._thread is not None
        self.quiet_button.setEnabled(not busy)
        self.noise_button.setEnabled(not busy and self.quiet_result is not None)
        self.apply_button.setEnabled(not busy and self.check_result is not None)
        self.close_button.setEnabled(not busy)


class PostCaptureDialog(QDialog):
    resample_requested = Signal()
    denoise_requested = Signal()
    save_requested = Signal()

    def __init__(self, already_saved: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("采集完成")
        self.setModal(True)
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        title = QLabel("采样数据已准备好，请选择下一步")
        title.setObjectName("DialogTitle")
        self.message_label = QLabel("可以重新采样、进入降噪对比，或先保存当前采样。")
        self.message_label.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(self.message_label)

        buttons = QHBoxLayout()
        self.resample_button = QPushButton("重新采样")
        self.resample_button.setProperty("role", "secondary")
        self.save_button = QPushButton("保存采样")
        self.save_button.setProperty("role", "secondary")
        self.denoise_button = QPushButton("进入降噪对比")
        buttons.addWidget(self.resample_button)
        buttons.addStretch(1)
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.denoise_button)
        layout.addLayout(buttons)

        self.resample_button.clicked.connect(self._resample)
        self.denoise_button.clicked.connect(self._denoise)
        self.save_button.clicked.connect(self.save_requested.emit)
        if already_saved:
            self.mark_saved("")

    def mark_saved(self, record_dir: str) -> None:
        self.save_button.setEnabled(False)
        self.save_button.setText("采样已保存")
        message = "采样已保存，仍可继续进入降噪对比或重新采样。"
        if record_dir:
            message += f"\n记录目录：{record_dir}"
        self.message_label.setText(message)

    def _resample(self) -> None:
        self.accept()
        self.resample_requested.emit()

    def _denoise(self) -> None:
        self.accept()
        self.denoise_requested.emit()


class RecordPickerDialog(QDialog):
    def __init__(self, records: list[dict[str, object]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("读取已保存采样")
        self.resize(820, 420)
        self.selected_record_dir: str | None = None
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["时间", "状态", "记录 ID", "输入来源", "诊断标签"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                record.get("created_at", ""),
                _status_text(str(record.get("status", ""))),
                record.get("record_id", ""),
                _analysis_source_text(str(record.get("analysis_source", ""))),
                record.get("label", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.UserRole, str(record.get("record_dir", "")))
                self.table.setItem(row, column, item)
        if records:
            self.table.selectRow(0)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("取消")
        cancel.setProperty("role", "secondary")
        load = QPushButton("载入到降噪对比")
        load.setEnabled(bool(records))
        cancel.clicked.connect(self.reject)
        load.clicked.connect(self._accept_selected)
        self.table.doubleClicked.connect(self._accept_selected)
        actions.addWidget(cancel)
        actions.addWidget(load)
        layout.addLayout(actions)

    def _accept_selected(self, *_args) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item is None:
            return
        self.selected_record_dir = str(item.data(Qt.UserRole) or "")
        if self.selected_record_dir:
            self.accept()


class MainWindow(QMainWindow):
    def __init__(self, *, start_model_warmup: bool = True) -> None:
        super().__init__()
        self.setWindowTitle("声纹故障诊断系统 - 鲁班猫")
        self.resize(1280, 860)
        self.state = WorkflowState.IDLE
        self._job_thread: QThread | None = None
        self._job_worker: QObject | None = None
        self._warmup_thread: QThread | None = None
        self._warmup_worker: ModelWarmupWorker | None = None
        self._show_post_capture_when_idle = False
        self._post_capture_dialog: PostCaptureDialog | None = None
        self._denoise_dirty = True
        self._active_analysis_source: AnalysisSource = "raw"

        self.preview_voltage = np.zeros(0, dtype=np.float32)
        self.active_sample_rate = 50000
        self.active_input_range_volts = 5.0
        self.current_capture: CaptureResult | None = None
        self.current_hardware: HardwareConfig | None = None
        self.current_raw_audio: np.ndarray | None = None
        self.current_denoise_result: DenoiseResult | None = None
        self.current_record_dir: Path | None = None
        self.current_source_record_id: str | None = None

        self.store = LocalRecordStore()
        self.engine = LegacyCnnEngine()
        self._hardware_config_path = CONFIG_DIR / "hardware_vk701n.json"

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_hardware_tab()
        self._build_capture_tab()
        self._build_denoise_tab()
        self._build_result_tab()
        self._build_history_tab()
        self._build_model_tab()

        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(PLAYBACK_INTERVAL_MS)
        self.playback_timer.timeout.connect(self._advance_comparison)
        self._refresh_history()
        self._update_actions()
        if start_model_warmup:
            self._start_model_warmup()

    def _build_hardware_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        self.hardware_group = QGroupBox("VK701N-SD 硬件设置")
        form = QFormLayout(self.hardware_group)
        form.setLabelAlignment(Qt.AlignRight)

        cfg = HardwareConfig.from_dict(load_json(self._hardware_config_path, {}))
        sdk_default = cfg.sdk_library_path or str(resolve_sdk_library(""))
        self.sdk_path = QLineEdit(sdk_default)
        browse = QPushButton("选择 SDK")
        browse.setProperty("role", "secondary")
        browse.clicked.connect(self._browse_sdk)
        sdk_row = QHBoxLayout()
        sdk_row.addWidget(self.sdk_path, 1)
        sdk_row.addWidget(browse)
        form.addRow("SDK 路径", sdk_row)

        self.port_spin = _spin(cfg.server_port, 1, 65535)
        self.device_spin = _spin(cfg.device_no, 0, 16)
        self.sample_rate_spin = _spin(cfg.sample_rate, 1, 100000)
        self.bit_mode_spin = _spin(cfg.bit_mode, 8, 32)
        self.channel_spin = _spin(cfg.adc_channel, 1, 4)
        self.input_range_combo = QComboBox()
        for range_volts in SUPPORTED_INPUT_RANGES:
            self.input_range_combo.addItem(f"{range_volts:g} V", float(range_volts))
        range_index = self.input_range_combo.findData(float(cfg.input_range_volts))
        self.input_range_combo.setCurrentIndex(max(0, range_index))
        self.frame_spin = _spin(cfg.read_frame_count, 1, 200000)
        self.gain_spin = _double_spin(cfg.gain, 0.001, 100.0, 3)
        self.blocking_spin = _spin(cfg.blocking_timeout_ms, 1, 10000)
        self.capture_seconds_spin = _double_spin(cfg.capture_seconds, 0.1, 3600.0, 1)
        self.initialize_profile_combo = QComboBox()
        self.initialize_profile_combo.addItems(["code_source", "fixed", "windows_c_example"])
        initialize_profile = str(cfg.initialize_all_profile or "code_source")
        if initialize_profile not in {"windows_c_example", "code_source", "fixed"}:
            initialize_profile = "code_source"
        self.initialize_profile_combo.setCurrentText(initialize_profile)
        form.addRow("端口", self.port_spin)
        form.addRow("设备号", self.device_spin)
        form.addRow("采样率 Hz", self.sample_rate_spin)
        form.addRow("位深", self.bit_mode_spin)
        form.addRow("ADC 通道", self.channel_spin)
        form.addRow("输入量程", self.input_range_combo)
        form.addRow("每次读取点数", self.frame_spin)
        form.addRow("legacy 增益", self.gain_spin)
        form.addRow("阻塞超时 ms", self.blocking_spin)
        form.addRow("采集时长 s", self.capture_seconds_spin)
        form.addRow("初始化 profile", self.initialize_profile_combo)
        layout.addWidget(self.hardware_group)
        layout.addStretch(1)

        actions = QHBoxLayout()
        self.sound_check_button = QPushButton("采集链路自检")
        self.sound_check_button.setProperty("role", "secondary")
        self.sound_check_button.clicked.connect(self._open_sound_check)
        save_button = QPushButton("保存设置")
        save_button.setProperty("role", "secondary")
        save_button.clicked.connect(lambda: self._save_hardware_config(show_message=True))
        next_button = QPushButton("保存并进入采集")
        next_button.clicked.connect(self._save_hardware_and_next)
        actions.addWidget(self.sound_check_button)
        actions.addWidget(save_button)
        actions.addStretch(1)
        actions.addWidget(next_button)
        layout.addLayout(actions)
        self.tabs.addTab(page, "硬件设置")

    def _build_capture_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        controls = QHBoxLayout()
        self.start_button = QPushButton("开始采集")
        self.stop_button = QPushButton("停止采集")
        self.stop_button.setProperty("role", "danger")
        self.start_button.clicked.connect(self._start_capture)
        self.stop_button.clicked.connect(self._stop_capture)
        self.auto_scale_checkbox = QCheckBox("自适应交流显示")
        self.auto_scale_checkbox.setChecked(True)
        self.auto_scale_checkbox.toggled.connect(self._on_display_mode_changed)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.auto_scale_checkbox)
        controls.addStretch(1)

        self.capture_status = QLabel("等待采集")
        self.capture_status.setObjectName("StatusLabel")
        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setFormat("输入电平 %p%")
        self.capture_progress_bar = QProgressBar()
        self.capture_progress_bar.setRange(0, 100)
        self.capture_progress_bar.setFormat("采集进度 %p%")
        self.waveform = WaveformWidget()
        self.capture_summary = QPlainTextEdit()
        self.capture_summary.setReadOnly(True)
        self.capture_summary.setMinimumHeight(125)

        self.post_capture_group = QGroupBox("采后操作")
        post_actions = QHBoxLayout(self.post_capture_group)
        self.resample_button = QPushButton("重新采样")
        self.resample_button.setProperty("role", "secondary")
        self.save_capture_button = QPushButton("保存采样")
        self.save_capture_button.setProperty("role", "secondary")
        self.enter_denoise_button = QPushButton("进入降噪对比")
        self.resample_button.clicked.connect(self._restart_capture)
        self.save_capture_button.clicked.connect(self._save_current_capture)
        self.enter_denoise_button.clicked.connect(self._enter_denoise)
        post_actions.addWidget(self.resample_button)
        post_actions.addStretch(1)
        post_actions.addWidget(self.save_capture_button)
        post_actions.addWidget(self.enter_denoise_button)

        layout.addLayout(controls)
        layout.addWidget(self.capture_status)
        layout.addWidget(self.level_bar)
        layout.addWidget(self.capture_progress_bar)
        layout.addWidget(QLabel("实时声纹电压"))
        layout.addWidget(self.waveform, 1)
        layout.addWidget(QLabel("采集摘要"))
        layout.addWidget(self.capture_summary)
        layout.addWidget(self.post_capture_group)
        self.tabs.addTab(page, "数据采集")

    def _build_denoise_tab(self) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 18, 18, 18)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        source_row = QHBoxLayout()
        self.denoise_source_label = QLabel("当前采样：尚未载入")
        self.denoise_source_label.setObjectName("StatusLabel")
        self.denoise_source_label.setWordWrap(True)
        self.load_record_button = QPushButton("读取已保存采样")
        self.load_record_button.setProperty("role", "secondary")
        self.load_record_button.clicked.connect(self._open_record_picker)
        source_row.addWidget(self.denoise_source_label, 1)
        source_row.addWidget(self.load_record_button)
        layout.addLayout(source_row)

        self.denoise_settings_group = QGroupBox("降噪参数")
        form = QFormLayout(self.denoise_settings_group)
        form.setLabelAlignment(Qt.AlignRight)
        cfg = DenoiseConfig.from_dict(load_json(CONFIG_DIR / "denoise.json", {}))
        self.denoise_enabled = QCheckBox("启用降噪")
        self.denoise_enabled.setChecked(cfg.enabled)
        self.bandpass_enabled = QCheckBox("启用带通滤波")
        self.bandpass_enabled.setChecked(cfg.bandpass_enabled)
        self.low_spin = _double_spin(cfg.bandpass_low_hz, 0.1, 100000.0, 1)
        self.high_spin = _double_spin(cfg.bandpass_high_hz, 0.1, 100000.0, 1)
        self.order_spin = _spin(cfg.bandpass_order, 1, 12)
        self.wavelet_enabled = QCheckBox("启用小波降噪")
        self.wavelet_enabled.setChecked(cfg.wavelet_enabled)
        self.wavelet_name = QComboBox()
        self.wavelet_name.setEditable(True)
        self.wavelet_name.addItems(["db4", "db6", "sym4", "sym6", "coif1", "coif3"])
        self.wavelet_name.setCurrentText(cfg.wavelet)
        self.wavelet_level = _spin(cfg.wavelet_level, 1, 8)
        self.wavelet_threshold = QComboBox()
        self.wavelet_threshold.addItems(["soft", "hard"])
        self.wavelet_threshold.setCurrentText(cfg.wavelet_threshold)
        form.addRow(self.denoise_enabled)
        form.addRow(self.bandpass_enabled)
        form.addRow("低截止 Hz", self.low_spin)
        form.addRow("高截止 Hz", self.high_spin)
        form.addRow("滤波阶数", self.order_spin)
        form.addRow(self.wavelet_enabled)
        form.addRow("小波基", self.wavelet_name)
        form.addRow("小波层数", self.wavelet_level)
        form.addRow("阈值模式", self.wavelet_threshold)
        layout.addWidget(self.denoise_settings_group)

        parameter_actions = QHBoxLayout()
        self.save_denoise_button = QPushButton("保存为默认参数")
        self.save_denoise_button.setProperty("role", "secondary")
        self.apply_denoise_button = QPushButton("应用并对比")
        self.save_denoise_button.clicked.connect(self._save_denoise_config)
        self.apply_denoise_button.clicked.connect(self._start_denoise)
        parameter_actions.addWidget(self.save_denoise_button)
        parameter_actions.addStretch(1)
        parameter_actions.addWidget(self.apply_denoise_button)
        layout.addLayout(parameter_actions)

        self.denoise_step_label = QLabel("降噪进度：等待采样")
        self.denoise_step_label.setObjectName("MutedLabel")
        self.denoise_progress_bar = QProgressBar()
        self.denoise_progress_bar.setRange(0, 100)
        self.denoise_progress_bar.setFormat("%p%")
        layout.addWidget(self.denoise_step_label)
        layout.addWidget(self.denoise_progress_bar)

        self.comparison_waveform = ComparisonWaveformWidget()
        layout.addWidget(self.comparison_waveform)
        playback = QHBoxLayout()
        self.play_pause_button = QPushButton()
        self.play_pause_button.setProperty("role", "icon")
        self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_pause_button.setToolTip("播放波形滚动")
        self.play_pause_button.clicked.connect(self._toggle_comparison_playback)
        self.comparison_time_label = QLabel("0.000 s / 0.000 s")
        self.comparison_slider = QSlider(Qt.Horizontal)
        self.comparison_slider.setRange(0, 0)
        self.comparison_slider.valueChanged.connect(self._on_comparison_position_changed)
        self.window_combo = QComboBox()
        for label, seconds in [("0.2 秒窗口", 0.2), ("1 秒窗口", 1.0), ("5 秒窗口", 5.0)]:
            self.window_combo.addItem(label, seconds)
        self.window_combo.setCurrentIndex(1)
        self.window_combo.currentIndexChanged.connect(self._reset_comparison_window)
        playback.addWidget(self.play_pause_button)
        playback.addWidget(self.comparison_time_label)
        playback.addWidget(self.comparison_slider, 1)
        playback.addWidget(self.window_combo)
        layout.addLayout(playback)

        self.denoise_metrics_label = QLabel("对比指标：尚未执行降噪")
        self.denoise_metrics_label.setObjectName("MetricsLabel")
        self.denoise_metrics_label.setWordWrap(True)
        layout.addWidget(self.denoise_metrics_label)

        analyze_actions = QHBoxLayout()
        self.analyze_raw_button = QPushButton("不降噪，直接分析")
        self.analyze_raw_button.setProperty("role", "secondary")
        self.analyze_denoised_button = QPushButton("使用当前降噪结果分析")
        self.analyze_raw_button.clicked.connect(lambda: self._start_analysis("raw"))
        self.analyze_denoised_button.clicked.connect(lambda: self._start_analysis("denoised"))
        analyze_actions.addStretch(1)
        analyze_actions.addWidget(self.analyze_raw_button)
        analyze_actions.addWidget(self.analyze_denoised_button)
        layout.addLayout(analyze_actions)
        self.tabs.addTab(page, "降噪对比")

        controls = [
            self.denoise_enabled,
            self.bandpass_enabled,
            self.low_spin,
            self.high_spin,
            self.order_spin,
            self.wavelet_enabled,
            self.wavelet_name,
            self.wavelet_level,
            self.wavelet_threshold,
        ]
        for control in controls:
            if isinstance(control, QCheckBox):
                control.toggled.connect(self._on_denoise_parameters_changed)
            elif isinstance(control, (QSpinBox, QDoubleSpinBox)):
                control.valueChanged.connect(self._on_denoise_parameters_changed)
            elif isinstance(control, QComboBox):
                control.currentTextChanged.connect(self._on_denoise_parameters_changed)
        self._update_denoise_control_state()

    def _build_result_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        self.analysis_step_label = QLabel("诊断进度：等待分析")
        self.analysis_step_label.setObjectName("StatusLabel")
        self.analysis_progress_bar = QProgressBar()
        self.analysis_progress_bar.setRange(0, 100)
        self.analysis_progress_bar.setFormat("%p%")
        self.result_text = QPlainTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlainText("完成采集并选择分析方式后显示结果。")
        actions = QHBoxLayout()
        self.result_resample_button = QPushButton("重新采样")
        self.result_resample_button.setProperty("role", "secondary")
        self.result_history_button = QPushButton("查看历史记录")
        self.result_resample_button.clicked.connect(self._restart_capture)
        self.result_history_button.clicked.connect(lambda: self.tabs.setCurrentIndex(TAB_HISTORY))
        actions.addStretch(1)
        actions.addWidget(self.result_resample_button)
        actions.addWidget(self.result_history_button)
        layout.addWidget(self.analysis_step_label)
        layout.addWidget(self.analysis_progress_bar)
        layout.addWidget(self.result_text, 1)
        layout.addLayout(actions)
        self.tabs.addTab(page, "诊断结果")

    def _build_history_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        actions = QHBoxLayout()
        refresh = QPushButton("刷新历史记录")
        refresh.setProperty("role", "secondary")
        self.history_load_button = QPushButton("载入到降噪对比")
        refresh.clicked.connect(self._refresh_history)
        self.history_load_button.clicked.connect(self._load_selected_history)
        actions.addWidget(refresh)
        actions.addStretch(1)
        actions.addWidget(self.history_load_button)
        self.history_table = QTableWidget(0, 7)
        self.history_table.setHorizontalHeaderLabels(
            ["时间", "状态", "记录 ID", "模型输入", "类别", "置信度", "目录"]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.doubleClicked.connect(self._load_selected_history)
        layout.addLayout(actions)
        layout.addWidget(self.history_table)
        self.tabs.addTab(page, "历史记录")

    def _build_model_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        self.model_status_label = QLabel("模型状态：等待预热")
        self.model_status_label.setObjectName("StatusLabel")
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(
            "\n".join(
                [
                    "当前模型: Legacy CNN",
                    f"模型目录: {LEGACY_MODEL_DIR}",
                    "后端: PyTorch",
                    "输入特征: 1 x 36 x 5，来自 MFCC / Mel / Chroma 统计特征",
                    "输出类别数: 10",
                    "标签配置: configs/labels.json",
                    "原始分析使用采集时的 legacy_input。",
                    "降噪分析会把处理后波形还原为电压，再按相同 gain 生成 legacy 输入。",
                ]
            )
        )
        layout.addWidget(self.model_status_label)
        layout.addWidget(text)
        self.tabs.addTab(page, "模型信息")

    def _hardware_config(self) -> HardwareConfig:
        data = load_json(self._hardware_config_path, {})
        data.update(
            {
                "sdk_library_path": self.sdk_path.text().strip(),
                "server_port": int(self.port_spin.value()),
                "device_no": int(self.device_spin.value()),
                "adc_channel": int(self.channel_spin.value()),
                "input_range_volts": float(self.input_range_combo.currentData()),
                "sample_rate": int(self.sample_rate_spin.value()),
                "bit_mode": int(self.bit_mode_spin.value()),
                "read_frame_count": int(self.frame_spin.value()),
                "gain": float(self.gain_spin.value()),
                "blocking_timeout_ms": int(self.blocking_spin.value()),
                "capture_seconds": float(self.capture_seconds_spin.value()),
                "initialize_all_profile": self.initialize_profile_combo.currentText(),
            }
        )
        return HardwareConfig.from_dict(data)

    def _denoise_config(self) -> DenoiseConfig:
        return DenoiseConfig(
            enabled=self.denoise_enabled.isChecked(),
            bandpass_enabled=self.bandpass_enabled.isChecked(),
            bandpass_low_hz=float(self.low_spin.value()),
            bandpass_high_hz=float(self.high_spin.value()),
            bandpass_order=int(self.order_spin.value()),
            wavelet_enabled=self.wavelet_enabled.isChecked(),
            wavelet=self.wavelet_name.currentText().strip() or "db4",
            wavelet_level=int(self.wavelet_level.value()),
            wavelet_threshold=self.wavelet_threshold.currentText(),
        )

    def _start_model_warmup(self) -> None:
        if self._warmup_thread is not None:
            return
        self._warmup_thread = QThread(self)
        self._warmup_worker = ModelWarmupWorker(self.engine)
        self._warmup_worker.moveToThread(self._warmup_thread)
        self._warmup_thread.started.connect(self._warmup_worker.run)
        self._warmup_worker.status_changed.connect(self._on_model_status)
        self._warmup_worker.failed.connect(self._on_model_warmup_failed)
        self._warmup_worker.done.connect(self._warmup_thread.quit)
        self._warmup_worker.done.connect(self._warmup_worker.deleteLater)
        self._warmup_thread.finished.connect(self._warmup_thread.deleteLater)
        self._warmup_thread.finished.connect(self._clear_warmup_worker)
        self._warmup_thread.start()

    def _start_capture(self) -> None:
        if self._job_thread is not None:
            return
        hardware = self._hardware_config()
        self._reset_current_session(set_idle=False)
        self.current_hardware = hardware
        self.active_sample_rate = int(hardware.sample_rate)
        self.active_input_range_volts = float(hardware.input_range_volts)
        self.waveform.set_display_mode(self.auto_scale_checkbox.isChecked(), self.active_input_range_volts)
        self.capture_status.setText("正在准备采集...")
        self.result_text.setPlainText("正在采集；停止后将由你选择保存、降噪或重新采样。")
        self._set_state(WorkflowState.CAPTURING)

        worker = CaptureWorker(hardware)
        worker.status_changed.connect(self.capture_status.setText)
        worker.chunk_ready.connect(self._on_chunk)
        worker.completed.connect(self._on_capture_completed)
        worker.failed.connect(self._on_capture_failed)
        self._launch_worker(worker)

    def _stop_capture(self) -> None:
        if isinstance(self._job_worker, CaptureWorker):
            self._job_worker.stop()
            self.capture_status.setText("正在停止采集并整理样本...")
            self.stop_button.setEnabled(False)

    def _on_capture_completed(self, capture_obj: object) -> None:
        if not isinstance(capture_obj, CaptureResult) or self.current_hardware is None:
            self._on_capture_failed("采集结果格式无效", "CaptureWorker did not return CaptureResult")
            return
        self._set_current_capture(capture_obj, self.current_hardware)
        self.capture_progress_bar.setValue(100)
        self.capture_status.setText("采集结束，请选择后续操作")
        self._show_post_capture_when_idle = True

    def _on_capture_failed(self, message: str, details: str) -> None:
        self.capture_status.setText("采集失败")
        self.result_text.setPlainText(details)
        self._set_state(WorkflowState.FAILED)
        QMessageBox.critical(self, "采集失败", message)

    def _start_denoise(self) -> None:
        if self._job_thread is not None or self.current_capture is None or self.current_hardware is None:
            return
        config = self._denoise_config()
        if not config.enabled or not (config.bandpass_enabled or config.wavelet_enabled):
            self.denoise_step_label.setText("降噪进度：尚未启用任何降噪方法")
            return
        self.denoise_progress_bar.setValue(0)
        self.denoise_step_label.setText("降噪进度：正在启动后台处理")
        self._set_state(WorkflowState.DENOISING)
        worker = DenoiseWorker(self.current_capture, self.current_hardware, config)
        worker.progress_changed.connect(self._on_denoise_progress)
        worker.completed.connect(self._on_denoise_completed)
        worker.failed.connect(self._on_denoise_failed)
        self._launch_worker(worker)

    def _on_denoise_progress(self, progress_obj: object) -> None:
        progress = _coerce_progress(progress_obj)
        if progress is None:
            return
        self.denoise_progress_bar.setValue(max(0, min(100, int(progress.percent))))
        self.denoise_step_label.setText(f"降噪进度：{progress.message}")

    def _on_denoise_completed(self, raw_audio_obj: object, result_obj: object) -> None:
        if not isinstance(result_obj, DenoiseResult) or self.current_capture is None or self.current_hardware is None:
            self._on_denoise_failed("降噪结果格式无效", "DenoiseWorker did not return DenoiseResult")
            return
        self.current_raw_audio = np.asarray(raw_audio_obj, dtype=np.float32)
        self.current_denoise_result = result_obj
        self._denoise_dirty = False
        processed_voltage = np.asarray(result_obj.processed_audio, dtype=np.float32) * float(
            self.current_hardware.input_range_volts
        )
        self.comparison_waveform.set_signals(
            np.asarray(self.current_capture.raw_voltage, dtype=np.float32),
            processed_voltage,
            self.current_capture.sample_rate,
        )
        self._reset_comparison_window()
        self._show_denoise_metrics(result_obj.metrics)
        methods = "+".join(result_obj.metadata.get("methods") or []) or "未执行"
        self.denoise_step_label.setText(f"降噪进度：完成（{methods}）")
        self.denoise_progress_bar.setValue(100)
        self._set_state(WorkflowState.READY_TO_ANALYZE)

    def _on_denoise_failed(self, message: str, details: str) -> None:
        self.denoise_step_label.setText(f"降噪进度：失败 - {message}")
        self.result_text.setPlainText(details)
        target = WorkflowState.READY_TO_ANALYZE if self._has_valid_denoise_result() else WorkflowState.CAPTURED
        self._set_state(target)
        QMessageBox.critical(self, "降噪失败", message)

    def _start_analysis(self, source: AnalysisSource) -> None:
        if self._job_thread is not None or self.current_capture is None or self.current_hardware is None:
            return
        denoise_result = self.current_denoise_result if source == "denoised" else None
        if source == "denoised" and not self._has_valid_denoise_result():
            QMessageBox.warning(self, "降噪结果不可用", "请先使用当前参数完成一次降噪处理。")
            return
        self._active_analysis_source = source
        self.analysis_progress_bar.setValue(0)
        self.analysis_step_label.setText("诊断进度：正在启动后台分析")
        self.result_text.setPlainText(
            f"正在使用{_analysis_source_text(source)}进行诊断，请等待阶段进度完成。"
        )
        self.tabs.setCurrentIndex(TAB_RESULT)
        self._set_state(WorkflowState.ANALYZING)
        worker = AnalysisWorker(
            capture=self.current_capture,
            hardware=self.current_hardware,
            engine=self.engine,
            store=self.store,
            analysis_source=source,
            denoise_result=denoise_result,
            record_dir=self.current_record_dir,
            source_record_id=self.current_source_record_id,
        )
        worker.progress_changed.connect(self._on_analysis_progress)
        worker.completed.connect(self._on_analysis_completed)
        worker.failed.connect(self._on_analysis_failed)
        self._launch_worker(worker)

    def _on_analysis_progress(self, progress_obj: object) -> None:
        progress = _coerce_progress(progress_obj)
        if progress is None:
            return
        self.analysis_progress_bar.setValue(max(0, min(100, int(progress.percent))))
        self.analysis_step_label.setText(f"诊断进度：{progress.message}")

    def _on_analysis_completed(self, record_dir: str, prediction) -> None:
        self.current_record_dir = Path(record_dir)
        self.current_source_record_id = None
        self.analysis_progress_bar.setValue(100)
        self.analysis_step_label.setText("诊断进度：完成")
        timings = prediction.metadata.get("timings", {}) if isinstance(prediction.metadata, dict) else {}
        timing_lines = [
            f"  {key}: {float(value):.3f} s"
            for key, value in timings.items()
            if isinstance(value, (int, float))
        ]
        denoise_lines = ["  未使用降噪结果"]
        if self._active_analysis_source == "denoised" and self.current_denoise_result is not None:
            config = self.current_denoise_result.config
            denoise_lines = [
                f"  带通滤波: {'启用' if config.bandpass_enabled else '关闭'}",
                f"  小波降噪: {'启用' if config.wavelet_enabled else '关闭'}",
                f"  方法: {', '.join(self.current_denoise_result.metadata.get('methods') or [])}",
            ]
        self.result_text.setPlainText(
            "\n".join(
                [
                    f"记录目录: {record_dir}",
                    f"模型输入来源: {_analysis_source_text(self._active_analysis_source)}",
                    f"模型: {prediction.model_name}",
                    f"分类索引: {prediction.class_index}",
                    f"故障标签: {prediction.label}",
                    f"置信度: {prediction.confidence:.6f}",
                    "",
                    "降噪:",
                    *denoise_lines,
                    "",
                    "Top-K:",
                    *[
                        f"  {item['class_index']} / {item['label']}: {item['confidence']:.6f}"
                        for item in prediction.top_k
                    ],
                    "",
                    "耗时:",
                    *(timing_lines or ["  暂无耗时数据"]),
                ]
            )
        )
        self._set_state(WorkflowState.COMPLETED)
        self._refresh_history()

    def _on_analysis_failed(self, message: str, details: str) -> None:
        self.analysis_step_label.setText(f"诊断进度：失败 - {message}")
        self.result_text.setPlainText(details)
        target = WorkflowState.READY_TO_ANALYZE if self._has_valid_denoise_result() else WorkflowState.CAPTURED
        self._set_state(target)
        QMessageBox.critical(self, "诊断失败", message)

    def _launch_worker(self, worker: QObject) -> None:
        if self._job_thread is not None:
            raise RuntimeError("another background job is already running")
        thread = QThread(self)
        self._job_thread = thread
        self._job_worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.done.connect(thread.quit)
        worker.done.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_job_worker)
        thread.start()
        self._update_actions()

    def _clear_job_worker(self) -> None:
        self._job_thread = None
        self._job_worker = None
        self._update_actions()
        if self._show_post_capture_when_idle:
            self._show_post_capture_when_idle = False
            QTimer.singleShot(0, self._show_post_capture_dialog)

    def _show_post_capture_dialog(self) -> None:
        if self.current_capture is None or self.state != WorkflowState.CAPTURED:
            return
        dialog = PostCaptureDialog(already_saved=self.current_record_dir is not None, parent=self)
        self._post_capture_dialog = dialog
        dialog.resample_requested.connect(self._restart_capture)
        dialog.denoise_requested.connect(self._enter_denoise)
        dialog.save_requested.connect(self._save_current_capture)
        dialog.exec()
        self._post_capture_dialog = None

    def _save_current_capture(self) -> None:
        if self.current_capture is None or self.current_hardware is None or self.current_raw_audio is None:
            return
        try:
            self.current_record_dir = self.store.save_capture(
                capture=self.current_capture,
                raw_audio=self.current_raw_audio,
                hardware_config=self.current_hardware,
                existing_record_dir=self.current_record_dir,
                source_record_id=self.current_source_record_id,
            )
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"{type(exc).__name__}: {exc}")
            return
        self.capture_status.setText(f"采样已保存：{self.current_record_dir.name}")
        if self._post_capture_dialog is not None:
            self._post_capture_dialog.mark_saved(str(self.current_record_dir))
        self._refresh_history()
        self._update_actions()

    def _enter_denoise(self) -> None:
        if self.current_capture is None:
            return
        self.tabs.setCurrentIndex(TAB_DENOISE)
        if self.current_denoise_result is None:
            has_method = self.denoise_enabled.isChecked() and (
                self.bandpass_enabled.isChecked() or self.wavelet_enabled.isChecked()
            )
            message = (
                "请设置参数后点击“应用并对比”"
                if has_method
                else "尚未启用任何降噪方法，可直接分析原始信号"
            )
            self.denoise_step_label.setText(f"降噪进度：{message}")

    def _restart_capture(self) -> None:
        if self._job_thread is not None:
            return
        self._reset_current_session(set_idle=True)
        self.tabs.setCurrentIndex(TAB_CAPTURE)
        self._start_capture()

    def _set_current_capture(
        self,
        capture: CaptureResult,
        hardware: HardwareConfig,
        record_dir: Path | None = None,
        source_record_id: str | None = None,
    ) -> None:
        self.current_capture = capture
        self.current_hardware = hardware
        self.current_raw_audio = voltage_to_audio(capture.raw_voltage, hardware.input_range_volts)
        self.current_denoise_result = None
        self.current_record_dir = record_dir
        self.current_source_record_id = source_record_id
        self._denoise_dirty = True
        self.active_sample_rate = int(capture.sample_rate)
        self.active_input_range_volts = float(hardware.input_range_volts)
        self.comparison_waveform.set_signals(
            np.asarray(capture.raw_voltage, dtype=np.float32),
            None,
            capture.sample_rate,
        )
        self._reset_comparison_window()
        duration = np.asarray(capture.raw_voltage).size / float(max(1, capture.sample_rate))
        source_text = f"记录 {record_dir.name}" if record_dir is not None else "本轮硬件采集"
        self.denoise_source_label.setText(
            f"当前采样：{source_text} · {duration:.3f} 秒 · {capture.sample_rate} Hz · {np.asarray(capture.raw_voltage).size} 点"
        )
        self.denoise_metrics_label.setText("对比指标：尚未执行降噪")
        self.denoise_progress_bar.setValue(0)
        self._set_state(WorkflowState.CAPTURED)

    def _reset_current_session(self, *, set_idle: bool) -> None:
        self._stop_comparison_playback()
        self.preview_voltage = np.zeros(0, dtype=np.float32)
        self.current_capture = None
        self.current_hardware = None
        self.current_raw_audio = None
        self.current_denoise_result = None
        self.current_record_dir = None
        self.current_source_record_id = None
        self._denoise_dirty = True
        if hasattr(self, "waveform"):
            self.waveform.set_audio(self.preview_voltage)
            self.capture_progress_bar.setValue(0)
            self.level_bar.setValue(0)
            self.capture_summary.clear()
            self.post_capture_group.setVisible(False)
        if hasattr(self, "comparison_waveform"):
            self.comparison_waveform.set_signals(np.zeros(0, dtype=np.float32), None, self.active_sample_rate)
            self.comparison_slider.setRange(0, 0)
            self.comparison_time_label.setText("0.000 s / 0.000 s")
            self.denoise_source_label.setText("当前采样：尚未载入")
            self.denoise_metrics_label.setText("对比指标：尚未执行降噪")
            self.denoise_progress_bar.setValue(0)
        if set_idle:
            self.capture_status.setText("等待采集")
            self._set_state(WorkflowState.IDLE)

    def _set_state(self, state: WorkflowState) -> None:
        self.state = state
        self._update_actions()

    def _update_actions(self) -> None:
        if not hasattr(self, "start_button"):
            return
        has_capture = self.current_capture is not None
        busy = self.state in {WorkflowState.CAPTURING, WorkflowState.DENOISING, WorkflowState.ANALYZING}
        worker_busy = self._job_thread is not None
        self.start_button.setEnabled(not worker_busy and self.state in {WorkflowState.IDLE, WorkflowState.FAILED})
        self.stop_button.setEnabled(self.state == WorkflowState.CAPTURING and isinstance(self._job_worker, CaptureWorker))
        self.hardware_group.setEnabled(not busy)
        self.sound_check_button.setEnabled(not busy and not worker_busy)
        show_post_actions = has_capture and self.state not in {WorkflowState.CAPTURING, WorkflowState.ANALYZING}
        self.post_capture_group.setVisible(show_post_actions)
        self.resample_button.setEnabled(show_post_actions and not worker_busy)
        self.enter_denoise_button.setEnabled(show_post_actions and not worker_busy)
        self.save_capture_button.setEnabled(show_post_actions and self.current_record_dir is None and not worker_busy)
        self.save_capture_button.setText("采样已保存" if self.current_record_dir else "保存采样")

        has_method = self.denoise_enabled.isChecked() and (
            self.bandpass_enabled.isChecked() or self.wavelet_enabled.isChecked()
        )
        self.apply_denoise_button.setEnabled(has_capture and has_method and not worker_busy)
        if not has_capture:
            self.apply_denoise_button.setToolTip("请先完成采集或读取历史采样")
        elif not has_method:
            self.apply_denoise_button.setToolTip("请至少启用带通滤波或小波降噪")
        else:
            self.apply_denoise_button.setToolTip("使用当前参数对完整采样进行后台处理")
        self.analyze_raw_button.setEnabled(has_capture and not worker_busy)
        self.analyze_denoised_button.setEnabled(has_capture and self._has_valid_denoise_result() and not worker_busy)
        self.analyze_denoised_button.setToolTip(
            "使用当前有效降噪结果生成模型输入"
            if self._has_valid_denoise_result()
            else "参数应用完成且未再次修改后才可使用"
        )
        self.load_record_button.setEnabled(not worker_busy)
        self.save_denoise_button.setEnabled(not worker_busy)
        self.denoise_settings_group.setEnabled(not worker_busy)
        self.play_pause_button.setEnabled(has_capture)
        self.comparison_slider.setEnabled(has_capture)
        self.window_combo.setEnabled(has_capture)
        self.result_resample_button.setEnabled(has_capture and not worker_busy)
        self.result_history_button.setEnabled(not worker_busy)
        self.history_load_button.setEnabled(self.history_table.currentRow() >= 0 and not worker_busy)
        self._update_denoise_control_state()

    def _update_denoise_control_state(self) -> None:
        enabled = self.denoise_enabled.isChecked()
        bandpass = enabled and self.bandpass_enabled.isChecked()
        wavelet = enabled and self.wavelet_enabled.isChecked()
        self.bandpass_enabled.setEnabled(enabled)
        self.low_spin.setEnabled(bandpass)
        self.high_spin.setEnabled(bandpass)
        self.order_spin.setEnabled(bandpass)
        self.wavelet_enabled.setEnabled(enabled)
        self.wavelet_name.setEnabled(wavelet)
        self.wavelet_level.setEnabled(wavelet)
        self.wavelet_threshold.setEnabled(wavelet)

    def _on_denoise_parameters_changed(self, *_args) -> None:
        if self.current_denoise_result is not None:
            self._denoise_dirty = True
            self.denoise_step_label.setText("降噪进度：参数已更改，请重新应用后再使用降噪结果分析")
        elif not self.denoise_enabled.isChecked() or not (
            self.bandpass_enabled.isChecked() or self.wavelet_enabled.isChecked()
        ):
            self.denoise_step_label.setText("降噪进度：尚未启用任何降噪方法，可直接分析原始信号")
        self._update_actions()

    def _has_valid_denoise_result(self) -> bool:
        return bool(
            self.current_denoise_result is not None
            and not self._denoise_dirty
            and self.current_denoise_result.metadata.get("applied")
        )

    def _show_denoise_metrics(self, metrics: dict[str, float]) -> None:
        scale = float(self.current_hardware.input_range_volts) if self.current_hardware else 1.0
        raw_rms = float(metrics.get("raw_ac_rms", 0.0)) * scale
        processed_rms = float(metrics.get("processed_ac_rms", 0.0)) * scale
        raw_p2p = float(metrics.get("raw_peak_to_peak", 0.0)) * scale
        processed_p2p = float(metrics.get("processed_peak_to_peak", 0.0)) * scale
        difference_rms = float(metrics.get("difference_rms", 0.0)) * scale
        self.denoise_metrics_label.setText(
            "对比指标（共用电压尺度）："
            f"原始 AC RMS {_format_volts(raw_rms)} · 降噪后 AC RMS {_format_volts(processed_rms)} · "
            f"原始峰峰值 {_format_volts(raw_p2p)} · 降噪后峰峰值 {_format_volts(processed_p2p)} · "
            f"差分 RMS {_format_volts(difference_rms)}"
        )

    def _on_chunk(self, voltage_obj: object, info_obj: object) -> None:
        voltage = np.asarray(voltage_obj, dtype=np.float32)
        info = dict(info_obj) if isinstance(info_obj, dict) else {}
        if voltage.size:
            self.preview_voltage = (
                voltage.copy()
                if self.preview_voltage.size == 0
                else np.concatenate([self.preview_voltage, voltage]).astype(np.float32, copy=False)
            )
            max_preview = max(1, int(self.active_sample_rate * PREVIEW_WINDOW_SECONDS))
            if self.preview_voltage.size > max_preview:
                self.preview_voltage = self.preview_voltage[-max_preview:]
            self.waveform.set_audio(self.preview_voltage)
            peak = float(np.max(np.abs(voltage)))
            full_scale = max(float(self.active_input_range_volts), 1e-6)
            self.level_bar.setValue(min(100, max(1, int(round(peak / full_scale * 100)))))
        received = int(info.get("received_samples") or 0)
        target = int(info.get("target_samples") or 0)
        if target:
            self.capture_progress_bar.setValue(min(100, int(round(received / target * 100))))
        stats = self.waveform.display_stats
        display_mode = "自适应交流显示" if self.auto_scale_checkbox.isChecked() else "满量程电压显示"
        self.capture_summary.setPlainText(
            "\n".join(
                [
                    f"DAQ IP: {info.get('daq_ip', '')}",
                    f"样本进度: {received} / {target}",
                    f"读取次数: {info.get('read_calls', 0)}",
                    f"连续 0 读取: {info.get('zero_read_count', 0)}",
                    f"显示模式: {display_mode}",
                    f"交流 RMS: {stats.ac_rms_volts:.9f} V",
                    f"峰峰值: {stats.peak_to_peak_volts:.9f} V",
                    f"显示缩放: {self.waveform.display_scale:.1f}x",
                ]
            )
        )

    def _on_display_mode_changed(self, *_args) -> None:
        self.waveform.set_display_mode(self.auto_scale_checkbox.isChecked(), self.active_input_range_volts)
        self.waveform.set_audio(self.preview_voltage)

    def _toggle_comparison_playback(self) -> None:
        if self.playback_timer.isActive():
            self._stop_comparison_playback()
            return
        if self.comparison_slider.maximum() <= 0:
            return
        if self.comparison_slider.value() >= self.comparison_slider.maximum():
            self.comparison_slider.setValue(0)
        self.playback_timer.start()
        self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.play_pause_button.setToolTip("暂停波形滚动")

    def _stop_comparison_playback(self) -> None:
        if hasattr(self, "playback_timer"):
            self.playback_timer.stop()
        if hasattr(self, "play_pause_button"):
            self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.play_pause_button.setToolTip("播放波形滚动")

    def _advance_comparison(self) -> None:
        step = max(1, int(round(self.active_sample_rate * PLAYBACK_INTERVAL_MS / 1000.0)))
        next_value = min(self.comparison_slider.maximum(), self.comparison_slider.value() + step)
        self.comparison_slider.setValue(next_value)
        if next_value >= self.comparison_slider.maximum():
            self._stop_comparison_playback()

    def _reset_comparison_window(self, *_args) -> None:
        if not hasattr(self, "comparison_waveform"):
            return
        window_seconds = float(self.window_combo.currentData() or 1.0)
        self.comparison_waveform.set_window(self.comparison_slider.value(), window_seconds)
        self.comparison_slider.setRange(0, self.comparison_waveform.max_start_sample)
        self.comparison_slider.setValue(min(self.comparison_slider.value(), self.comparison_slider.maximum()))
        self._on_comparison_position_changed(self.comparison_slider.value())

    def _on_comparison_position_changed(self, start_sample: int) -> None:
        window_seconds = float(self.window_combo.currentData() or 1.0)
        self.comparison_waveform.set_window(start_sample, window_seconds)
        sample_rate = max(1, self.comparison_waveform.sample_rate)
        current = int(start_sample) / float(sample_rate)
        total = self.comparison_waveform.sample_count / float(sample_rate)
        self.comparison_time_label.setText(f"{current:.3f} s / {total:.3f} s")

    def _open_record_picker(self) -> None:
        records = self.store.list_records()
        if not records:
            QMessageBox.information(self, "暂无记录", "当前没有可读取的采样记录。")
            return
        dialog = RecordPickerDialog(records, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_record_dir:
            self._load_record(dialog.selected_record_dir)

    def _load_selected_history(self, *_args) -> None:
        row = self.history_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "请选择记录", "请先选择一条历史记录。")
            return
        item = self.history_table.item(row, 0)
        record_dir = str(item.data(Qt.UserRole) or "") if item else ""
        if record_dir:
            self._load_record(record_dir)

    def _load_record(self, record_dir: str) -> None:
        if self._job_thread is not None:
            return
        try:
            stored: StoredCapture = self.store.load_capture_record(record_dir)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"{type(exc).__name__}: {exc}")
            return
        status = str(stored.metadata.get("status") or "captured")
        source_id = str(stored.metadata.get("record_id") or stored.record_dir.name) if status == "diagnosed" else None
        self._set_current_capture(
            capture=stored.capture,
            hardware=stored.hardware_config,
            record_dir=stored.record_dir,
            source_record_id=source_id,
        )
        self.denoise_step_label.setText("降噪进度：历史采样已载入，请设置参数后应用")
        self.tabs.setCurrentIndex(TAB_DENOISE)

    def _refresh_history(self) -> None:
        if not hasattr(self, "history_table"):
            return
        records = self.store.list_records()
        self.history_table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                record.get("created_at", ""),
                _status_text(str(record.get("status", ""))),
                record.get("record_id", ""),
                _analysis_source_text(str(record.get("analysis_source", ""))),
                record.get("label", ""),
                f"{float(record.get('confidence') or 0.0):.6f}" if record.get("label") else "-",
                record.get("record_dir", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.UserRole, str(record.get("record_dir", "")))
                self.history_table.setItem(row, column, item)
        if records:
            self.history_table.selectRow(0)
        self._update_actions()

    def _browse_sdk(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 VK SDK",
            str(self.sdk_path.text() or "."),
            "VK SDK (*.dll *.so);;All Files (*)",
        )
        if path:
            self.sdk_path.setText(path)

    def _open_sound_check(self) -> None:
        if self._job_thread is not None:
            QMessageBox.warning(self, "后台任务运行中", "请等待当前采集或分析任务结束。")
            return
        dialog = SoundCaptureCheckDialog(self._hardware_config(), parent=self)
        dialog.recommendation_applied.connect(self._apply_sound_check_recommendation)
        dialog.exec()

    def _apply_sound_check_recommendation(self, channel: int, input_range_volts: float) -> None:
        self.channel_spin.setValue(int(channel))
        range_index = self.input_range_combo.findData(float(input_range_volts))
        if range_index >= 0:
            self.input_range_combo.setCurrentIndex(range_index)
        self.capture_status.setText(
            f"自检建议已应用：CH{int(channel)}、{float(input_range_volts):g} V；请重新自检后保存设置"
        )

    def _save_hardware_config(self, *, show_message: bool) -> None:
        save_json(self._hardware_config_path, self._hardware_config().to_dict())
        if show_message:
            QMessageBox.information(self, "保存完成", "硬件配置已保存。")

    def _save_hardware_and_next(self) -> None:
        self._save_hardware_config(show_message=False)
        self.tabs.setCurrentIndex(TAB_CAPTURE)
        self.capture_status.setText("硬件参数已保存，可以开始采集")

    def _save_denoise_config(self) -> None:
        save_json(CONFIG_DIR / "denoise.json", self._denoise_config().to_dict())
        QMessageBox.information(self, "保存完成", "当前降噪参数已保存为默认配置。")

    def _on_model_status(self, message: str) -> None:
        self.model_status_label.setText(f"模型状态：{message}")

    def _on_model_warmup_failed(self, message: str, details: str) -> None:
        self.model_status_label.setText(f"模型状态：预热失败 - {message}")
        self.result_text.setPlainText(details)

    def _clear_warmup_worker(self) -> None:
        self._warmup_thread = None
        self._warmup_worker = None


def _coerce_progress(progress_obj: object) -> DiagnosisProgress | None:
    if isinstance(progress_obj, DiagnosisProgress):
        return progress_obj
    if isinstance(progress_obj, dict):
        return DiagnosisProgress(
            stage=str(progress_obj.get("stage") or ""),
            percent=int(progress_obj.get("percent") or 0),
            message=str(progress_obj.get("message") or ""),
        )
    return None


def _status_text(status: str) -> str:
    return {"captured": "已采样", "diagnosed": "已诊断"}.get(status, status or "未知")


def _analysis_source_text(source: str) -> str:
    return {"raw": "原始信号", "denoised": "降噪信号"}.get(source, source or "-")


def _capture_check_status_text(status: str) -> str:
    return {
        "strong": "明确响应",
        "likely": "较大概率响应",
        "inconclusive": "证据不足",
        "clipped": "发生削波",
        "invalid": "采集无效",
    }.get(status, status or "未知")


def _format_volts(value: float) -> str:
    absolute = abs(float(value))
    if absolute >= 1.0:
        return f"{value:.3f} V"
    if absolute >= 0.001:
        return f"{value * 1000.0:.2f} mV"
    return f"{value * 1_000_000.0:.1f} uV"


def _spin(value: int, minimum: int, maximum: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(int(minimum), int(maximum))
    spin.setValue(int(value))
    return spin


def _double_spin(value: float, minimum: float, maximum: float, decimals: int) -> QDoubleSpinBox:
    spin = QDoubleSpinBox()
    spin.setRange(float(minimum), float(maximum))
    spin.setDecimals(int(decimals))
    spin.setValue(float(value))
    return spin


def _apply_style(app: QApplication) -> None:
    font = QFont("Noto Sans CJK SC")
    font.setPointSize(10)
    app.setFont(font)
    app.setStyleSheet(
        """
        QMainWindow, QWidget {
            background: #f4f7fb;
            color: #1f2937;
        }
        QTabWidget::pane {
            border: 1px solid #d6dee8;
            background: #ffffff;
        }
        QTabBar::tab {
            background: #e8eef6;
            border: 1px solid #d6dee8;
            padding: 9px 17px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            color: #0f766e;
            border-bottom-color: #ffffff;
        }
        QGroupBox {
            background: #ffffff;
            border: 1px solid #d6dee8;
            border-radius: 6px;
            margin-top: 12px;
            padding: 14px;
            font-weight: 600;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
        }
        QPushButton {
            background: #0f766e;
            color: white;
            border: 0;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: 600;
            min-height: 20px;
        }
        QPushButton:hover { background: #0d9488; }
        QPushButton:disabled {
            background: #a8b3c2;
            color: #eef2f7;
        }
        QPushButton[role="secondary"] {
            background: #e7edf4;
            color: #243447;
            border: 1px solid #cbd6e2;
        }
        QPushButton[role="secondary"]:hover { background: #dbe5ef; }
        QPushButton[role="danger"] { background: #b42318; }
        QPushButton[role="danger"]:hover { background: #d92d20; }
        QPushButton[role="icon"] {
            min-width: 34px;
            max-width: 34px;
            padding: 5px;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTableWidget {
            background: #ffffff;
            border: 1px solid #ccd6e2;
            border-radius: 4px;
            padding: 5px;
        }
        QProgressBar {
            border: 1px solid #ccd6e2;
            border-radius: 5px;
            text-align: center;
            background: #eef3f8;
            min-height: 18px;
        }
        QProgressBar::chunk {
            background: #14b8a6;
            border-radius: 4px;
        }
        QSlider::groove:horizontal {
            height: 5px;
            background: #d5dee8;
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            background: #0f766e;
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        QLabel#StatusLabel, QLabel#DialogTitle {
            color: #0f766e;
            font-weight: 600;
        }
        QLabel#DialogTitle { font-size: 16px; }
        QLabel#MutedLabel { color: #4b5563; }
        QLabel#MetricsLabel {
            background: #eef7f5;
            border: 1px solid #b9ddd6;
            border-radius: 5px;
            padding: 9px;
        }
        """
    )


def main() -> int:
    app = QApplication([])
    _apply_style(app)
    window = MainWindow()
    window.show()
    return app.exec()
