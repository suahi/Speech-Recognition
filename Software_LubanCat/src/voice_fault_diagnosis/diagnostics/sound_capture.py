from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import math
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy import signal

from voice_fault_diagnosis.audio_io import save_wav, voltage_to_audio
from voice_fault_diagnosis.capture.vk701n import SUPPORTED_INPUT_RANGES
from voice_fault_diagnosis.config import save_json
from voice_fault_diagnosis.models import HardwareConfig
from voice_fault_diagnosis.paths import CAPTURE_CHECKS_DIR


AUDIBLE_LOW_HZ = 20.0
AUDIBLE_HIGH_HZ = 20_000.0
LIKELY_INCREASE_DB = 6.0
STRONG_INCREASE_DB = 10.0
CLIPPING_RATIO_LIMIT = 0.001
CLIPPING_LEVEL_RATIO = 0.99
MONITOR_TARGET_RMS_DBFS = -20.0
MONITOR_PEAK_LIMIT_DBFS = -1.0
MONITOR_MAX_GAIN_DB = 40.0
MONITOR_HIGHPASS_HZ = 20.0

ProgressCallback = Callable[[int, str], None]


@dataclass
class ChannelMetrics:
    channel: int
    sample_count: int
    finite: bool
    nonfinite_count: int
    dc_mean_volts: float
    ac_rms_volts: float
    peak_to_peak_volts: float
    peak_abs_volts: float
    ac_rms_dbfs: float
    peak_full_scale_percent: float
    clipping_ratio: float
    audible_band_rms_volts: float
    audible_band_power: float
    dominant_frequency_hz: float


@dataclass
class ChannelComparison:
    channel: int
    status: str
    message: str
    ac_rms_increase_db: float
    band_power_increase_db: float
    quiet: ChannelMetrics
    noise: ChannelMetrics


@dataclass
class CaptureCheckReport:
    created_at: str
    sample_rate: int
    input_range_volts: float
    selected_channel: int
    recommended_channel: int
    recommended_input_range_volts: float
    overall_status: str
    overall_message: str
    channels: list[ChannelComparison]
    hardware_config: dict[str, Any]
    stage_metadata: dict[str, Any] = field(default_factory=dict)
    audio_files: list[dict[str, Any]] = field(default_factory=list)
    output_dir: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CaptureCheckResult:
    report: CaptureCheckReport
    output_dir: Path


def calculate_channel_metrics(
    voltage: np.ndarray,
    sample_rate: int,
    input_range_volts: float,
    channel: int,
) -> ChannelMetrics:
    arr = np.asarray(voltage, dtype=np.float64).reshape(-1)
    if int(sample_rate) <= 0:
        raise ValueError("sample_rate must be positive")
    if float(input_range_volts) <= 0:
        raise ValueError("input_range_volts must be positive")

    finite_mask = np.isfinite(arr)
    nonfinite_count = int(arr.size - np.count_nonzero(finite_mask))
    finite = bool(arr.size > 0 and nonfinite_count == 0)
    values = arr[finite_mask]
    if values.size == 0:
        return ChannelMetrics(
            channel=int(channel),
            sample_count=int(arr.size),
            finite=False,
            nonfinite_count=nonfinite_count,
            dc_mean_volts=0.0,
            ac_rms_volts=0.0,
            peak_to_peak_volts=0.0,
            peak_abs_volts=0.0,
            ac_rms_dbfs=-300.0,
            peak_full_scale_percent=0.0,
            clipping_ratio=0.0,
            audible_band_rms_volts=0.0,
            audible_band_power=0.0,
            dominant_frequency_hz=0.0,
        )

    dc_mean = float(np.mean(values))
    ac = values - dc_mean
    ac_rms = float(np.sqrt(np.mean(np.square(ac))))
    peak_abs = float(np.max(np.abs(values)))
    peak_to_peak = float(np.ptp(values))
    full_scale = float(input_range_volts)
    clipping_ratio = float(np.mean(np.abs(values) >= full_scale * CLIPPING_LEVEL_RATIO))
    ac_rms_dbfs = _amplitude_dbfs(ac_rms, full_scale)
    band_power, dominant_frequency = _audible_band_power(ac, int(sample_rate))

    return ChannelMetrics(
        channel=int(channel),
        sample_count=int(arr.size),
        finite=finite,
        nonfinite_count=nonfinite_count,
        dc_mean_volts=dc_mean,
        ac_rms_volts=ac_rms,
        peak_to_peak_volts=peak_to_peak,
        peak_abs_volts=peak_abs,
        ac_rms_dbfs=ac_rms_dbfs,
        peak_full_scale_percent=peak_abs / full_scale * 100.0,
        clipping_ratio=clipping_ratio,
        audible_band_rms_volts=float(math.sqrt(max(0.0, band_power))),
        audible_band_power=float(band_power),
        dominant_frequency_hz=float(dominant_frequency),
    )


