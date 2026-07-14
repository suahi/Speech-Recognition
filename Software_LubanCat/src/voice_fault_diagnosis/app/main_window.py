from __future__ import annotations

import threading
import traceback

import numpy as np

try:
    from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
    from PySide6.QtGui import QColor, QFont, QPainter, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
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
        QSpinBox,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PySide6 is required to run the desktop app") from exc

from voice_fault_diagnosis.app.waveform_display import WaveformDisplay, calculate_waveform_display
from voice_fault_diagnosis.capture.vk701n import Vk701nCaptureSession, resolve_sdk_library
from voice_fault_diagnosis.config import load_json, save_json
from voice_fault_diagnosis.inference.legacy_cnn import LegacyCnnEngine
from voice_fault_diagnosis.models import DenoiseConfig, DiagnosisProgress, HardwareConfig
from voice_fault_diagnosis.paths import CONFIG_DIR, LEGACY_MODEL_DIR
from voice_fault_diagnosis.pipeline import run_diagnosis
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


PREVIEW_WINDOW_SECONDS = 0.2


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
        for i in range(1, 5):
            y = plot_rect.top() + i * plot_rect.height() / 5
            painter.drawLine(plot_rect.left(), int(y), plot_rect.right(), int(y))
        for i in range(1, 7):
            x = plot_rect.left() + i * plot_rect.width() / 7
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

            mid_values = (display.y_min_values + display.y_max_values) * 0.5
            points: list[tuple[int, int]] = []
            for index, display_value in enumerate(mid_values):
                x = plot_rect.left() + 4 + index * width / max(1, count - 1)
                y = center_y - float(display_value) * y_scale
                points.append((int(x), int(y)))
            painter.setPen(QPen(QColor("#8af0d0"), 0.8))
            for left, right in zip(points, points[1:]):
                painter.drawLine(left[0], left[1], right[0], right[1])
            return

        points: list[tuple[int, int]] = []
        for index, display_value in enumerate(display.y_values):
            x = plot_rect.left() + 4 + index * width / max(1, display.y_values.size - 1)
            y = center_y - float(display_value) * y_scale
            points.append((int(x), int(y)))
        painter.setPen(QPen(QColor("#2ed3a6"), 1.6))
        for left, right in zip(points, points[1:]):
            painter.drawLine(left[0], left[1], right[0], right[1])


def _format_volts(value: float) -> str:
    abs_value = abs(float(value))
    if abs_value >= 1.0:
        return f"{value:.3f} V"
    if abs_value >= 0.001:
        return f"{value * 1000.0:.2f} mV"
    return f"{value * 1_000_000.0:.1f} uV"


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


