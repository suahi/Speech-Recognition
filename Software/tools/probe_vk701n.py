from __future__ import annotations

import argparse
import ctypes
import os
import platform
import time
from pathlib import Path
from typing import Any


RANGE_CODES = {
    10.0: 0,
    5.0: 1,
    2.5: 2,
    1.0: 3,
    0.5: 4,
    0.1: 5,
    0.02: 6,
    0.001: 7,
}


def range_code(input_range_volts: float) -> int:
    for volts, code in RANGE_CODES.items():
        if abs(float(input_range_volts) - volts) <= 1e-9:
            return code
    supported = ", ".join(str(value).rstrip("0").rstrip(".") for value in RANGE_CODES)
    raise ValueError(f"unsupported input range {input_range_volts}; supported: {supported}")


def default_library_path() -> Path:
    software_dir = Path(__file__).resolve().parents[1]
    vendor_dir = software_dir / "vendor" / "vk701n"
    if platform.system().lower().startswith("win"):
        return vendor_dir / "VK70xNMC_DAQ2.dll"
    return vendor_dir / "libVK70XNMC_DAQ_SHARED.so"


class VkSdk:
    def __init__(self, library_path: Path) -> None:
        self.library_path = library_path.resolve()
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(self.library_path.parent))
        os.chdir(self.library_path.parent)
        self.dll = ctypes.CDLL(str(self.library_path))
        self._bind()

    def _bind(self) -> None:
        self.dll.Server_TCPOpen.argtypes = [ctypes.c_int]
        self.dll.Server_TCPOpen.restype = ctypes.c_int
        self.dll.Server_TCPClose.argtypes = [ctypes.c_int]
        self.dll.Server_TCPClose.restype = ctypes.c_int
        self.dll.Server_Get_ConnectedClientNumbers.argtypes = [ctypes.POINTER(ctypes.c_int)]
        self.dll.Server_Get_ConnectedClientNumbers.restype = ctypes.c_int
        self.dll.Server_Get_ConnectedClientHandle.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_char),
        ]
        self.dll.Server_Get_ConnectedClientHandle.restype = ctypes.c_int
        self.dll.VK70xNMC_Set_SystemMode.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
        ]
        self.dll.VK70xNMC_Set_SystemMode.restype = ctypes.c_int
        self.dll.VK70xNMC_InitializeAll.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
        ]
        self.dll.VK70xNMC_InitializeAll.restype = ctypes.c_int
        self.dll.VK70xNMC_Set_BlockingMethodtoReadADCResult.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
        ]
        self.dll.VK70xNMC_Set_BlockingMethodtoReadADCResult.restype = ctypes.c_int
        self.dll.VK70xNMC_StartSampling.argtypes = [ctypes.c_int]
        self.dll.VK70xNMC_StartSampling.restype = ctypes.c_int
        self.dll.VK70xNMC_StopSampling.argtypes = [ctypes.c_int]
        self.dll.VK70xNMC_StopSampling.restype = ctypes.c_int
        self.dll.VK70xNMC_GetFourChannel.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_int,
        ]
        self.dll.VK70xNMC_GetFourChannel.restype = ctypes.c_int

    def close(self, port: int, device_no: int) -> None:
        try:
            print(f"StopSampling -> {self.dll.VK70xNMC_StopSampling(int(device_no))}")
        except Exception as exc:
            print(f"StopSampling exception -> {exc}")
        try:
            print(f"Server_TCPClose -> {self.dll.Server_TCPClose(int(port))}")
        except Exception as exc:
            print(f"Server_TCPClose exception -> {exc}")

    def initialize_all(self, device_no: int, params: list[int]) -> int:
        array = (ctypes.c_int * len(params))(*params)
        return int(self.dll.VK70xNMC_InitializeAll(int(device_no), array, len(params)))

    def get_four_channel(self, device_no: int, buffer: Any, read_points: int) -> int:
        return int(self.dll.VK70xNMC_GetFourChannel(int(device_no), buffer, int(read_points)))


def corrected_params(sample_rate: int, bit_mode: int, input_range_volts: float) -> list[int]:
    code = range_code(input_range_volts)
    return [int(sample_rate), 4, int(bit_mode), 0, code, code, code, code, 0, 0, 0, 0]


def current_bug_params(sample_rate: int, bit_mode: int, input_range_volts: float) -> list[int]:
    code = range_code(input_range_volts)
    return [
        int(sample_rate),
        4,
        int(bit_mode),
        int(sample_rate),
        code,
        code,
        code,
        code,
        1,
        1,
        1,
        1,
    ]


