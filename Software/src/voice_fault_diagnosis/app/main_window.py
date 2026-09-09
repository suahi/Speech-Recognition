from __future__ import annotations

from pathlib import Path
import threading
import traceback

import numpy as np

try:
    from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - exercised only without the desktop extra
    raise RuntimeError("桌面界面依赖未安装，请运行：python -m pip install -e .[desktop]") from exc

from voice_fault_diagnosis.app.waveform_display import calculate_waveform_display
from voice_fault_diagnosis.audio_io import load_wav_preview
from voice_fault_diagnosis.config import EXPECTED_LABEL_CODES, PcAppConfig, PcConfigError, load_pc_config
from voice_fault_diagnosis.inference.wav_cnn import WavCnnEngine
from voice_fault_diagnosis.pipeline import run_imported_wav, run_realtime_capture
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


PREVIEW_SECONDS = 0.2
OLIVE = "#46543a"
OLIVE_DARK = "#34402c"
ERROR_RED = "#8a2f2f"
TEXT_DARK = "#202620"
TEXT_MUTED = "#5f685f"
PANEL = "#f7f8f5"
STEEL = "#d9ddd8"


class WaveformWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("waveform")
        self.setMinimumHeight(145)
        self.setMaximumHeight(160)
        self._voltage = np.zeros(0, dtype=np.float32)
        self._input_range_volts = 5.0
        self._display = calculate_waveform_display(self._voltage, full_scale_volts=self._input_range_volts)

    def set_voltage(self, voltage: np.ndarray, input_range_volts: float) -> None:
        self._voltage = np.asarray(voltage, dtype=np.float32).reshape(-1)
        self._input_range_volts = max(float(input_range_volts), 1e-6)
        self._display = calculate_waveform_display(
            self._voltage,
            adaptive=True,
            full_scale_volts=self._input_range_volts,
        )
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        rect = self.rect().adjusted(0, 0, -1, -1)
        plot = rect.adjusted(62, 10, -10, -24)
        painter.fillRect(rect, QColor("#ffffff"))
        painter.setPen(QPen(QColor("#aeb5ae"), 1))
        painter.drawRect(rect)
        painter.setPen(QPen(QColor("#e2e5e1"), 1))
        for index in range(1, 4):
            y = plot.top() + plot.height() * index / 4
            painter.drawLine(plot.left(), int(y), plot.right(), int(y))
        painter.setPen(QColor(TEXT_MUTED))
        painter.drawText(rect.left() + 6, plot.top() + 10, _format_volts(self._display.upper_volts))
        painter.drawText(rect.left() + 6, plot.center().y() + 4, _format_volts(self._display.center_volts))
        painter.drawText(rect.left() + 6, plot.bottom(), _format_volts(self._display.lower_volts))
        if self._display.samples.size < 2:
            painter.drawText(plot, Qt.AlignCenter, "等待波形数据")
            return
        painter.setRenderHint(QPainter.Antialiasing)
        center_y = plot.center().y()
        half_height = plot.height() * 0.5
        width = max(1, plot.width() - 8)
        painter.setPen(QPen(QColor(OLIVE), 1.2))
        if self._display.is_envelope:
            count = self._display.y_min_values.size
            for index, (minimum, maximum) in enumerate(
                zip(self._display.y_min_values, self._display.y_max_values)
            ):
                x = plot.left() + 4 + index * width / max(1, count - 1)
                painter.drawLine(
                    int(x),
                    int(center_y - maximum * half_height),
                    int(x),
                    int(center_y - minimum * half_height),
                )
            return
        points = []
        for index, value in enumerate(self._display.y_values):
            x = plot.left() + 4 + index * width / max(1, self._display.y_values.size - 1)
            points.append((int(x), int(center_y - value * half_height)))
        for left, right in zip(points, points[1:]):
            painter.drawLine(left[0], left[1], right[0], right[1])


