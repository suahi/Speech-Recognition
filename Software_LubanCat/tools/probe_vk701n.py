from __future__ import annotations

import argparse
import ctypes
from contextlib import contextmanager
import os
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

PROFILES = ("fixed_initialize_all", "legacy_initialize_all", "windows_initialize")


def range_code(input_range_volts: float) -> int:
    for volts, code in RANGE_CODES.items():
        if abs(float(input_range_volts) - volts) <= 1e-9:
            return code
    supported = ", ".join(str(value).rstrip("0").rstrip(".") for value in RANGE_CODES)
    raise ValueError(f"unsupported input range {input_range_volts}; supported: {supported}")


def default_library_path() -> Path:
    software_dir = Path(__file__).resolve().parents[1]
    vendor_dir = software_dir / "vendor" / "vk701n"
    return vendor_dir / "libVK70XNMC_DAQ_SHARED.so"


def resolve_library_path(configured: str) -> Path:
    if not configured:
        return default_library_path()
    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    return path.resolve()


class VkSdk:
    def __init__(self, library_path: Path) -> None:
        self.library_path = library_path.resolve()
        self.library_dir = self.library_path.parent
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(self.library_dir))
        with self.working_directory():
            self.dll = ctypes.CDLL(str(self.library_path))
            self._bind()

    @contextmanager
    def working_directory(self):
        previous = Path.cwd()
        os.chdir(self.library_dir)
        try:
            yield
        finally:
            os.chdir(previous)

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
        self.has_initialize = hasattr(self.dll, "VK70xNMC_Initialize")
        if self.has_initialize:
            self.dll.VK70xNMC_Initialize.argtypes = [
                ctypes.c_int,
                ctypes.c_double,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
            ]
            self.dll.VK70xNMC_Initialize.restype = ctypes.c_int
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
        with self.working_directory():
            try:
                print(f"StopSampling -> {self.dll.VK70xNMC_StopSampling(int(device_no))}")
            except Exception as exc:
                print(f"StopSampling exception -> {exc}")
            try:
                print(f"Server_TCPClose -> {self.dll.Server_TCPClose(int(port))}")
            except Exception as exc:
                print(f"Server_TCPClose exception -> {exc}")

    def open_server(self, port: int) -> int:
        with self.working_directory():
            return int(self.dll.Server_TCPOpen(int(port)))

    def connected_client_numbers(self) -> tuple[int, int]:
        count = ctypes.c_int(0)
        with self.working_directory():
            status = int(self.dll.Server_Get_ConnectedClientNumbers(ctypes.byref(count)))
        return status, int(count.value)

    def connected_client_handle(self, device_no: int) -> tuple[int, int, str]:
        handle = ctypes.c_int(0)
        ip = ctypes.create_string_buffer(128)
        with self.working_directory():
            status = int(
                self.dll.Server_Get_ConnectedClientHandle(
                    int(device_no),
                    ctypes.byref(handle),
                    ip,
                )
            )
        return status, int(handle.value), ip.value.decode(errors="replace")

    def set_system_mode(self, device_no: int) -> int:
        with self.working_directory():
            return int(self.dll.VK70xNMC_Set_SystemMode(int(device_no), 0, 0, 0))

    def initialize_all(self, device_no: int, params: list[int]) -> int:
        array = (ctypes.c_int * len(params))(*params)
        with self.working_directory():
            return int(self.dll.VK70xNMC_InitializeAll(int(device_no), array, len(params)))

    def initialize(
        self,
        device_no: int,
        ref_voltage: float,
        bit_mode: int,
        sample_rate: int,
        code: int,
    ) -> int:
        if not self.has_initialize:
            raise RuntimeError("VK70xNMC_Initialize is not exported by this SDK")
        with self.working_directory():
            return int(
                self.dll.VK70xNMC_Initialize(
                    int(device_no),
                    float(ref_voltage),
                    int(bit_mode),
                    int(sample_rate),
                    int(code),
                    int(code),
                    int(code),
                    int(code),
                )
            )

    def set_blocking(self, timeout_ms: int) -> int:
        with self.working_directory():
            return int(self.dll.VK70xNMC_Set_BlockingMethodtoReadADCResult(1, int(timeout_ms)))

    def start_sampling(self, device_no: int) -> int:
        with self.working_directory():
            return int(self.dll.VK70xNMC_StartSampling(int(device_no)))

    def get_four_channel(self, device_no: int, buffer: Any, read_points: int) -> int:
        with self.working_directory():
            return int(self.dll.VK70xNMC_GetFourChannel(int(device_no), buffer, int(read_points)))