def wait_for_device(sdk: VkSdk, device_no: int, timeout_s: float) -> None:
    deadline = time.monotonic() + float(timeout_s)
    last_status = -1
    last_count = 0
    while True:
        count = ctypes.c_int(0)
        status = int(sdk.dll.Server_Get_ConnectedClientNumbers(ctypes.byref(count)))
        last_status = status
        last_count = int(count.value)
        if status >= 0 and count.value > int(device_no):
            print(f"Server_Get_ConnectedClientNumbers -> status={status}, count={count.value}")
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(f"DAQ connection timed out: status={last_status}, count={last_count}")
        time.sleep(0.02)


def summarize_ch1(buffer: Any, recv_len: int) -> str:
    if recv_len <= 0:
        return "no_data"
    values = [float(buffer[index * 4]) for index in range(min(int(recv_len), 2000))]
    mean = sum(values) / len(values)
    rms = (sum(value * value for value in values) / len(values)) ** 0.5
    return (
        f"ch1_min={min(values):.8f}, ch1_max={max(values):.8f}, "
        f"ch1_mean={mean:.8f}, ch1_rms={rms:.8f}"
    )


def run_probe(args: argparse.Namespace) -> None:
    library_path = Path(args.library) if args.library else default_library_path()
    if not library_path.exists():
        raise FileNotFoundError(library_path)
    sdk = VkSdk(library_path)
    params = (
        current_bug_params(args.sample_rate, args.bit_mode, args.input_range_volts)
        if args.mode == "current-bug"
        else corrected_params(args.sample_rate, args.bit_mode, args.input_range_volts)
    )

    print(f"library={library_path}")
    print(f"mode={args.mode}")
    print(f"initialize_all_params={params}")
    sdk.close(args.port, args.device_no)
    time.sleep(0.5)
    try:
        status = int(sdk.dll.Server_TCPOpen(int(args.port)))
        print(f"Server_TCPOpen({args.port}) -> {status}")
        if status < 0:
            raise RuntimeError(f"Server_TCPOpen failed: {status}")
        wait_for_device(sdk, args.device_no, args.connect_timeout_s)

        handle = ctypes.c_int(0)
        ip = ctypes.create_string_buffer(128)
        status = int(
            sdk.dll.Server_Get_ConnectedClientHandle(
                int(args.device_no),
                ctypes.byref(handle),
                ip,
            )
        )
        print(
            "Server_Get_ConnectedClientHandle -> "
            f"status={status}, handle={handle.value}, ip={ip.value.decode(errors='replace')}"
        )
        if status < 0:
            raise RuntimeError(f"Server_Get_ConnectedClientHandle failed: {status}")

        print(f"Set_SystemMode -> {sdk.dll.VK70xNMC_Set_SystemMode(int(args.device_no), 0, 0, 0)}")
        print(f"InitializeAll -> {sdk.initialize_all(args.device_no, params)}")
        print(
            "Set_Blocking -> "
            f"{sdk.dll.VK70xNMC_Set_BlockingMethodtoReadADCResult(1, int(args.blocking_timeout_ms))}"
        )
        print(f"StartSampling -> {sdk.dll.VK70xNMC_StartSampling(int(args.device_no))}")

        buffer = (ctypes.c_double * (int(args.read_points) * 4))()
        total = 0
        zeros = 0
        last: list[int] = []
        for loop_index in range(1, int(args.loops) + 1):
            started_at = time.monotonic()
            recv_len = sdk.get_four_channel(args.device_no, buffer, args.read_points)
            elapsed = time.monotonic() - started_at
            last.append(recv_len)
            if recv_len > 0:
                total += recv_len
            elif recv_len == 0:
                zeros += 1
            print(
                f"loop={loop_index:02d}, recvLen={recv_len}, call_dt={elapsed:.3f}s, "
                f"total={total}, zeros={zeros}, {summarize_ch1(buffer, recv_len)}"
            )
        print(f"last_recv_lengths={last}")
    finally:
        sdk.close(args.port, args.device_no)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe VK701N-SD continuous ADC reads.")
    parser.add_argument("--library", default="", help="Path to VK70xNMC_DAQ2.dll or libVK70XNMC_DAQ_SHARED.so.")
    parser.add_argument("--mode", choices=["fixed", "current-bug"], default="fixed")
    parser.add_argument("--port", type=int, default=8234)
    parser.add_argument("--device-no", type=int, default=0)
    parser.add_argument("--sample-rate", type=int, default=50000)
    parser.add_argument("--bit-mode", type=int, default=24)
    parser.add_argument("--input-range-volts", type=float, default=5.0)
    parser.add_argument("--read-points", type=int, default=5000)
    parser.add_argument("--blocking-timeout-ms", type=int, default=1000)
    parser.add_argument("--connect-timeout-s", type=float, default=10.0)
    parser.add_argument("--loops", type=int, default=12)
    return parser.parse_args()


if __name__ == "__main__":
    run_probe(parse_args())
