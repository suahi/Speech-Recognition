from __future__ import annotations

import json

import numpy as np

from voice_fault_diagnosis.capture.vk701n import Vk701nCaptureSession
from voice_fault_diagnosis.config import load_pc_config
from voice_fault_diagnosis.models import CaptureResult, HardwareConfig, PredictionResult
from voice_fault_diagnosis.pipeline import run_realtime_capture
from voice_fault_diagnosis.storage.local_records import LocalRecordStore


class FakeVkSdk:
    def __init__(self, scripted_lengths: list[int] | None = None) -> None:
        self.scripted_lengths = list(scripted_lengths or [])
        self.events: list[str] = []
        self.read_calls = 0
        self.initialize_params = None

    def server_tcp_open(self, port: int) -> int:
        self.events.append("server_tcp_open")
        self.port = port
        return 0

    def server_tcp_close(self, port: int) -> int:
        self.events.append("server_tcp_close")
        return 0

    def server_get_connected_client_numbers(self) -> tuple[int, int]:
        return 0, 1

    def server_get_connected_client_handle(self, device_no: int) -> tuple[int, int, str]:
        return 0, 1000 + device_no, "192.168.1.199"

    def set_system_mode(self, device_no: int, sysmode: int, sample_method: int, sd_format: int) -> int:
        self.system_mode = (device_no, sysmode, sample_method, sd_format)
        return 0

    def initialize_all(self, device_no: int, params: list[int]) -> int:
        self.initialize_all_params = list(params)
        return 0

    def has_initialize(self) -> bool:
        return True

    def initialize(
        self,
        device_no: int,
        ref_voltage: float,
        bit_mode: int,
        sample_rate: int,
        range_ch1: int,
        range_ch2: int,
        range_ch3: int,
        range_ch4: int,
    ) -> int:
        self.initialize_params = (
            device_no,
            ref_voltage,
            bit_mode,
            sample_rate,
            range_ch1,
            range_ch2,
            range_ch3,
            range_ch4,
        )
        return 0

    def set_blocking_method(self, mode: int, timeout_ms: int) -> int:
        self.blocking = (mode, timeout_ms)
        return 0

    def start_sampling(self, device_no: int) -> int:
        self.events.append("start_sampling")
        return 0

    def stop_sampling(self, device_no: int) -> int:
        self.events.append("stop_sampling")
        return 0

    def get_four_channel(self, device_no: int, buffer, frame_count: int) -> int:
        self.read_calls += 1
        if self.read_calls <= len(self.scripted_lengths):
            count = self.scripted_lengths[self.read_calls - 1]
            if count <= 0:
                return 0
        else:
            count = min(frame_count, 5)
        for index in range(count):
            base = index * 4
            buffer[base] = float(index)
            buffer[base + 1] = 0.25
            buffer[base + 2] = 0.5
            buffer[base + 3] = 0.75
        return count


def _hardware(**overrides) -> HardwareConfig:
    values = {
        "capture_seconds": 0.001,
        "sample_rate": 50000,
        "adc_channel": 2,
        "read_frame_count": 5000,
        "input_range_volts": 5.0,
        "initialize_all_profile": "windows_c_example",
        "poll_interval_s": 0.0,
        "preflight_cleanup_delay_s": 0.0,
        "post_initialize_delay_s": 0.0,
        "post_start_delay_s": 0.0,
    }
    values.update(overrides)
    return HardwareConfig(**values)


def test_simulated_capture_uses_ch2_and_correct_range_code() -> None:
    sdk = FakeVkSdk()
    result = Vk701nCaptureSession(_hardware(), sdk=sdk).capture()

    assert result.raw_voltage.size == 50
    np.testing.assert_allclose(result.raw_voltage, 0.25)
    assert sdk.port == 8234
    assert sdk.system_mode == (0, 0, 0, 0)
    assert sdk.initialize_params == (0, 4.0, 1, 50000, 1, 1, 1, 1)
    assert sdk.blocking == (1, 1000)
    assert result.metadata["adc_channel"] == 2
    assert result.metadata["range_code"] == 1
    assert result.metadata["initialize_method"] == "VK70xNMC_Initialize"
    assert result.metadata["startup_profile"] == "windows_c_example"
    assert sdk.events[0] == "server_tcp_open"
    assert sdk.events[-2:] == ["stop_sampling", "server_tcp_close"]


def test_simulated_capture_ignores_empty_reads_and_reports_progress() -> None:
    sdk = FakeVkSdk(scripted_lengths=[1, 0, 0, 5])
    seen: list[tuple[int, int]] = []

    result = Vk701nCaptureSession(_hardware(), sdk=sdk).capture(
        on_chunk=lambda values, info: seen.append((int(info["recv_len"]), int(info["received_samples"])))
    )

    assert seen[:3] == [(1, 1), (0, 1), (0, 1)]
    assert result.raw_voltage.size == 50
    assert result.metadata["zero_read_count"] == 2


def test_selected_small_range_is_forwarded_to_all_channels() -> None:
    sdk = FakeVkSdk()

    Vk701nCaptureSession(_hardware(input_range_volts=0.1), sdk=sdk).capture()

    assert sdk.initialize_params == (0, 4.0, 1, 50000, 5, 5, 5, 5)


class FakeEngine:
    def predict(self, wav_path) -> PredictionResult:
        return PredictionResult(
            model_name="fake",
            class_index=1,
            label="C1",
            confidence=0.8,
            probabilities=[0.02, 0.8, 0.05, 0.04, 0.04, 0.05],
            top_k=[{"label": "C1", "display_name": "风扇", "confidence": 0.8}],
            metadata={"display_name": "风扇"},
        )


def test_realtime_pipeline_regression_with_simulated_session(tmp_path, monkeypatch) -> None:
    import voice_fault_diagnosis.pipeline as pipeline_module

    class FakeSession:
        def __init__(self, hardware) -> None:
            self.hardware = hardware

        def capture(self, on_chunk=None, stop_event=None) -> CaptureResult:
            values = np.linspace(-0.5, 0.5, 500, dtype=np.float32)
            if on_chunk is not None:
                on_chunk(values, {"recv_len": 500, "received_samples": 500, "target_samples": 500})
            return CaptureResult(values, self.hardware.sample_rate, {"daq_ip": "simulated"})

    monkeypatch.setattr(pipeline_module, "Vk701nCaptureSession", FakeSession)
    stages: list[int] = []
    record_dir, prediction = run_realtime_capture(
        load_pc_config(),
        engine=FakeEngine(),
        store=LocalRecordStore(tmp_path / "records"),
        on_stage=lambda message, progress: stages.append(progress),
    )

    assert prediction.label == "C1"
    assert stages == [5, 10, 72, 100]
    assert (record_dir / "raw_voltage.npy").is_file()
    assert (record_dir / "raw.wav").is_file()
    assert (record_dir / "result.json").is_file()
    metadata = json.loads((record_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["source_type"] == "realtime_capture"
