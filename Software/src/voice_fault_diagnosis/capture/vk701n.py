from __future__ import annotations

import ctypes
from contextlib import contextmanager
import os
import platform
from pathlib import Path
import threading
import time
from typing import Any, Callable

import numpy as np

from voice_fault_diagnosis.legacy_format import voltage_to_legacy_bytes
from voice_fault_diagnosis.models import CaptureResult, HardwareConfig
from voice_fault_diagnosis.paths import VENDOR_VK701N_DIR


class Vk701nError(RuntimeError):
    """Raised when the VK701N SDK reports an error."""


_SDK_LOCK = threading.RLock()


class CtypesVk701nSdk:
    def __init__(self, library_path: str | Path) -> None:
        self.library_path = Path(library_path).resolve()
        self.library_dir = self.library_path.parent
        self._dll_dir_cookie = None
        if hasattr(os, "add_dll_directory"):
            self._dll_dir_cookie = os.add_dll_directory(str(self.library_dir))
        with self._sdk_working_directory():
            self._dll = ctypes.CDLL(str(self.library_path))
            self._bind_functions()

    @contextmanager
    def _sdk_working_directory(self):
        with _SDK_LOCK:
            previous = Path.cwd()
            os.chdir(self.library_dir)
            try:
                yield
            finally:
                os.chdir(previous)

    def _bind_functions(self) -> None:
        self._dll.Server_TCPOpen.argtypes = [ctypes.c_int]
        self._dll.Server_TCPOpen.restype = ctypes.c_int
        self._dll.Server_TCPClose.argtypes = [ctypes.c_int]
        self._dll.Server_TCPClose.restype = ctypes.c_int
        self._dll.Server_Get_ConnectedClientNumbers.argtypes = [ctypes.POINTER(ctypes.c_int)]
        self._dll.Server_Get_ConnectedClientNumbers.restype = ctypes.c_int
        self._dll.Server_Get_ConnectedClientHandle.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_char),
        ]
        self._dll.Server_Get_ConnectedClientHandle.restype = ctypes.c_int
        self._dll.VK70xNMC_Set_SystemMode.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
        ]
        self._dll.VK70xNMC_Set_SystemMode.restype = ctypes.c_int
        self._dll.VK70xNMC_InitializeAll.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
        ]
        self._dll.VK70xNMC_InitializeAll.restype = ctypes.c_int
        self._dll.VK70xNMC_Set_BlockingMethodtoReadADCResult.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
        ]
        self._dll.VK70xNMC_Set_BlockingMethodtoReadADCResult.restype = ctypes.c_int
        self._dll.VK70xNMC_StartSampling.argtypes = [ctypes.c_int]
        self._dll.VK70xNMC_StartSampling.restype = ctypes.c_int
        self._dll.VK70xNMC_StopSampling.argtypes = [ctypes.c_int]
        self._dll.VK70xNMC_StopSampling.restype = ctypes.c_int
        self._dll.VK70xNMC_GetFourChannel.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_int,
        ]
        self._dll.VK70xNMC_GetFourChannel.restype = ctypes.c_int

    def server_tcp_open(self, port: int) -> int:
        with self._sdk_working_directory():
            return int(self._dll.Server_TCPOpen(int(port)))

    def server_tcp_close(self, port: int) -> int:
        with self._sdk_working_directory():
            return int(self._dll.Server_TCPClose(int(port)))

    def server_get_connected_client_numbers(self) -> tuple[int, int]:
        count = ctypes.c_int(0)
        with self._sdk_working_directory():
            status = int(self._dll.Server_Get_ConnectedClientNumbers(ctypes.byref(count)))
        return status, int(count.value)

    def server_get_connected_client_handle(self, device_no: int) -> tuple[int, int, str]:
        handle = ctypes.c_int(0)
        ip_buffer = ctypes.create_string_buffer(128)
        with self._sdk_working_directory():
            status = int(
                self._dll.Server_Get_ConnectedClientHandle(
                    int(device_no),
                    ctypes.byref(handle),
                    ip_buffer,
                )
            )
        return status, int(handle.value), ip_buffer.value.decode(errors="replace")

    def set_system_mode(self, device_no: int, sysmode: int, sample_method: int, sd_format: int) -> int:
        with self._sdk_working_directory():
            return int(
                self._dll.VK70xNMC_Set_SystemMode(
                    int(device_no),
                    int(sysmode),
                    int(sample_method),
                    int(sd_format),
                )
            )

    def initialize_all(self, device_no: int, params: list[int]) -> int:
        param_array = (ctypes.c_int * len(params))(*[int(item) for item in params])
        with self._sdk_working_directory():
            return int(self._dll.VK70xNMC_InitializeAll(int(device_no), param_array, len(params)))

    def set_blocking_method(self, mode: int, timeout_ms: int) -> int:
        with self._sdk_working_directory():
            return int(
                self._dll.VK70xNMC_Set_BlockingMethodtoReadADCResult(
                    int(mode),
                    int(timeout_ms),
                )
            )

    def start_sampling(self, device_no: int) -> int:
        with self._sdk_working_directory():
            return int(self._dll.VK70xNMC_StartSampling(int(device_no)))

    def stop_sampling(self, device_no: int) -> int:
        with self._sdk_working_directory():
            return int(self._dll.VK70xNMC_StopSampling(int(device_no)))

    def get_four_channel(self, device_no: int, buffer: Any, frame_count: int) -> int:
        with self._sdk_working_directory():
            return int(self._dll.VK70xNMC_GetFourChannel(int(device_no), buffer, int(frame_count)))