class CaptureWorker(QObject):
    chunk_ready = Signal(object, object)
    stage_changed = Signal(str, int)
    completed = Signal(str, object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(self, config: PcAppConfig, engine: WavCnnEngine, store: LocalRecordStore) -> None:
        super().__init__()
        self.config = config
        self.engine = engine
        self.store = store
        self.stop_event = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            record_dir, prediction = run_realtime_capture(
                self.config,
                engine=self.engine,
                store=self.store,
                on_chunk=lambda voltage, info: self.chunk_ready.emit(voltage.copy(), dict(info)),
                stop_event=self.stop_event,
                on_stage=lambda message, value: self.stage_changed.emit(message, value),
            )
            self.completed.emit(str(record_dir), prediction)
        except Exception as exc:
            self.failed.emit(_friendly_error(exc), traceback.format_exc())
        finally:
            self.done.emit()

    def stop(self) -> None:
        self.stop_event.set()


class ImportWorker(QObject):
    preview_ready = Signal(object, object)
    stage_changed = Signal(str, int)
    completed = Signal(str, object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(
        self,
        config: PcAppConfig,
        source_path: str | Path,
        engine: WavCnnEngine,
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
            preview, info = load_wav_preview(self.source_path)
            self.preview_ready.emit(preview, info)
            record_dir, prediction = run_imported_wav(
                self.config,
                self.source_path,
                engine=self.engine,
                store=self.store,
                on_stage=lambda message, value: self.stage_changed.emit(message, value),
            )
            self.completed.emit(str(record_dir), prediction)
        except Exception as exc:
            self.failed.emit(_friendly_error(exc), traceback.format_exc())
        finally:
            self.done.emit()


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: PcAppConfig,
        *,
        engine: WavCnnEngine | None = None,
        store: LocalRecordStore | None = None,
    ) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle("声纹故障诊断演示系统")
        self.resize(1080, 760)
        self.setMinimumSize(960, 680)
        self._capture_thread: QThread | None = None
        self._capture_worker: CaptureWorker | None = None
        self._import_thread: QThread | None = None
        self._import_worker: ImportWorker | None = None
        self._task_kind: str | None = None
        self._preview_voltage = np.zeros(0, dtype=np.float32)
        self._active_import_path: Path | None = None
        self._engine = engine or WavCnnEngine(config.model)
        self._store = store or LocalRecordStore()
        self._build_page()
        self._apply_style()

    @property
    def is_busy(self) -> bool:
        return self._task_kind is not None

    def _build_page(self) -> None:
        page = QWidget()
        page.setObjectName("page")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(18, 16, 18, 18)
        outer.setSpacing(10)
        self.setCentralWidget(page)

        heading = QLabel("声纹故障诊断演示系统")
        heading.setObjectName("heading")
        subtitle = QLabel("麦克风  →  VK701N-SD CH2  →  网线直连 Windows 电脑")
        subtitle.setObjectName("subtitle")
        outer.addWidget(heading)
        outer.addWidget(subtitle)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setObjectName("main_splitter")
        self.main_splitter.setChildrenCollapsible(False)
        outer.addWidget(self.main_splitter, 1)

        controls = QFrame()
        controls.setObjectName("control_panel")
        left = QVBoxLayout(controls)
        left.setContentsMargins(14, 14, 14, 14)
        left.setSpacing(9)

        left.addWidget(_section_label("操作与输入"))
        button_row = QHBoxLayout()
        self.start_button = QPushButton("开始实时采集")
        self.start_button.setObjectName("primary_button")
        self.stop_button = QPushButton("停止采集")
        self.stop_button.setEnabled(False)
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        left.addLayout(button_row)
        self.load_button = QPushButton("加载 WAV 并识别")
        self.load_button.setObjectName("load_wav_button")
        left.addWidget(self.load_button)
        self.start_button.clicked.connect(self._start_capture)
        self.stop_button.clicked.connect(self._stop_capture)
        self.load_button.clicked.connect(self._choose_wav)

        left.addWidget(_section_label("当前来源"))
        self.source_label = QLabel("等待选择实时采集或 WAV 文件")
        self.source_label.setObjectName("source_label")
        self.source_label.setWordWrap(True)
        left.addWidget(self.source_label)

        left.addWidget(_section_label("任务状态"))
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("status_label")
        left.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        left.addWidget(self.progress)
        self.capture_summary = QLabel(
            f"默认参数：CH{self.config.hardware.adc_channel} / "
            f"{self.config.hardware.sample_rate / 1000:g} kHz / "
            f"{self.config.hardware.bit_mode} bit / ±{self.config.hardware.input_range_volts:g} V / "
            f"{self.config.capture_duration_seconds:g} 秒"
        )
        self.capture_summary.setObjectName("capture_summary")
        self.capture_summary.setWordWrap(True)
        left.addWidget(self.capture_summary)

        left.addWidget(_section_label("波形预览"))
        self.waveform = WaveformWidget()
        left.addWidget(self.waveform)
        left.addStretch(1)

        result_panel = QFrame()
        result_panel.setObjectName("result_panel")
        right = QVBoxLayout(result_panel)
        right.setContentsMargins(18, 16, 18, 16)
        right.setSpacing(9)
        right.addWidget(_section_label("诊断结果"))
        self.result_code_label = QLabel("--  等待识别")
        self.result_code_label.setObjectName("result_code")
        result_font = self.result_code_label.font()
        result_font.setPointSize(24)
        result_font.setBold(True)
        self.result_code_label.setFont(result_font)
        self.result_code_label.setWordWrap(True)
        right.addWidget(self.result_code_label)
        self.confidence_label = QLabel("置信度：--")
        self.confidence_label.setObjectName("confidence")
        right.addWidget(self.confidence_label)

        probability_title = QLabel("六分类概率")
        probability_title.setObjectName("probability_title")
        right.addWidget(probability_title)
        self.probability_rows: dict[str, QFrame] = {}
        self.probability_bars: dict[str, QProgressBar] = {}
        for code in EXPECTED_LABEL_CODES:
            row = QFrame()
            row.setObjectName(f"probability_row_{code}")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 5, 8, 5)
            row_layout.setSpacing(8)
            name = QLabel(f"{code}  {self.config.model.labels[code]}")
            name.setMinimumWidth(105)
            bar = QProgressBar()
            bar.setObjectName(f"probability_{code}")
            bar.setRange(0, 10000)
            bar.setValue(0)
            bar.setFormat("0.00%")
            row_layout.addWidget(name)
            row_layout.addWidget(bar, 1)
            right.addWidget(row)
            self.probability_rows[code] = row
            self.probability_bars[code] = bar

        right.addStretch(1)
        input_title = _section_label("输入信息")
        right.addWidget(input_title)
        self.input_label = QLabel("尚无输入。")
        self.input_label.setObjectName("input_info")
        self.input_label.setWordWrap(True)
        right.addWidget(self.input_label)
        self.record_label = QLabel("记录目录：--")
        self.record_label.setObjectName("record_path")
        self.record_label.setWordWrap(True)
        self.record_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right.addWidget(self.record_label)

        self.main_splitter.addWidget(controls)
        self.main_splitter.addWidget(result_panel)
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setSizes([400, 600])

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget#page {{ background: #e7eae6; color: {TEXT_DARK}; }}
            QLabel#heading {{ font-size: 24px; font-weight: 700; color: {OLIVE_DARK}; }}
            QLabel#subtitle {{ color: {TEXT_MUTED}; font-size: 13px; }}
            QFrame#control_panel, QFrame#result_panel {{ background: {PANEL}; border: 1px solid #aeb5ae; }}
            QLabel[section="true"] {{ color: {OLIVE_DARK}; font-size: 14px; font-weight: 700; border-bottom: 1px solid #bcc2bc; padding-bottom: 4px; }}
            QPushButton {{ min-height: 34px; padding: 0 10px; background: #eef0ed; border: 1px solid #8d958d; color: {TEXT_DARK}; font-weight: 600; }}
            QPushButton#primary_button, QPushButton#load_wav_button {{ background: {OLIVE}; border-color: {OLIVE_DARK}; color: white; }}
            QPushButton:hover {{ border-color: {OLIVE_DARK}; }}
            QPushButton:disabled {{ background: #d5d8d4; color: #8a908a; border-color: #b8bdb8; }}
            QLabel#source_label, QLabel#capture_summary, QLabel#input_info, QLabel#record_path {{ color: {TEXT_MUTED}; }}
            QLabel#status_label {{ font-size: 14px; font-weight: 700; color: {OLIVE_DARK}; }}
            QProgressBar {{ min-height: 20px; border: 1px solid #9ca49c; background: white; text-align: center; color: {TEXT_DARK}; }}
            QProgressBar::chunk {{ background: {OLIVE}; }}
            QLabel#result_code {{ font-size: 30px; font-weight: 700; color: {OLIVE_DARK}; padding: 8px 0; }}
            QLabel#confidence {{ font-size: 21px; font-weight: 700; color: {TEXT_DARK}; padding-bottom: 5px; }}
            QLabel#probability_title {{ font-size: 15px; font-weight: 700; color: {TEXT_DARK}; }}
            QFrame[winning="true"] {{ background: #e3e8de; border: 1px solid {OLIVE}; }}
            QFrame[winning="false"] {{ background: #f7f8f5; border: 1px solid #d4d8d3; }}
            QSplitter::handle {{ background: #c7ccc6; width: 5px; }}
            """
        )
        for row in self.probability_rows.values():
            row.setProperty("winning", "false")

    @Slot()
    def _start_capture(self) -> None:
        if self.is_busy:
            return
        self._task_kind = "capture"
        self._active_import_path = None
        self._preview_voltage = np.zeros(0, dtype=np.float32)
        self.waveform.set_voltage(self._preview_voltage, self.config.hardware.input_range_volts)
        self.source_label.setText(f"实时采集：VK701N-SD CH{self.config.hardware.adc_channel}")
        self.input_label.setText(
            f"实时采集｜CH{self.config.hardware.adc_channel}｜"
            f"{self.config.hardware.sample_rate} Hz｜{self.config.capture_duration_seconds:g} 秒"
        )
        self.capture_summary.setText("正在等待采集数据。")
        self.record_label.setText("记录目录：任务完成后生成")
        self._prepare_busy("正在准备实时采集…", stop_enabled=True)

        self._capture_thread = QThread(self)
        self._capture_worker = CaptureWorker(self.config, self._engine, self._store)
        self._capture_worker.moveToThread(self._capture_thread)
        self._capture_thread.started.connect(self._capture_worker.run)
        self._capture_worker.chunk_ready.connect(self._on_chunk)
        self._capture_worker.stage_changed.connect(self._on_stage)
        self._capture_worker.completed.connect(self._on_completed)
        self._capture_worker.failed.connect(self._on_failed)
        self._capture_worker.done.connect(self._capture_thread.quit)
        self._capture_worker.done.connect(self._capture_worker.deleteLater)
        self._capture_thread.finished.connect(self._clear_capture_worker)
        self._capture_thread.finished.connect(self._capture_thread.deleteLater)
        self._capture_thread.start()

    @Slot()
    def _choose_wav(self) -> None:
        if self.is_busy:
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 WAV 文件", "", "WAV 音频 (*.wav)")
        if not file_path:
            return
        self._start_import(file_path)

    def _start_import(self, source_path: str | Path) -> None:
        if self.is_busy:
            return
        self._task_kind = "import"
        self._active_import_path = Path(source_path).resolve()
        self.source_label.setText(f"WAV 文件：{self._active_import_path.name}")
        self.input_label.setText(f"导入文件：{self._active_import_path}")
        self.capture_summary.setText("正在读取 WAV 头信息。")
        self.record_label.setText("记录目录：任务完成后生成")
        self._prepare_busy("正在准备 WAV 识别…", stop_enabled=False)

        self._import_thread = QThread(self)
        self._import_worker = ImportWorker(self.config, self._active_import_path, self._engine, self._store)
        self._import_worker.moveToThread(self._import_thread)
        self._import_thread.started.connect(self._import_worker.run)
        self._import_worker.preview_ready.connect(self._on_import_preview)
        self._import_worker.stage_changed.connect(self._on_stage)
        self._import_worker.completed.connect(self._on_completed)
        self._import_worker.failed.connect(self._on_failed)
        self._import_worker.done.connect(self._import_thread.quit)
        self._import_worker.done.connect(self._import_worker.deleteLater)
        self._import_thread.finished.connect(self._clear_import_worker)
        self._import_thread.finished.connect(self._import_thread.deleteLater)
        self._import_thread.start()

    @Slot()
    def _stop_capture(self) -> None:
        if self._task_kind == "capture" and self._capture_worker is not None:
            self.stop_button.setEnabled(False)
            self.status_label.setText("正在停止采集；已有数据将继续归档并识别…")
            self._capture_worker.stop()

    def _prepare_busy(self, status: str, *, stop_enabled: bool) -> None:
        self.start_button.setEnabled(False)
        self.load_button.setEnabled(False)
        self.stop_button.setEnabled(stop_enabled)
        self.status_label.setStyleSheet(f"color: {OLIVE_DARK};")
        self.status_label.setText(status)
        self.progress.setValue(0)

    @Slot(str, int)
    def _on_stage(self, message: str, value: int) -> None:
        self.status_label.setText(message)
        self.progress.setValue(max(self.progress.value(), int(value)))

    @Slot(object, object)
    def _on_chunk(self, voltage: np.ndarray, info: dict[str, object]) -> None:
        values = np.asarray(voltage, dtype=np.float32)
        if values.size:
            preview_samples = max(1, int(self.config.hardware.sample_rate * PREVIEW_SECONDS))
            self._preview_voltage = np.concatenate((self._preview_voltage, values))[-preview_samples:]
            self.waveform.set_voltage(self._preview_voltage, self.config.hardware.input_range_volts)
        received = int(info.get("received_samples", 0))
        target = max(1, int(info.get("target_samples", 1)))
        self.progress.setValue(max(self.progress.value(), min(70, int(received * 70 / target))))
        self.capture_summary.setText(
            f"已采集 {received}/{target} 个样本｜读取 {int(info.get('read_calls', 0))} 次｜"
            f"空读取 {int(info.get('zero_read_count', 0))} 次"
        )

    @Slot(object, object)
    def _on_import_preview(self, samples: np.ndarray, info) -> None:
        self.waveform.set_voltage(np.asarray(samples, dtype=np.float32), 1.0)
        self.capture_summary.setText(
            f"WAV：{info.sample_rate} Hz｜{info.channels} 声道｜{info.duration_seconds:.2f} 秒"
        )
        if self._active_import_path is not None:
            self.input_label.setText(
                f"导入文件：{self._active_import_path}\n"
                f"原始参数：{info.sample_rate} Hz / {info.channels} 声道 / {info.duration_seconds:.2f} 秒\n"
                "模型输入：单声道 / 16000 Hz"
            )

    @Slot(str, object)
    def _on_completed(self, record_dir: str, prediction) -> None:
        self.status_label.setStyleSheet(f"color: {OLIVE_DARK};")
        self.status_label.setText("识别完成")
        self.progress.setValue(100)
        display_name = str(prediction.metadata.get("display_name", ""))
        self.result_code_label.setText(f"{prediction.label}  {display_name}")
        self.confidence_label.setText(f"置信度：{prediction.confidence * 100:.2f}%")
        self.record_label.setText(f"记录目录：{record_dir}")
        probabilities = list(prediction.probabilities)
        for index, code in enumerate(EXPECTED_LABEL_CODES):
            probability = float(probabilities[index]) if index < len(probabilities) else 0.0
            bar = self.probability_bars[code]
            bar.setValue(int(round(probability * 10000)))
            bar.setFormat(f"{probability * 100:.2f}%")
            row = self.probability_rows[code]
            row.setProperty("winning", "true" if code == prediction.label else "false")
            row.style().unpolish(row)
            row.style().polish(row)

    @Slot(str, str)
    def _on_failed(self, message: str, details: str) -> None:
        self.status_label.setStyleSheet(f"color: {ERROR_RED};")
        self.status_label.setText("任务失败")
        self.result_code_label.setText("--  未完成识别")
        self.confidence_label.setText(message)
        self.capture_summary.setText(message)
        self.progress.setValue(0)
        self._show_error(message, details)
        if self._capture_thread is None and self._import_thread is None:
            self._restore_idle_buttons()

    def _show_error(self, message: str, details: str) -> None:
        QMessageBox.critical(self, "识别失败", message)

    @Slot()
    def _clear_capture_worker(self) -> None:
        self._capture_worker = None
        self._capture_thread = None
        self._task_kind = None
        self._restore_idle_buttons()

    @Slot()
    def _clear_import_worker(self) -> None:
        self._import_worker = None
        self._import_thread = None
        self._task_kind = None
        self._restore_idle_buttons()

    def _restore_idle_buttons(self) -> None:
        self.start_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.stop_button.setEnabled(False)


def _section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("section", True)
    return label


def _format_volts(value: float) -> str:
    if abs(value) >= 1:
        return f"{value:.2f} V"
    if abs(value) >= 0.001:
        return f"{value * 1000:.1f} mV"
    return f"{value * 1_000_000:.0f} µV"


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, (ValueError, FileNotFoundError, RuntimeError)):
        return str(exc)
    return f"{type(exc).__name__}: {exc}"


def main() -> int:
    app = QApplication.instance() or QApplication([])
    try:
        config = load_pc_config()
    except PcConfigError as exc:
        QMessageBox.critical(None, "配置错误", str(exc))
        return 2
    window = MainWindow(config)
    window.show()
    return app.exec()