def fixed_initialize_all_params(sample_rate: int, bit_mode: int, input_range_volts: float) -> list[int]:
    code = range_code(input_range_volts)
    return [int(sample_rate), 4, int(bit_mode), 0, code, code, code, code, 0, 0, 0, 0]


def legacy_initialize_all_params(sample_rate: int, bit_mode: int) -> list[int]:
    return [int(sample_rate), 4, int(bit_mode), int(sample_rate), 1, 1, 1, 1, 1, 1, 1, 1]


def wait_for_device(sdk: VkSdk, device_no: int, timeout_s: float) -> None:
    deadline = time.monotonic() + float(timeout_s)
    last_status = -1
    last_count = 0
    while True:
        status, count = sdk.connected_client_numbers()
        last_status = int(status)
        last_count = int(count)
        if status >= 0 and count > int(device_no):
            print(f"Server_Get_ConnectedClientNumbers -> status={status}, count={count}")
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(f"DAQ connection timed out: status={last_status}, count={last_count}")
        time.sleep(0.02)


def summarize_channels(buffer: Any, recv_len: int) -> str:
    if recv_len <= 0:
        return "no_data"
    limit = min(int(recv_len), 2000)
    parts = []
    for channel in range(4):
        values = [float(buffer[index * 4 + channel]) for index in range(limit)]
        mean = sum(values) / len(values)
        rms = (sum(value * value for value in values) / len(values)) ** 0.5
        parts.append(
            f"CH{channel + 1}: min={min(values):.8f}, max={max(values):.8f}, "
            f"mean={mean:.8f}, rms={rms:.8f}"
        )
    return "; ".join(parts)


def initialize_profile(sdk: VkSdk, args: argparse.Namespace, profile: str) -> None:
    if profile == "fixed_initialize_all":
        params = fixed_initialize_all_params(args.sample_rate, args.bit_mode, args.input_range_volts)
        print(f"InitializeAll fixed params={params}")
        print(f"InitializeAll -> {sdk.initialize_all(args.device_no, params)}")
        return
    if profile == "legacy_initialize_all":
        params = legacy_initialize_all_params(args.sample_rate, args.bit_mode)
        print(f"InitializeAll legacy params={params}")
        print(f"InitializeAll -> {sdk.initialize_all(args.device_no, params)}")
        return
    if profile == "windows_initialize":
        print(
            "Initialize windows params="
            f"device_no={args.device_no}, ref_voltage=4.0, bit=1, "
            f"sample_rate={args.sample_rate}, range_code=0"
        )
        print(f"Initialize -> {sdk.initialize(args.device_no, 4.0, 1, args.sample_rate, 0)}")
        return
    raise ValueError(f"unsupported profile: {profile}")


def read_probe_loop(
    sdk: VkSdk,
    args: argparse.Namespace,
    buffer: Any,
    loop_count: int,
    label: str,
) -> tuple[list[int], bool]:
    threshold = max(1, int(args.read_points * float(args.health_check_min_fraction)))
    required_successes = max(1, int(args.health_check_min_successes))
    consecutive_successes = 0
    passed = False
    lengths: list[int] = []
    total = 0
    zeros = 0
    for loop_index in range(1, int(loop_count) + 1):
        started_at = time.monotonic()
        recv_len = sdk.get_four_channel(args.device_no, buffer, args.read_points)
        elapsed = time.monotonic() - started_at
        lengths.append(int(recv_len))
        if recv_len > 0:
            total += int(recv_len)
        elif recv_len == 0:
            zeros += 1
        if recv_len >= threshold:
            consecutive_successes += 1
            if consecutive_successes >= required_successes:
                passed = True
        else:
            consecutive_successes = 0
        print(
            f"{label} loop={loop_index:02d}, recvLen={recv_len}, call_dt={elapsed:.3f}s, "
            f"total={total}, zeros={zeros}, {summarize_channels(buffer, recv_len)}"
        )
    return lengths, passed


