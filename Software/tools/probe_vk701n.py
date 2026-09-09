from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np


SOFTWARE_ROOT = Path(__file__).resolve().parents[1]
SRC = SOFTWARE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voice_fault_diagnosis.capture.vk701n import Vk701nCaptureSession
from voice_fault_diagnosis.config import load_pc_config


def run_probe(duration_seconds: float) -> None:
    config = load_pc_config()
    session = Vk701nCaptureSession(config.hardware)
    result = session.capture_all_channels(duration_seconds)
    values = np.asarray(result.raw_voltage, dtype=np.float32)
    print(f"采集卡：{result.metadata.get('daq_ip', '未知')}")
    print(f"采样：{values.shape[0]} 帧，{result.sample_rate} Hz，TCP {config.hardware.server_port}")
    for index in range(values.shape[1]):
        channel = values[:, index]
        rms = float(np.sqrt(np.mean(channel.astype(np.float64) ** 2)))
        print(
            f"CH{index + 1}: min={float(np.min(channel)):.8f} V, "
            f"max={float(np.max(channel)):.8f} V, rms={rms:.8f} V"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="使用 pc_direct.json 探测 VK701N-SD 四通道输入。")
    parser.add_argument("--duration", type=float, default=1.0, help="探测时长（秒），默认 1 秒。")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.duration <= 0:
        raise SystemExit("--duration 必须大于 0。")
    run_probe(arguments.duration)