class Vk701nCaptureSession:
    def __init__(self, config: HardwareConfig, sdk: Any | None = None) -> None:
        self.config = config
        self._sdk = sdk
        self._server_open = False
        self._sampling_started = False
        self._device_ip = ""
        self._device_handle: int | None = None
        self._library_path: Path | None = None
        self._buffer: Any | None = None
        self._buffer_capacity = 0

    def start(self) -> dict[str, Any]:
        sdk = self._ensure_sdk()
        cfg = self.config
        self._check("open TCP server", sdk.server_tcp_open(cfg.server_port), allow_positive=True)
        self._server_open = True
        self._wait_for_device(sdk)

        status, handle, ip = sdk.server_get_connected_client_handle(cfg.device_no)
        self._check("get DAQ handle", status)
        self._device_handle = handle
        self._device_ip = ip

        self._check("set system mode", sdk.set_system_mode(cfg.device_no, 0, 0, 0))
        self._check("initialize all", sdk.initialize_all(cfg.device_no, self._initialize_all_params()))
        self._check("set blocking read", sdk.set_blocking_method(1, cfg.blocking_timeout_ms))
        self._check("start sampling", sdk.start_sampling(cfg.device_no))
        self._sampling_started = True
        return self.runtime_metadata()

    def stop(self) -> None:
        if self._sdk is None:
            return
        if self._sampling_started:
            try:
                self._sdk.stop_sampling(self.config.device_no)
            finally:
                self._sampling_started = False
        if self._server_open:
            try:
                self._sdk.server_tcp_close(self.config.server_port)
            finally:
                self._server_open = False

    def capture(
        self,
        duration_seconds: float | None = None,
        on_chunk: Callable[[np.ndarray, dict[str, Any]], None] | None = None,
        stop_event: threading.Event | None = None,
    ) -> CaptureResult:
        cfg = self.config
        target_seconds = float(duration_seconds if duration_seconds is not None else cfg.capture_seconds)
        target_samples = max(1, int(cfg.sample_rate * target_seconds))
        raw_chunks: list[np.ndarray] = []
        legacy = bytearray()
        read_calls = 0
        zero_read_count = 0
        positive_read_count = 0
        received_samples = 0
        started_at = time.monotonic()
        last_positive_at = started_at
        stopped_by_user = False
        last_recv_lengths: list[int] = []

        try:
            self.start()
            started_at = time.monotonic()
            last_positive_at = started_at
            while received_samples < target_samples:
                if stop_event is not None and stop_event.is_set():
                    stopped_by_user = True
                    break

                now = time.monotonic()
                seconds_since_last_data = now - last_positive_at
                if seconds_since_last_data >= float(cfg.zero_read_timeout_s):
                    raise Vk701nError(
                        "DAQ read timed out: "
                        f"received_samples={received_samples}, "
                        f"target_samples={target_samples}, "
                        f"read_calls={read_calls}, "
                        f"zero_read_count={zero_read_count}, "
                        f"last_recv_lengths={last_recv_lengths[-20:]}, "
                        f"range_code={self._input_range_code()}, "
                        f"initialize_all_params={self._initialize_all_params()}"
                    )

                recv_len, voltage = self.read_voltage_chunk(cfg.read_frame_count)
                read_calls += 1
                last_recv_lengths.append(int(recv_len))
                last_recv_lengths = last_recv_lengths[-20:]
                if recv_len == 0:
                    zero_read_count += 1
                    if on_chunk is not None:
                        on_chunk(
                            np.zeros(0, dtype=np.float32),
                            {
                                "recv_len": 0,
                                "received_samples": received_samples,
                                "target_samples": target_samples,
                                "read_calls": read_calls,
                                "zero_read_count": zero_read_count,
                                "positive_read_count": positive_read_count,
                                "seconds_since_last_data": seconds_since_last_data,
                                "last_recv_lengths": list(last_recv_lengths),
                                **self.runtime_metadata(),
                            },
                        )
                    if cfg.poll_interval_s > 0:
                        time.sleep(float(cfg.poll_interval_s))
                    continue

                positive_read_count += 1
                last_positive_at = time.monotonic()
                remaining = target_samples - received_samples
                kept = voltage[:remaining].astype(np.float32, copy=False)
                raw_chunks.append(kept)
                legacy.extend(voltage_to_legacy_bytes(kept, gain=cfg.gain))
                received_samples += int(kept.size)
                if on_chunk is not None:
                    on_chunk(
                        kept,
                        {
                            "recv_len": int(recv_len),
                            "chunk_samples": int(kept.size),
                            "received_samples": received_samples,
                            "target_samples": target_samples,
                            "read_calls": read_calls,
                            "zero_read_count": zero_read_count,
                            "positive_read_count": positive_read_count,
                            "seconds_since_last_data": 0.0,
                            "last_recv_lengths": list(last_recv_lengths),
                            **self.runtime_metadata(),
                        },
                    )

            raw_voltage = (
                np.concatenate(raw_chunks).astype(np.float32, copy=False)
                if raw_chunks
                else np.zeros(0, dtype=np.float32)
            )
            elapsed = max(0.0, time.monotonic() - started_at)
            return CaptureResult(
                raw_voltage=raw_voltage,
                legacy_input=bytes(legacy),
                sample_rate=int(cfg.sample_rate),
                metadata={
                    **self.runtime_metadata(),
                    "target_samples": int(target_samples),
                    "received_samples": int(raw_voltage.size),
                    "requested_duration_seconds": float(target_seconds),
                    "actual_capture_seconds": elapsed,
                    "actual_audio_seconds": raw_voltage.size / float(cfg.sample_rate),
                    "read_calls": int(read_calls),
                    "zero_read_count": int(zero_read_count),
                    "positive_read_count": int(positive_read_count),
                    "last_recv_lengths": list(last_recv_lengths),
                    "stopped_by_user": bool(stopped_by_user),
                },
            )
        finally:
            self.stop()

    def read_voltage_chunk(self, frame_count: int) -> tuple[int, np.ndarray]:
        if self._sdk is None:
            raise RuntimeError("SDK is not loaded")
        cfg = self.config
        if cfg.adc_total_channels != 4:
            raise ValueError("VK70xNMC_GetFourChannel requires adc_total_channels=4")
        if not 1 <= cfg.adc_channel <= cfg.adc_total_channels:
            raise ValueError("adc_channel must be between 1 and adc_total_channels")

        raw_buffer = self._get_buffer(frame_count * cfg.adc_total_channels)
        recv_len = int(self._sdk.get_four_channel(cfg.device_no, raw_buffer, int(frame_count)))
        if recv_len < 0:
            raise Vk701nError(f"GetFourChannel failed with status {recv_len}")
        if recv_len == 0:
            return 0, np.zeros(0, dtype=np.float32)

        used = min(int(recv_len), int(frame_count))
        interleaved = np.ctypeslib.as_array(raw_buffer)[: used * cfg.adc_total_channels]
        voltage = interleaved.reshape(used, cfg.adc_total_channels)[:, cfg.adc_channel - 1]
        return used, voltage.astype(np.float32, copy=True)

    def runtime_metadata(self) -> dict[str, Any]:
        range_code = self._input_range_code()
        initialize_params = self._initialize_all_params()
        return {
            "sdk_library_path": str(self._library_path or self.config.sdk_library_path or ""),
            "server_port": int(self.config.server_port),
            "device_no": int(self.config.device_no),
            "daq_ip": self._device_ip,
            "daq_handle": self._device_handle,
            "adc_channel": int(self.config.adc_channel),
            "adc_total_channels": int(self.config.adc_total_channels),
            "sample_rate": int(self.config.sample_rate),
            "bit_mode": int(self.config.bit_mode),
            "read_frame_count": int(self.config.read_frame_count),
            "gain": float(self.config.gain),
            "blocking_timeout_ms": int(self.config.blocking_timeout_ms),
            "input_range_volts": float(self.config.input_range_volts),
            "range_code": int(range_code),
            "initialize_method": "VK70xNMC_InitializeAll",
            "initialize_all_params": initialize_params,
        }

    def _ensure_sdk(self) -> Any:
        if self._sdk is not None:
            return self._sdk
        self._library_path = resolve_sdk_library(self.config.sdk_library_path)
        self._sdk = CtypesVk701nSdk(self._library_path)
        return self._sdk

    def _wait_for_device(self, sdk: Any) -> None:
        deadline = time.monotonic() + float(self.config.connect_timeout_s)
        last_status = -1
        last_count = 0
        while True:
            status, count = sdk.server_get_connected_client_numbers()
            last_status = int(status)
            last_count = int(count)
            if status >= 0 and count > int(self.config.device_no):
                return
            if time.monotonic() >= deadline:
                raise Vk701nError(
                    f"DAQ connection timed out: status={last_status}, connected={last_count}"
                )
            time.sleep(0.02)

    def _initialize_all_params(self) -> list[int]:
        cfg = self.config
        range_code = self._input_range_code()
        return [
            int(cfg.sample_rate),
            4,
            int(cfg.bit_mode),
            0,
            range_code,
            range_code,
            range_code,
            range_code,
            0,
            0,
            0,
            0,
        ]

    def _input_range_code(self) -> int:
        range_map = {
            10.0: 0,
            5.0: 1,
            2.5: 2,
            1.0: 3,
            0.5: 4,
            0.1: 5,
            0.02: 6,
            0.001: 7,
        }
        requested = float(self.config.input_range_volts)
        for volts, code in range_map.items():
            if abs(requested - volts) <= 1e-9:
                return code
        supported = ", ".join(str(value).rstrip("0").rstrip(".") for value in range_map)
        raise Vk701nError(f"unsupported input_range_volts={requested}; supported values: {supported}")

    def _get_buffer(self, required: int) -> Any:
        if self._buffer is None or self._buffer_capacity < required:
            self._buffer = (ctypes.c_double * int(required))()
            self._buffer_capacity = int(required)
        return self._buffer

    @staticmethod
    def _check(action: str, status: int, allow_positive: bool = False) -> None:
        failed = status < 0 if allow_positive else status < 0
        if failed:
            raise Vk701nError(f"{action} failed with status {status}")


def resolve_sdk_library(configured_path: str = "") -> Path:
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    if platform.system().lower().startswith("win"):
        return (VENDOR_VK701N_DIR / "VK70xNMC_DAQ2.dll").resolve()
    return (VENDOR_VK701N_DIR / "libVK70XNMC_DAQ_SHARED.so").resolve()