def run_profile(sdk: VkSdk, args: argparse.Namespace, profile: str) -> None:
    print("")
    print(f"=== profile={profile} ===")
    sdk.close(args.port, args.device_no)
    time.sleep(float(args.cleanup_delay_s))
    try:
        status = sdk.open_server(args.port)
        print(f"Server_TCPOpen({args.port}) -> {status}")
        if status < 0:
            raise RuntimeError(f"Server_TCPOpen failed: {status}")
        wait_for_device(sdk, args.device_no, args.connect_timeout_s)

        status, handle, ip = sdk.connected_client_handle(args.device_no)
        print(f"Server_Get_ConnectedClientHandle -> status={status}, handle={handle}, ip={ip}")
        if status < 0:
            raise RuntimeError(f"Server_Get_ConnectedClientHandle failed: {status}")

        print(f"Set_SystemMode -> {sdk.set_system_mode(args.device_no)}")
        initialize_profile(sdk, args, profile)
        print(f"Set_Blocking -> {sdk.set_blocking(args.blocking_timeout_ms)}")
        if args.post_initialize_delay_s > 0:
            print(f"Post initialize delay -> {args.post_initialize_delay_s}s")
            time.sleep(float(args.post_initialize_delay_s))
        print(f"StartSampling -> {sdk.start_sampling(args.device_no)}")
        if args.post_start_delay_s > 0:
            print(f"Post start delay -> {args.post_start_delay_s}s")
            time.sleep(float(args.post_start_delay_s))

        buffer = (ctypes.c_double * (int(args.read_points) * 4))()
        health_lengths, health_passed = read_probe_loop(
            sdk,
            args,
            buffer,
            args.health_check_loops,
            "health",
        )
        threshold = max(1, int(args.read_points * float(args.health_check_min_fraction)))
        print(
            f"health_result passed={health_passed}, threshold={threshold}, "
            f"required_consecutive_successes={args.health_check_min_successes}, "
            f"recv_lengths={health_lengths}"
        )
        if health_passed and args.loops > 0:
            loop_lengths, _ = read_probe_loop(sdk, args, buffer, args.loops, "read")
            print(f"read_recv_lengths={loop_lengths}")
    except Exception as exc:
        print(f"profile_error={type(exc).__name__}: {exc}")
    finally:
        sdk.close(args.port, args.device_no)


def selected_profiles(profile: str) -> list[str]:
    if profile == "all":
        return list(PROFILES)
    if profile == "fixed":
        return ["fixed_initialize_all"]
    if profile == "legacy":
        return ["legacy_initialize_all"]
    if profile == "windows":
        return ["windows_initialize"]
    return [profile]


def run_probe(args: argparse.Namespace) -> None:
    library_path = resolve_library_path(args.library)
    if not library_path.exists():
        raise FileNotFoundError(library_path)
    sdk = VkSdk(library_path)
    print(f"library={library_path}")
    print(f"has_windows_initialize={sdk.has_initialize}")
    print(f"profiles={selected_profiles(args.profile)}")
    for profile in selected_profiles(args.profile):
        run_profile(sdk, args, profile)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe VK701N-SD startup profiles and continuous ADC reads.")
    parser.add_argument("--library", default="", help="Path to libVK70XNMC_DAQ_SHARED.so.")
    parser.add_argument(
        "--profile",
        choices=["fixed", "legacy", "windows", "all", *PROFILES],
        default="legacy",
        help="Startup profile to probe.",
    )
    parser.add_argument("--port", type=int, default=8234)
    parser.add_argument("--device-no", type=int, default=0)
    parser.add_argument("--sample-rate", type=int, default=50000)
    parser.add_argument("--bit-mode", type=int, default=24)
    parser.add_argument("--input-range-volts", type=float, default=5.0)
    parser.add_argument("--read-points", type=int, default=5000)
    parser.add_argument("--blocking-timeout-ms", type=int, default=1000)
    parser.add_argument("--connect-timeout-s", type=float, default=10.0)
    parser.add_argument("--cleanup-delay-s", type=float, default=0.5)
    parser.add_argument("--post-initialize-delay-s", type=float, default=1.0)
    parser.add_argument("--post-start-delay-s", type=float, default=0.1)
    parser.add_argument("--health-check-loops", type=int, default=8)
    parser.add_argument("--health-check-min-fraction", type=float, default=0.5)
    parser.add_argument("--health-check-min-successes", type=int, default=2)
    parser.add_argument("--loops", type=int, default=12, help="Extra read loops after health check passes.")
    return parser.parse_args()


if __name__ == "__main__":
    run_probe(parse_args())