class DiagnosisWorker(QObject):
    chunk_ready = Signal(object, object)
    progress_changed = Signal(object)
    status_changed = Signal(str)
    completed = Signal(str, object)
    failed = Signal(str, str)
    done = Signal()

    def __init__(self, hardware: HardwareConfig, denoise: DenoiseConfig, engine: LegacyCnnEngine) -> None:
        super().__init__()
        self.hardware = hardware
        self.denoise = denoise
        self.engine = engine
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

            self.status_changed.emit("采集结束，正在诊断...")
            self.progress_changed.emit(DiagnosisProgress("start", 1, "采集结束，准备诊断"))
            record_dir, prediction = run_diagnosis(
                capture=capture,
                hardware_config=self.hardware,
                denoise_config=self.denoise,
                engine=self.engine,
                store=LocalRecordStore(),
                progress_callback=self.progress_changed.emit,
            )
            self.completed.emit(str(record_dir), prediction)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}", traceback.format_exc())
        finally:
            self.done.emit()

    def stop(self) -> None:
        self.stop_event.set()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("声纹故障诊断系统 - 鲁班猫")
        self.resize(1280, 820)
        self._thread: QThread | None = None
        self._worker: DiagnosisWorker | None = None
        self._warmup_thread: QThread | None = None
        self._warmup_worker: ModelWarmupWorker | None = None
        self.preview_voltage = np.zeros(0, dtype=np.float32)
        self.active_sample_rate = 50000
        self.active_input_range_volts = 5.0
        self.store = LocalRecordStore()
        self.engine = LegacyCnnEngine()
        self._hardware_config_path = CONFIG_DIR / "hardware_vk701n.json"

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_hardware_tab()
        self._build_capture_tab()
        self._build_denoise_tab()
        self._build_model_tab()
        self._build_result_tab()
        self._build_history_tab()
        self._refresh_history()
        self._start_model_warmup()

    def _build_hardware_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        group = QGroupBox("VK701N-SD 硬件设置")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)

        cfg = HardwareConfig.from_dict(load_json(self._hardware_config_path, {}))
        sdk_default = cfg.sdk_library_path or str(resolve_sdk_library(""))
        self.sdk_path = QLineEdit(sdk_default)
        browse = QPushButton("选择 SDK")
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
        form.addRow("每次读取点数", self.frame_spin)
        form.addRow("legacy 增益", self.gain_spin)
        form.addRow("阻塞超时 ms", self.blocking_spin)
        form.addRow("采集时长 s", self.capture_seconds_spin)
        form.addRow("初始化 profile", self.initialize_profile_combo)

        save_button = QPushButton("保存硬件配置")
        save_button.clicked.connect(self._save_hardware_config)
        layout.addWidget(group)
        layout.addWidget(save_button, 0, Qt.AlignLeft)
        layout.addStretch(1)
        self.tabs.addTab(page, "硬件设置")

    def _build_capture_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        controls = QHBoxLayout()
        self.start_button = QPushButton("开始采集")
        self.stop_button = QPushButton("停止并诊断")
        self.stop_button.setEnabled(False)
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
        self.diagnosis_step_label = QLabel("诊断进度：等待采集")
        self.diagnosis_step_label.setObjectName("MutedLabel")
        self.diagnosis_progress_bar = QProgressBar()
        self.diagnosis_progress_bar.setRange(0, 100)
        self.diagnosis_progress_bar.setFormat("%p%")
        self.waveform = WaveformWidget()
        self.capture_summary = QPlainTextEdit()
        self.capture_summary.setReadOnly(True)
        self.capture_summary.setMinimumHeight(150)

        layout.addLayout(controls)
        layout.addWidget(self.capture_status)
        layout.addWidget(self.level_bar)
        layout.addWidget(self.capture_progress_bar)
        layout.addWidget(self.diagnosis_step_label)
        layout.addWidget(self.diagnosis_progress_bar)
        layout.addWidget(QLabel("实时声纹电压"))
        layout.addWidget(self.waveform)
        layout.addWidget(QLabel("采集摘要"))
        layout.addWidget(self.capture_summary)
        self.tabs.addTab(page, "采集诊断")

    def _build_denoise_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        group = QGroupBox("降噪设置")
        form = QFormLayout(group)
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
        self.wavelet_name = QLineEdit(cfg.wavelet)
        self.wavelet_level = _spin(cfg.wavelet_level, 1, 8)
        form.addRow(self.denoise_enabled)
        form.addRow(self.bandpass_enabled)
        form.addRow("低截止 Hz", self.low_spin)
        form.addRow("高截止 Hz", self.high_spin)
        form.addRow("滤波阶数", self.order_spin)
        form.addRow(self.wavelet_enabled)
        form.addRow("小波基", self.wavelet_name)
        form.addRow("小波层数", self.wavelet_level)
        save_button = QPushButton("保存降噪配置")
        save_button.clicked.connect(self._save_denoise_config)
        layout.addWidget(group)
        layout.addWidget(save_button, 0, Qt.AlignLeft)
        layout.addStretch(1)
        self.tabs.addTab(page, "降噪配置")

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
                    "说明: 使用 CodeSource/python_continuous_sampling 的 best_model_cnn.pt 和 mean_std.pkl。",
                ]
            )
        )
        layout.addWidget(self.model_status_label)
        layout.addWidget(text)
        self.tabs.addTab(page, "模型管理")

    def _build_result_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        self.result_text = QPlainTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlainText("完成采集并诊断后显示结果。")
        layout.addWidget(self.result_text)
        self.tabs.addTab(page, "诊断结果")

    def _build_history_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        refresh = QPushButton("刷新历史记录")
        refresh.clicked.connect(self._refresh_history)
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["时间", "记录 ID", "类别", "置信度", "目录"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(refresh, 0, Qt.AlignLeft)
        layout.addWidget(self.history_table)
        self.tabs.addTab(page, "历史记录")

    def _hardware_config(self) -> HardwareConfig:
        data = load_json(self._hardware_config_path, {})
        data.update(
            {
                "sdk_library_path": self.sdk_path.text().strip(),
                "server_port": int(self.port_spin.value()),
                "device_no": int(self.device_spin.value()),
                "adc_channel": int(self.channel_spin.value()),
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
            wavelet=self.wavelet_name.text().strip() or "db4",
            wavelet_level=int(self.wavelet_level.value()),
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
        if self._thread is not None:
            return
        hardware = self._hardware_config()
        denoise = self._denoise_config()
        self.active_sample_rate = int(hardware.sample_rate)
        self.active_input_range_volts = float(hardware.input_range_volts)
        self.preview_voltage = np.zeros(0, dtype=np.float32)
        self.waveform.set_display_mode(self.auto_scale_checkbox.isChecked(), self.active_input_range_volts)
        self.waveform.set_audio(self.preview_voltage)
        self.capture_progress_bar.setValue(0)
        self.diagnosis_progress_bar.setValue(0)
        self.diagnosis_step_label.setText("诊断进度：等待采集结束")
        self.level_bar.setValue(0)
        self.result_text.setPlainText("正在采集，停止后将自动诊断。")
        self.capture_status.setText("正在采集声纹电压...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self._thread = QThread(self)
        self._worker = DiagnosisWorker(hardware, denoise, self.engine)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.status_changed.connect(self.capture_status.setText)
        self._worker.chunk_ready.connect(self._on_chunk)
        self._worker.progress_changed.connect(self._on_diagnosis_progress)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._worker.done.connect(self._thread.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_worker)
        self._thread.start()

    def _stop_capture(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self.capture_status.setText("正在停止采集，随后进入诊断...")
            self.diagnosis_step_label.setText("诊断进度：等待采集线程收尾")
            self.stop_button.setEnabled(False)

    def _on_display_mode_changed(self) -> None:
        self.waveform.set_display_mode(self.auto_scale_checkbox.isChecked(), self.active_input_range_volts)
        self.waveform.set_audio(self.preview_voltage)

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
                    f"本轮 recvLen: {info.get('recv_len', 0)}",
                    f"当前样本数: {received}",
                    f"目标样本数: {target}",
                    f"读取次数: {info.get('read_calls', 0)}",
                    f"连续 0 读取次数: {info.get('zero_read_count', 0)}",
                    f"最近 SDK 返回: {info.get('last_recv_lengths', [])}",
                    f"预览窗口: {PREVIEW_WINDOW_SECONDS:.2f} s",
                    f"启动 profile: {info.get('startup_profile', '')}",
                    f"显示模式: {display_mode}",
                    f"均值: {stats.mean_volts:.9f} V",
                    f"交流 RMS: {stats.ac_rms_volts:.9f} V",
                    f"峰峰值: {stats.peak_to_peak_volts:.9f} V",
                    f"显示范围: {stats.lower_volts:.9f} V ~ {stats.upper_volts:.9f} V",
                    f"显示缩放: {self.waveform.display_scale:.1f}x",
                ]
            )
        )

    def _on_diagnosis_progress(self, progress_obj: object) -> None:
        if isinstance(progress_obj, DiagnosisProgress):
            percent = max(0, min(100, int(progress_obj.percent)))
            self.diagnosis_progress_bar.setValue(percent)
            self.diagnosis_step_label.setText(f"诊断进度：{progress_obj.message}")
        elif isinstance(progress_obj, dict):
            percent = max(0, min(100, int(progress_obj.get("percent") or 0)))
            self.diagnosis_progress_bar.setValue(percent)
            self.diagnosis_step_label.setText(f"诊断进度：{progress_obj.get('message', '')}")

    def _on_completed(self, record_dir: str, prediction) -> None:
        self.capture_status.setText("诊断完成")
        self.capture_progress_bar.setValue(100)
        self.diagnosis_progress_bar.setValue(100)
        self.diagnosis_step_label.setText("诊断进度：完成")
        timings = prediction.metadata.get("timings", {}) if isinstance(prediction.metadata, dict) else {}
        timing_lines = [
            f"  {key}: {float(value):.3f} s"
            for key, value in timings.items()
            if isinstance(value, (int, float))
        ]
        self.result_text.setPlainText(
            "\n".join(
                [
                    f"记录目录: {record_dir}",
                    f"模型: {prediction.model_name}",
                    f"分类索引: {prediction.class_index}",
                    f"故障标签: {prediction.label}",
                    f"置信度: {prediction.confidence:.6f}",
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
        self._refresh_history()
        self.tabs.setCurrentIndex(4)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _on_failed(self, message: str, details: str) -> None:
        self.capture_status.setText("诊断失败")
        self.diagnosis_step_label.setText("诊断进度：失败")
        self.result_text.setPlainText(details)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.critical(self, "诊断失败", message)

    def _on_model_status(self, message: str) -> None:
        self.model_status_label.setText(f"模型状态：{message}")

    def _on_model_warmup_failed(self, message: str, details: str) -> None:
        self.model_status_label.setText(f"模型状态：预热失败 - {message}")
        self.result_text.setPlainText(details)

    def _clear_worker(self) -> None:
        self._thread = None
        self._worker = None

    def _clear_warmup_worker(self) -> None:
        self._warmup_thread = None
        self._warmup_worker = None

    def _refresh_history(self) -> None:
        if not hasattr(self, "history_table"):
            return
        records = self.store.list_records()
        self.history_table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                record.get("created_at", ""),
                record.get("record_id", ""),
                record.get("label", ""),
                f"{float(record.get('confidence') or 0.0):.6f}",
                record.get("record_dir", ""),
            ]
            for col, value in enumerate(values):
                self.history_table.setItem(row, col, QTableWidgetItem(str(value)))

    def _browse_sdk(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 VK SDK",
            str(self.sdk_path.text() or "."),
            "VK SDK (*.dll *.so);;All Files (*)",
        )
        if path:
            self.sdk_path.setText(path)

    def _save_hardware_config(self) -> None:
        save_json(self._hardware_config_path, self._hardware_config().to_dict())
        QMessageBox.information(self, "保存完成", "硬件配置已保存。")

    def _save_denoise_config(self) -> None:
        save_json(CONFIG_DIR / "denoise.json", self._denoise_config().to_dict())
        QMessageBox.information(self, "保存完成", "降噪配置已保存。")


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
    font = QFont("Microsoft YaHei")
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
            padding: 8px 18px;
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
        }
        QPushButton:hover {
            background: #0d9488;
        }
        QPushButton:disabled {
            background: #a8b3c2;
            color: #eef2f7;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTableWidget {
            background: #ffffff;
            border: 1px solid #ccd6e2;
            border-radius: 4px;
            padding: 4px;
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
        QLabel#StatusLabel {
            color: #0f766e;
            font-weight: 600;
        }
        QLabel#MutedLabel {
            color: #4b5563;
        }
        """
    )


def main() -> int:
    app = QApplication([])
    _apply_style(app)
    window = MainWindow()
    window.show()
    return app.exec()
