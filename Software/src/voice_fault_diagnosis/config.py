from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from voice_fault_diagnosis.capture.vk701n import INPUT_RANGE_CODES, resolve_sdk_library
from voice_fault_diagnosis.models import HardwareConfig
from voice_fault_diagnosis.paths import PC_CONFIG_PATH, SOFTWARE_ROOT
from voice_fault_diagnosis.runtime_checks import PeFormatError, require_x64_windows_dll


EXPECTED_LABEL_CODES = ("C0", "C1", "C2", "C3", "C4", "C5")


class PcConfigError(ValueError):
    """Raised when the Windows PC application configuration is invalid."""


@dataclass(frozen=True)
class WavModelConfig:
    model_path: Path
    mean_std_path: Path
    source_revision: str
    labels: dict[str, str]


@dataclass(frozen=True)
class PcAppConfig:
    hardware: HardwareConfig
    capture_duration_seconds: float
    model: WavModelConfig
    source_path: Path


def load_pc_config(path: str | Path = PC_CONFIG_PATH) -> PcAppConfig:
    source_path = Path(path).resolve()
    if not source_path.is_file():
        raise PcConfigError(f"找不到电脑端配置文件：{source_path}")
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PcConfigError(f"电脑端配置不是有效 JSON：{source_path}") from exc
    if not isinstance(data, dict):
        raise PcConfigError("电脑端配置根节点必须是对象。")

    hardware_data = _required_object(data, "hardware")
    capture_data = _required_object(data, "capture")
    model_data = _required_object(data, "model")
    hardware = HardwareConfig.from_dict(hardware_data)
    duration = _positive_number(capture_data.get("duration_seconds"), "capture.duration_seconds")
    hardware.capture_seconds = duration
    _validate_hardware(hardware)

    sdk_path = resolve_sdk_library(hardware.sdk_library_path)
    _require_project_file(sdk_path, "hardware.sdk_library_path")
    if sdk_path.suffix.lower() != ".dll":
        raise PcConfigError(f"hardware.sdk_library_path 必须指向 Windows DLL：{sdk_path}")
    try:
        require_x64_windows_dll(sdk_path)
    except PeFormatError as exc:
        raise PcConfigError(str(exc)) from exc
    hardware.sdk_library_path = str(sdk_path)

    labels_data = _required_object(model_data, "labels")
    if set(labels_data) != set(EXPECTED_LABEL_CODES):
        raise PcConfigError("model.labels 必须完整配置 C0、C1、C2、C3、C4、C5。")
    labels = {code: str(labels_data[code]).strip() for code in EXPECTED_LABEL_CODES}
    if any(not name for name in labels.values()):
        raise PcConfigError("model.labels 中的中文名称不能为空。")

    model_path = _project_path(model_data.get("model_path"), "model.model_path")
    mean_std_path = _project_path(model_data.get("mean_std_path"), "model.mean_std_path")
    missing = [str(item) for item in (model_path, mean_std_path) if not item.is_file()]
    if missing:
        raise PcConfigError("缺少 WAV 模型文件：" + "，".join(missing))
    source_revision = str(model_data.get("source_revision", "")).strip()
    if not source_revision:
        raise PcConfigError("model.source_revision 不能为空。")

    return PcAppConfig(
        hardware=hardware,
        capture_duration_seconds=duration,
        model=WavModelConfig(
            model_path=model_path,
            mean_std_path=mean_std_path,
            source_revision=source_revision,
            labels=labels,
        ),
        source_path=source_path,
    )


def _required_object(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise PcConfigError(f"{key} 必须是对象。")
    return value


def _positive_number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise PcConfigError(f"{name} 必须是正数。") from exc
    if number <= 0:
        raise PcConfigError(f"{name} 必须大于 0。")
    return number


def _project_path(value: Any, name: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise PcConfigError(f"{name} 必须是项目内的文件路径。")
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (SOFTWARE_ROOT / candidate).resolve()
    _require_project_file(resolved, name)
    return resolved


def _require_project_file(path: Path, name: str) -> None:
    try:
        path.relative_to(SOFTWARE_ROOT)
    except ValueError as exc:
        raise PcConfigError(f"{name} 必须位于电脑端项目目录内。") from exc
    if not path.is_file():
        raise PcConfigError(f"{name} 指向的文件不存在：{path}")


def _validate_hardware(hardware: HardwareConfig) -> None:
    if not 1 <= int(hardware.server_port) <= 65535:
        raise PcConfigError("hardware.server_port 必须在 1 到 65535 之间。")
    if int(hardware.device_no) < 0:
        raise PcConfigError("hardware.device_no 不能为负数。")
    if int(hardware.adc_total_channels) != 4:
        raise PcConfigError("当前 VK701N-SD 采集仅支持 hardware.adc_total_channels=4。")
    if not 1 <= int(hardware.adc_channel) <= int(hardware.adc_total_channels):
        raise PcConfigError("hardware.adc_channel 必须位于 1 到 adc_total_channels 之间。")
    if int(hardware.sample_rate) <= 0 or int(hardware.read_frame_count) <= 0:
        raise PcConfigError("hardware.sample_rate 和 hardware.read_frame_count 必须大于 0。")
    if int(hardware.bit_mode) != 24:
        raise PcConfigError("当前演示配置要求 hardware.bit_mode=24。")
    if str(hardware.initialize_all_profile).strip().lower() != "windows_c_example":
        raise PcConfigError("电脑直连模式要求 hardware.initialize_all_profile=windows_c_example。")
    if float(hardware.input_range_volts) not in INPUT_RANGE_CODES:
        supported = "、".join(str(value) for value in INPUT_RANGE_CODES)
        raise PcConfigError(f"hardware.input_range_volts 必须是：{supported}。")