def analyze_capture_pair(
    quiet_voltage: np.ndarray,
    noise_voltage: np.ndarray,
    sample_rate: int,
    input_range_volts: float,
    selected_channel: int,
    hardware_config: dict[str, Any] | None = None,
    stage_metadata: dict[str, Any] | None = None,
) -> CaptureCheckReport:
    quiet = _validate_multichannel(quiet_voltage, "quiet_voltage")
    noise = _validate_multichannel(noise_voltage, "noise_voltage")
    if quiet.shape[1] != noise.shape[1]:
        raise ValueError("quiet and noise channel counts must match")
    if not 1 <= int(selected_channel) <= quiet.shape[1]:
        raise ValueError("selected_channel is outside the captured channel range")

    comparisons: list[ChannelComparison] = []
    for index in range(quiet.shape[1]):
        channel = index + 1
        quiet_metrics = calculate_channel_metrics(
            quiet[:, index], sample_rate, input_range_volts, channel
        )
        noise_metrics = calculate_channel_metrics(
            noise[:, index], sample_rate, input_range_volts, channel
        )
        comparisons.append(_compare_channel(quiet_metrics, noise_metrics, input_range_volts))

    recommended = _select_recommended_channel(comparisons, int(selected_channel))
    recommended_range = suggest_input_range(
        recommended.noise.peak_abs_volts,
        current_range_volts=float(input_range_volts),
    )
    overall_status, overall_message = _overall_result(comparisons, recommended.channel)
    return CaptureCheckReport(
        created_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        sample_rate=int(sample_rate),
        input_range_volts=float(input_range_volts),
        selected_channel=int(selected_channel),
        recommended_channel=int(recommended.channel),
        recommended_input_range_volts=float(recommended_range),
        overall_status=overall_status,
        overall_message=overall_message,
        channels=comparisons,
        hardware_config=dict(hardware_config or {}),
        stage_metadata=dict(stage_metadata or {}),
    )


def suggest_input_range(peak_abs_volts: float, current_range_volts: float) -> float:
    peak = float(peak_abs_volts)
    current = float(current_range_volts)
    if not math.isfinite(peak) or peak <= 0:
        return current
    required_range = peak / 0.8
    for candidate in sorted(SUPPORTED_INPUT_RANGES):
        if candidate >= required_range:
            return float(candidate)
    return float(max(SUPPORTED_INPUT_RANGES))


