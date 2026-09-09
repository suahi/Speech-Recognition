from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HardwareConfig:
    """VK701N-SD parameters loaded from the PC direct-connect config."""

    sdk_library_path: str = ""
    server_port: int = 8234
    device_no: int = 0
    adc_channel: int = 2
    adc_total_channels: int = 4
    sample_rate: int = 50000
    bit_mode: int = 24
    read_frame_count: int = 5000
    gain: float = 0.668
    blocking_timeout_ms: int = 1000
    connect_timeout_s: float = 10.0
    zero_read_timeout_s: float = 30.0
    poll_interval_s: float = 0.01
    preflight_cleanup: bool = False
    preflight_cleanup_delay_s: float = 0.5
    initialize_all_profile: str = "windows_c_example"
    post_initialize_delay_s: float = 1.0
    post_start_delay_s: float = 0.1
    input_range_volts: float = 5.0
    capture_seconds: float = 10.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HardwareConfig":
        fields = cls.__dataclass_fields__
        return cls(**{key: data[key] for key in fields if key in data})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CaptureResult:
    raw_voltage: Any
    sample_rate: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiChannelCaptureResult:
    raw_voltage: Any
    sample_rate: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    model_name: str
    class_index: int
    label: str
    confidence: float
    probabilities: list[float]
    top_k: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def path_to_str(path: str | Path) -> str:
    return str(Path(path))
