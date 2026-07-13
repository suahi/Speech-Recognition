from __future__ import annotations

import numpy as np

from voice_fault_diagnosis.capture.vk701n import Vk701nCaptureSession
from voice_fault_diagnosis.models import HardwareConfig


class FakeVkSdk:
    def __init__(
        self,
        scripted_lengths: list[int] | None = None,
        stop_sampling_status: int = 0,
        tcp_close_status: int = 0,
    ) -> None:
        self.scripted_lengths = list(scripted_lengths or [])
        self.stop_sampling_status = int(stop_sampling_status)
        self.tcp_close_status = int(tcp_close_status)
        self.opened = False
        self.closed = False
        self.started = False
        self.stopped = False
        self.params: list[int] = []
        self.params_history: list[list[int]] = []
        self.initialize_params = None
        self.blocking = None
        self.system_mode = None
        self.read_calls = 0
        self.events: list[str] = []

    def server_tcp_open(self, port: int) -> int:
        self.events.append("server_tcp_open")
        self.opened = True
        self.port = port
        return 0

    def server_tcp_close(self, port: int) -> int:
        self.events.append("server_tcp_close")
        self.closed = True
        return self.tcp_close_status

    def server_get_connected_client_numbers(self) -> tuple[int, int]:
        self.events.append("server_get_connected_client_numbers")
        return 0, 1

    def server_get_connected_client_handle(self, device_no: int) -> tuple[int, int, str]:
        self.events.append("server_get_connected_client_handle")
        return 0, 1000 + device_no, "192.168.1.199"

    def set_system_mode(self, device_no: int, sysmode: int, sample_method: int, sd_format: int) -> int:
        self.events.append("set_system_mode")
        self.system_mode = (device_no, sysmode, sample_method, sd_format)
        return 0

    def initialize_all(self, device_no: int, params: list[int]) -> int:
        self.events.append("initialize_all")
        self.params = list(params)
        self.params_history.append(list(params))
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
        self.events.append("initialize")
        self.initialize_params = (
            int(device_no),
            float(ref_voltage),
            int(bit_mode),
            int(sample_rate),
            int(range_ch1),
            int(range_ch2),
            int(range_ch3),
            int(range_ch4),
        )
        return 0

    def set_blocking_method(self, mode: int, timeout_ms: int) -> int:
        self.events.append("set_blocking_method")
        self.blocking = (mode, timeout_ms)
        return 0

    def start_sampling(self, device_no: int) -> int:
        self.events.append("start_sampling")
        self.started = True
        return 0

    def stop_sampling(self, device_no: int) -> int:
        self.events.append("stop_sampling")
        self.stopped = True
        return self.stop_sampling_status

    def get_four_channel(self, device_no: int, buffer, frame_count: int) -> int:
        self.events.append("get_four_channel")
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
            buffer[base + 1] = 99.0
            buffer[base + 2] = 98.0
            buffer[base + 3] = 97.0
        return count


def test_vk701n_capture_sequence_and_ch1_extraction() -> None:
    sdk = FakeVkSdk()
    config = HardwareConfig(
        capture_seconds=0.001,
        sample_rate=50000,
        read_frame_count=5000,
        preflight_cleanup_delay_s=0.0,
        post_initialize_delay_s=0.0,
        post_start_delay_s=0.0,
    )
    session = Vk701nCaptureSession(config, sdk=sdk)

    result = session.capture()

    assert sdk.opened
    assert sdk.started
    assert sdk.stopped
    assert sdk.closed
    assert sdk.events[0] == "server_tcp_open"
    assert sdk.system_mode == (0, 0, 0, 0)
    assert sdk.params == [50000, 4, 24, 50000, 1, 1, 1, 1, 1, 1, 1, 1]
    assert sdk.blocking == (1, 1000)
    assert result.raw_voltage.size == 50
    np.testing.assert_allclose(result.raw_voltage[:5], np.array([0, 1, 2, 3, 4], dtype=np.float32))
    assert result.metadata["daq_ip"] == "192.168.1.199"
    assert result.metadata["range_code"] == 1
    assert result.metadata["initialize_method"] == "VK70xNMC_InitializeAll"
    assert result.metadata["active_initialize_params"] == [50000, 4, 24, 50000, 1, 1, 1, 1, 1, 1, 1, 1]
    assert result.metadata["startup_profile"] == "code_source"
    assert result.metadata["startup_health_recv_lengths"] == []
    assert result.metadata["preflight_cleanup_enabled"] is False
    assert result.metadata["preflight_stop_sampling_status"] is None
    assert result.metadata["preflight_tcp_close_status"] is None
    assert len(result.legacy_input) == 50


def test_vk701n_capture_ignores_zero_reads_and_reports_progress() -> None:
    sdk = FakeVkSdk(scripted_lengths=[1, 0, 0, 5])
    config = HardwareConfig(
        capture_seconds=0.001,
        sample_rate=50000,
        poll_interval_s=0.0,
        preflight_cleanup_delay_s=0.0,
        post_initialize_delay_s=0.0,
        post_start_delay_s=0.0,
    )
    session = Vk701nCaptureSession(config, sdk=sdk)
    seen: list[tuple[int, int]] = []

    result = session.capture(
        on_chunk=lambda voltage, info: seen.append((int(info["recv_len"]), int(info["received_samples"])))
    )

    assert seen[:3] == [(1, 1), (0, 1), (0, 1)]
    assert result.raw_voltage.size == 50
    assert result.metadata["zero_read_count"] == 2
    assert result.metadata["positive_read_count"] >= 2


def test_vk701n_fixed_initialize_profile_is_available_for_field_debugging() -> None:
    sdk = FakeVkSdk()
    config = HardwareConfig(
        capture_seconds=0.001,
        sample_rate=50000,
        initialize_all_profile="fixed",
        post_initialize_delay_s=0.0,
        post_start_delay_s=0.0,
    )
    session = Vk701nCaptureSession(config, sdk=sdk)

    result = session.capture()

    assert result.raw_voltage.size == 50
    assert sdk.params == [50000, 4, 24, 0, 1, 1, 1, 1, 0, 0, 0, 0]
    assert result.metadata["startup_profile"] == "fixed"


def test_vk701n_preflight_cleanup_failure_does_not_block_startup() -> None:
    sdk = FakeVkSdk(stop_sampling_status=-7, tcp_close_status=-8)
    config = HardwareConfig(
        capture_seconds=0.001,
        sample_rate=50000,
        preflight_cleanup=True,
        preflight_cleanup_delay_s=0.0,
        post_initialize_delay_s=0.0,
        post_start_delay_s=0.0,
    )
    session = Vk701nCaptureSession(config, sdk=sdk)

    result = session.capture()

    assert sdk.started
    assert result.raw_voltage.size == 50
    assert result.metadata["preflight_stop_sampling_status"] == -7
    assert result.metadata["preflight_tcp_close_status"] == -8
