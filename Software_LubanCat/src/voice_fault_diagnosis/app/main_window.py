from __future__ import annotations

import threading
import traceback

import numpy as np

try:
    from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PySide6 is required to run the LubanCat desktop app") from exc

from voice_fault_diagnosis.app.waveform_display import WaveformDisplay, calculate_waveform_display
from voice_fault_diagnosis.capture.vk701n import Vk701nCaptureSession
from voice_fault_diagnosis.config import LightAppConfig, LightConfigError, load_light_config
from voice_fault_diagnosis.inference.wav_cnn import WavCnnEngine
from voice_fault_diagnosis.pipeline import run_wav_diagnosis
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


PREVIEW_SECONDS = 0.2


class WaveformWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(260)
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
        rect = self.rect().adjusted(1, 1, -1, -1)
        plot = rect.adjusted(76, 12, -12, -30)
        painter.fillRect(rect, QColor("#101820"))
        painter.setPen(QPen(QColor("#294255"), 1))
        for index in range(1, 5):
            y = plot.top() + plot.height() * index / 5
            painter.drawLine(plot.left(), int(y), plot.right(), int(y))
        painter.setPen(QColor("#b8c6d1"))
        painter.drawText(rect.left() + 8, plot.top() + 12, _format_volts(self._display.upper_volts))
        painter.drawText(rect.left() + 8, plot.center().y() + 4, _format_volts(self._display.center_volts))
        painter.drawText(rect.left() + 8, plot.bottom(), _format_volts(self._display.lower_volts))
        if self._display.samples.size < 2:
            painter.drawText(plot, Qt.AlignCenter, "等待声纹电压数据")
            return
        painter.setRenderHint(QPainter.Antialiasing)
        center_y = plot.center().y()
        half_height = plot.height() * 0.5
        width = max(1, plot.width() - 8)
        if self._display.is_envelope:
            count = self._display.y_min_values.size
            painter.setPen(QPen(QColor("#39d5a3"), 1.0))
            for index, (minimum, maximum) in enumerate(zip(self._display.y_min_values, self._display.y_max_values)):
                x = plot.left() + 4 + index * width / max(1, count - 1)
                painter.drawLine(int(x), int(center_y - maximum * half_height), int(x), int(center_y - minimum * half_height))
            return
        points = []
        for index, value in enumerate(self._display.y_values):
            x = plot.left() + 4 + index * width / max(1, self._display.y_values.size - 1)
            points.append((int(x), int(center_y - value * half_height)))
        painter.setPen(QPen(QColor("#39d5a3"), 1.4))
        for left, right in zip(points, points[1:]):
            painter.drawLine(left[0], left[1], right[0], right[1])


class CaptureWorker(QObject):
    chunk_ready = Signal(object, object)
    status_changed = Signal(str)
    stage_changed = Signal(int)
    completed = Signal(str, object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(self, config: LightAppConfig, engine: WavCnnEngine, store: LocalRecordStore) -> None:
        super().__init__()
        self.config = config
        self.engine = engine
        self.store = store
        self.stop_event = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            self.status_changed.emit("正在连接 VK701N-SD 采集卡…")
            self.stage_changed.emit(2)
            session = Vk701nCaptureSession(self.config.hardware)

            def on_chunk(voltage: np.ndarray, info: dict[str, object]) -> None:
                self.chunk_ready.emit(voltage.copy(), dict(info))

            self.status_changed.emit("正在采集声纹电压…")
            capture = session.capture(on_chunk=on_chunk, stop_event=self.stop_event)
            if capture.raw_voltage.size == 0:
                raise RuntimeError("未采集到有效声纹电压数据，未生成 WAV 或执行推理。")
            self.status_changed.emit("正在生成 WAV 并执行六类识别…")
            self.stage_changed.emit(72)
            record_dir, prediction = run_wav_diagnosis(
                capture=capture,
                hardware_config=self.config.hardware,
                engine=self.engine,
                store=self.store,
            )
            self.stage_changed.emit(100)
            self.completed.emit(str(record_dir), prediction)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}", traceback.format_exc())
        finally:
            self.done.emit()

    def stop(self) -> None:
        self.stop_event.set()