def create_monitor_audio(
    voltage: np.ndarray,
    sample_rate: int,
    input_range_volts: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    values = np.asarray(voltage, dtype=np.float32).reshape(-1)
    normalized = voltage_to_audio(values, input_range_volts)
    normalized = np.nan_to_num(normalized, nan=0.0, posinf=0.0, neginf=0.0)
    dc = float(np.mean(normalized)) if normalized.size else 0.0
    centered = normalized.astype(np.float64) - dc
    filtered, highpass_applied = _highpass(centered, int(sample_rate))

    input_rms = _ac_rms(filtered)
    input_peak = float(np.max(np.abs(filtered))) if filtered.size else 0.0
    target_rms = 10.0 ** (MONITOR_TARGET_RMS_DBFS / 20.0)
    peak_limit = 10.0 ** (MONITOR_PEAK_LIMIT_DBFS / 20.0)
    max_gain = 10.0 ** (MONITOR_MAX_GAIN_DB / 20.0)
    if input_rms <= np.finfo(np.float64).eps or input_peak <= np.finfo(np.float64).eps:
        gain = 1.0
        monitor = np.zeros(values.size, dtype=np.float32)
    else:
        gain = min(max_gain, target_rms / input_rms, peak_limit / input_peak)
        monitor = np.clip(filtered * gain, -peak_limit, peak_limit).astype(np.float32)

    output_rms = _ac_rms(monitor)
    output_peak = float(np.max(np.abs(monitor))) if monitor.size else 0.0
    metadata = {
        "dc_removed_normalized": dc,
        "dc_removed_volts": dc * float(input_range_volts),
        "highpass_applied": bool(highpass_applied),
        "highpass_hz": MONITOR_HIGHPASS_HZ if highpass_applied else 0.0,
        "target_rms_dbfs": MONITOR_TARGET_RMS_DBFS,
        "peak_limit_dbfs": MONITOR_PEAK_LIMIT_DBFS,
        "max_gain_db": MONITOR_MAX_GAIN_DB,
        "gain_linear": float(gain),
        "gain_db": float(20.0 * math.log10(gain)) if gain > 0 else -300.0,
        "input_ac_rms_dbfs": _amplitude_dbfs(input_rms, 1.0),
        "output_ac_rms_dbfs": _amplitude_dbfs(output_rms, 1.0),
        "output_peak_dbfs": _amplitude_dbfs(output_peak, 1.0),
    }
    return monitor, metadata


def save_capture_check(
    quiet_voltage: np.ndarray,
    noise_voltage: np.ndarray,
    hardware_config: HardwareConfig,
    quiet_metadata: dict[str, Any] | None = None,
    noise_metadata: dict[str, Any] | None = None,
    output_root: str | Path = CAPTURE_CHECKS_DIR,
    progress_callback: ProgressCallback | None = None,
) -> CaptureCheckResult:
    quiet = _validate_multichannel(quiet_voltage, "quiet_voltage").astype(np.float32, copy=False)
    noise = _validate_multichannel(noise_voltage, "noise_voltage").astype(np.float32, copy=False)
    if quiet.shape[1] != noise.shape[1]:
        raise ValueError("quiet and noise channel counts must match")

    _progress(progress_callback, 5, "正在创建自检目录")
    output_dir = _new_output_dir(Path(output_root))
    np.save(output_dir / "quiet_voltage.npy", quiet, allow_pickle=False)
    np.save(output_dir / "noise_voltage.npy", noise, allow_pickle=False)

    stage_metadata = {
        "quiet": dict(quiet_metadata or {}),
        "noise": dict(noise_metadata or {}),
    }
    report = analyze_capture_pair(
        quiet,
        noise,
        sample_rate=hardware_config.sample_rate,
        input_range_volts=hardware_config.input_range_volts,
        selected_channel=hardware_config.adc_channel,
        hardware_config=hardware_config.to_dict(),
        stage_metadata=stage_metadata,
    )

    _progress(progress_callback, 20, "正在生成原始和试听 WAV")
    audio_files: list[dict[str, Any]] = []
    total_files = quiet.shape[1] * 2
    completed = 0
    for stage_name, matrix in (("quiet", quiet), ("noise", noise)):
        for index in range(matrix.shape[1]):
            channel = index + 1
            voltage = matrix[:, index]
            raw_name = f"{stage_name}_ch{channel}_raw.wav"
            monitor_name = f"{stage_name}_ch{channel}_monitor.wav"
            save_wav(
                output_dir / raw_name,
                voltage_to_audio(voltage, hardware_config.input_range_volts),
                hardware_config.sample_rate,
            )
            monitor, monitor_metadata = create_monitor_audio(
                voltage,
                hardware_config.sample_rate,
                hardware_config.input_range_volts,
            )
            save_wav(output_dir / monitor_name, monitor, hardware_config.sample_rate)
            audio_files.append(
                {
                    "stage": stage_name,
                    "channel": channel,
                    "raw_wav": raw_name,
                    "monitor_wav": monitor_name,
                    "monitor_processing": monitor_metadata,
                }
            )
            completed += 1
            percent = 20 + int(round(completed / total_files * 65))
            _progress(progress_callback, percent, f"正在生成 {stage_name} CH{channel} 音频")

    report.audio_files = audio_files
    report.output_dir = str(output_dir)
    save_json(output_dir / "report.json", report.to_dict())
    (output_dir / "summary.txt").write_text(_summary_text(report), encoding="utf-8")
    _progress(progress_callback, 100, "采集链路自检报告已完成")
    return CaptureCheckResult(report=report, output_dir=output_dir)


def _compare_channel(
    quiet: ChannelMetrics,
    noise: ChannelMetrics,
    input_range_volts: float,
) -> ChannelComparison:
    amplitude_floor = max(float(input_range_volts) * 1e-12, np.finfo(np.float64).tiny)
    power_floor = amplitude_floor * amplitude_floor
    rms_increase = 20.0 * math.log10(
        max(noise.ac_rms_volts, amplitude_floor) / max(quiet.ac_rms_volts, amplitude_floor)
    )
    band_increase = 10.0 * math.log10(
        max(noise.audible_band_power, power_floor) / max(quiet.audible_band_power, power_floor)
    )

    if not quiet.finite or not noise.finite:
        status = "invalid"
        message = "包含非有限值或没有有效采样"
    elif noise.clipping_ratio > CLIPPING_RATIO_LIMIT:
        status = "clipped"
        message = "噪声阶段发生削波，需增大量程后重新测试"
    elif rms_increase >= STRONG_INCREASE_DB and band_increase >= STRONG_INCREASE_DB:
        status = "strong"
        message = "明确检测到机械声音响应"
    elif rms_increase >= LIKELY_INCREASE_DB and band_increase >= LIKELY_INCREASE_DB:
        status = "likely"
        message = "较大概率检测到机械声音响应"
    else:
        status = "inconclusive"
        message = "声音响应证据不足"

    return ChannelComparison(
        channel=quiet.channel,
        status=status,
        message=message,
        ac_rms_increase_db=float(rms_increase),
        band_power_increase_db=float(band_increase),
        quiet=quiet,
        noise=noise,
    )


def _select_recommended_channel(
    comparisons: list[ChannelComparison],
    selected_channel: int,
) -> ChannelComparison:
    def score(item: ChannelComparison) -> tuple[int, float, int]:
        status_rank = {"strong": 5, "likely": 4, "clipped": 3, "inconclusive": 2, "invalid": 0}
        evidence = min(item.ac_rms_increase_db, item.band_power_increase_db)
        selected_bonus = 1 if item.channel == selected_channel else 0
        return status_rank.get(item.status, 0), evidence, selected_bonus

    return max(comparisons, key=score)


def _overall_result(
    comparisons: list[ChannelComparison],
    recommended_channel: int,
) -> tuple[str, str]:
    statuses = {item.status for item in comparisons}
    if "strong" in statuses:
        return "strong", f"CH{recommended_channel} 明确随机械噪声变化，已采到声音响应"
    if "likely" in statuses:
        return "likely", f"CH{recommended_channel} 较大概率采到声音响应，建议再重复一次确认"
    if "clipped" in statuses:
        return "clipped", "至少一个通道发生削波，调整量程后必须重新自检"
    if statuses == {"invalid"}:
        return "invalid", "四个通道都没有有效数据，先排查 SDK、连接和采集卡"
    return "inconclusive", "尚不能证明采到了声音，先检查通道、接线、供电和前置放大"


def _audible_band_power(audio: np.ndarray, sample_rate: int) -> tuple[float, float]:
    if audio.size < 8:
        return 0.0, 0.0
    nperseg = min(4096, int(audio.size))
    frequencies, psd = signal.welch(
        audio,
        fs=float(sample_rate),
        window="hann",
        nperseg=nperseg,
        detrend=False,
        scaling="density",
    )
    upper = min(AUDIBLE_HIGH_HZ, float(sample_rate) / 2.0)
    mask = (frequencies >= AUDIBLE_LOW_HZ) & (frequencies <= upper)
    if not np.any(mask):
        return 0.0, 0.0
    frequency_step = float(frequencies[1] - frequencies[0]) if frequencies.size > 1 else 0.0
    band_psd = psd[mask]
    band_power = float(np.sum(band_psd) * frequency_step)
    if not np.any(band_psd > 0.0):
        return 0.0, 0.0
    dominant_index = int(np.argmax(band_psd))
    dominant_frequency = float(frequencies[mask][dominant_index])
    return max(0.0, band_power), dominant_frequency


def _highpass(audio: np.ndarray, sample_rate: int) -> tuple[np.ndarray, bool]:
    if audio.size < 32 or sample_rate <= MONITOR_HIGHPASS_HZ * 2.0:
        return audio, False
    sos = signal.butter(4, MONITOR_HIGHPASS_HZ, btype="highpass", fs=sample_rate, output="sos")
    try:
        return signal.sosfiltfilt(sos, audio), True
    except ValueError:
        return audio, False


def _validate_multichannel(value: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(value)
    if arr.ndim != 2 or arr.shape[1] != 4:
        raise ValueError(f"{name} must have shape (samples, 4)")
    if arr.shape[0] == 0:
        raise ValueError(f"{name} must contain samples")
    return arr


def _new_output_dir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = root / timestamp
    suffix = 1
    while candidate.exists():
        candidate = root / f"{timestamp}_{suffix:02d}"
        suffix += 1
    candidate.mkdir(parents=False)
    return candidate


def _summary_text(report: CaptureCheckReport) -> str:
    status_text = {
        "strong": "明确采到声音响应",
        "likely": "较大概率采到声音响应",
        "inconclusive": "证据不足",
        "clipped": "存在削波",
        "invalid": "采集无效",
    }
    lines = [
        "鲁班猫声音采集链路自检",
        f"结论: {status_text.get(report.overall_status, report.overall_status)}",
        f"说明: {report.overall_message}",
        f"当前选择通道: CH{report.selected_channel}",
        f"推荐通道: CH{report.recommended_channel}",
        f"当前量程: {report.input_range_volts:g} V",
        f"推荐量程: {report.recommended_input_range_volts:g} V",
        "",
        "四通道对比:",
    ]
    for item in report.channels:
        lines.append(
            f"CH{item.channel}: {status_text.get(item.status, item.status)}; "
            f"AC RMS 增量 {item.ac_rms_increase_db:.2f} dB; "
            f"可听频带增量 {item.band_power_increase_db:.2f} dB; "
            f"噪声峰值 {item.noise.peak_abs_volts:.9f} V; "
            f"削波 {item.noise.clipping_ratio * 100.0:.4f}%"
        )
    lines.extend(
        [
            "",
            "monitor.wav 仅用于试听，进行了去直流、20 Hz 高通和一次固定线性增益。",
            "raw_voltage.npy 是原始电压原件；试听文件不会进入降噪或模型流程。",
            "本报告不能替代麦克风偏置、IEPE 激励、前置放大或真实声压校准。",
        ]
    )
    return "\n".join(lines) + "\n"


def _amplitude_dbfs(amplitude: float, full_scale: float) -> float:
    if amplitude <= 0 or full_scale <= 0:
        return -300.0
    return float(20.0 * math.log10(amplitude / full_scale))


def _ac_rms(audio: np.ndarray) -> float:
    arr = np.asarray(audio, dtype=np.float64)
    if arr.size == 0:
        return 0.0
    centered = arr - float(np.mean(arr))
    return float(np.sqrt(np.mean(np.square(centered))))


def _progress(callback: ProgressCallback | None, percent: int, message: str) -> None:
    if callback is not None:
        callback(int(percent), message)
