from __future__ import annotations

import argparse
from pathlib import Path
import sys

from voice_fault_diagnosis.capture.vk701n import Vk701nCaptureSession
from voice_fault_diagnosis.config import load_json
from voice_fault_diagnosis.diagnostics.sound_capture import save_capture_check
from voice_fault_diagnosis.models import HardwareConfig, MultiChannelCaptureResult
from voice_fault_diagnosis.paths import CAPTURE_CHECKS_DIR, CONFIG_DIR


def capture_stage(
    hardware: HardwareConfig,
    duration_seconds: float,
    stage_label: str,
) -> MultiChannelCaptureResult:
    session = Vk701nCaptureSession(hardware)
    last_percent = -1

    def on_chunk(_voltage, info: dict[str, object]) -> None:
        nonlocal last_percent
        received = int(info.get("received_samples") or 0)
        target = max(1, int(info.get("target_samples") or 1))
        percent = min(100, int(received / target * 100))
        if percent >= last_percent + 10 or percent == 100:
            print(f"{stage_label}: {percent}% ({received}/{target})")
            last_percent = percent

    return session.capture_all_channels(duration_seconds, on_chunk=on_chunk)


def run(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser()
    hardware = HardwareConfig.from_dict(load_json(config_path, {}))
    duration = float(args.duration)
    if duration <= 0:
        raise ValueError("--duration must be positive")

    print("鲁班猫声音采集链路自检")
    print(
        f"采样率={hardware.sample_rate} Hz, 量程={hardware.input_range_volts:g} V, "
        f"当前通道=CH{hardware.adc_channel}, 每阶段={duration:g} s"
    )
    print("请先关闭其他厂家采集软件，保持 VK701N 仅连接鲁班猫。")
    input("\n第 1 步：现场保持安静，准备好后按回车开始采集 4 个通道...")
    quiet = capture_stage(hardware, duration, "安静基线")

    input(
        "\n第 2 步：准备持续制造可重复的机械噪声。"
        "按回车后立即开始，并在整个采集阶段持续制造噪声..."
    )
    noise = capture_stage(hardware, duration, "机械噪声")

    if quiet.sample_rate != noise.sample_rate:
        raise RuntimeError("quiet and noise sample rates do not match")
    output_root = Path(args.output_root).expanduser()
    result = save_capture_check(
        quiet.raw_voltage,
        noise.raw_voltage,
        hardware,
        quiet_metadata=quiet.metadata,
        noise_metadata=noise.metadata,
        output_root=output_root,
        progress_callback=lambda percent, message: print(f"报告 {percent:3d}%: {message}"),
    )

    print("\n" + (result.output_dir / "summary.txt").read_text(encoding="utf-8"))
    print(f"完整报告目录: {result.output_dir}")
    print("请把推荐通道 noise_chN_monitor.wav 复制到电脑试听。")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 VK701N 四通道是否采集到真实声音响应。")
    parser.add_argument(
        "--config",
        default=str(CONFIG_DIR / "hardware_vk701n.json"),
        help="硬件配置 JSON 路径。",
    )
    parser.add_argument("--duration", type=float, default=5.0, help="每个阶段的采集秒数。")
    parser.add_argument(
        "--output-root",
        default=str(CAPTURE_CHECKS_DIR),
        help="自检报告根目录。",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        raise SystemExit(run(parse_args()))
    except KeyboardInterrupt:
        print("\n用户取消自检。", file=sys.stderr)
        raise SystemExit(130) from None
    except Exception as exc:
        print(f"自检失败: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