class MainWindow(QMainWindow):
    def __init__(self, config: LightAppConfig) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle("鲁班猫声纹采集与识别")
        self.resize(1080, 760)
        self._thread: QThread | None = None
        self._worker: CaptureWorker | None = None
        self._preview_voltage = np.zeros(0, dtype=np.float32)
        self._engine = WavCnnEngine(config.model)
        self._store = LocalRecordStore()
        self._build_page()

    def _build_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        self.setCentralWidget(page)

        title = QLabel("声纹采集与六类识别")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)
        details = QLabel(
            f"本次采集时长：{self.config.capture_duration_seconds:g} 秒。硬件与模型参数请在 "
            f"{self.config.source_path.name} 中修改。"
        )
        details.setStyleSheet("color: #536171;")
        layout.addWidget(details)

        controls = QHBoxLayout()
        self.start_button = QPushButton("开始采集")
        self.stop_button = QPushButton("停止并识别")
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self._start_capture)
        self.stop_button.clicked.connect(self._stop_capture)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform, 1)
        self.capture_summary = QLabel("尚未开始采集。")
        self.capture_summary.setWordWrap(True)
        self.capture_summary.setStyleSheet("color: #536171;")
        layout.addWidget(self.capture_summary)

        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("QFrame { background: #edf8f4; border: 1px solid #a4d9c5; border-radius: 8px; }")
        card_layout = QVBoxLayout(card)
        result_title = QLabel("识别结果")
        result_title.setStyleSheet("font-weight: 700;")
        self.result_label = QLabel("完成采集后将自动保存 WAV 并显示识别结果。")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-size: 18px;")
        self.record_label = QLabel("")
        self.record_label.setWordWrap(True)
        self.record_label.setStyleSheet("color: #536171;")
        card_layout.addWidget(result_title)
        card_layout.addWidget(self.result_label)
        card_layout.addWidget(self.record_label)
        layout.addWidget(card)

    def _start_capture(self) -> None:
        if self._thread is not None:
            return
        self._preview_voltage = np.zeros(0, dtype=np.float32)
        self.waveform.set_voltage(self._preview_voltage, self.config.hardware.input_range_volts)
        self.progress.setValue(0)
        self.status_label.setText("正在准备采集…")
        self.capture_summary.setText("正在等待采集数据。")
        self.result_label.setText("采集结束后将自动生成 WAV 并开始识别。")
        self.record_label.clear()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self._thread = QThread(self)
        self._worker = CaptureWorker(self.config, self._engine, self._store)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.chunk_ready.connect(self._on_chunk)
        self._worker.status_changed.connect(self.status_label.setText)
        self._worker.stage_changed.connect(self.progress.setValue)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._worker.done.connect(self._thread.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._clear_worker)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _stop_capture(self) -> None:
        if self._worker is not None:
            self.stop_button.setEnabled(False)
            self.status_label.setText("正在停止采集；已有数据将继续生成 WAV 并识别…")
            self._worker.stop()

    def _on_chunk(self, voltage: np.ndarray, info: dict[str, object]) -> None:
        if voltage.size:
            preview_samples = max(1, int(self.config.hardware.sample_rate * PREVIEW_SECONDS))
            self._preview_voltage = np.concatenate((self._preview_voltage, voltage))[-preview_samples:]
            self.waveform.set_voltage(self._preview_voltage, self.config.hardware.input_range_volts)
        received = int(info.get("received_samples", 0))
        target = max(1, int(info.get("target_samples", 1)))
        self.progress.setValue(min(70, int(received * 70 / target)))
        self.capture_summary.setText(
            f"已采集 {received}/{target} 个样本；读取次数 {int(info.get('read_calls', 0))}；"
            f"空读取 {int(info.get('zero_read_count', 0))} 次。"
        )

    def _on_completed(self, record_dir: str, prediction) -> None:
        display_name = str(prediction.metadata.get("display_name", ""))
        self.status_label.setText("识别完成")
        self.progress.setValue(100)
        self.result_label.setText(
            f"{prediction.label}｜{display_name}\n"
            f"置信度：{prediction.confidence * 100:.2f}%"
        )
        self.record_label.setText(f"WAV 与结果已保存至：{record_dir}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _on_failed(self, message: str, details: str) -> None:
        self.status_label.setText("采集或识别失败")
        self.result_label.setText(message)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.critical(self, "采集与识别失败", message + "\n\n" + details)

    def _clear_worker(self) -> None:
        self._worker = None
        self._thread = None


def _format_volts(value: float) -> str:
    if abs(value) >= 1:
        return f"{value:.3f} V"
    if abs(value) >= 0.001:
        return f"{value * 1000:.2f} mV"
    return f"{value * 1_000_000:.1f} µV"


def main() -> int:
    app = QApplication.instance() or QApplication([])
    try:
        config = load_light_config()
    except LightConfigError as exc:
        QMessageBox.critical(None, "配置错误", str(exc))
        return 2
    window = MainWindow(config)
    window.show()
    return app.exec()
