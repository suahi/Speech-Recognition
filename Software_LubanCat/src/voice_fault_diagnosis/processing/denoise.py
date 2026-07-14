from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from voice_fault_diagnosis.models import DenoiseConfig, DiagnosisProgress


ProgressCallback = Callable[[DiagnosisProgress], None]


def apply_denoise(
    audio: np.ndarray,
    sample_rate: int,
    config: DenoiseConfig,
    progress_callback: ProgressCallback | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    arr = np.asarray(audio, dtype=np.float32)
    _emit(progress_callback, "denoise_prepare", 5, "正在校验降噪参数")
    _validate_config(arr, sample_rate, config)
    metadata: dict[str, Any] = {
        "enabled": bool(config.enabled),
        "applied": False,
        "methods": [],
    }
    if not config.enabled:
        metadata["skip_reason"] = "disabled"
        metadata["metrics"] = _calculate_metrics(arr, arr)
        _emit(progress_callback, "denoise_complete", 100, "已跳过降噪")
        return arr.copy(), metadata

    processed = arr.astype(np.float32, copy=True)
    if config.bandpass_enabled:
        _emit(progress_callback, "denoise_bandpass", 20, "正在执行带通滤波")
        processed = _bandpass(processed, sample_rate, config)
        metadata["methods"].append("bandpass")
        metadata["bandpass"] = {
            "low_hz": config.bandpass_low_hz,
            "high_hz": config.bandpass_high_hz,
            "order": config.bandpass_order,
        }
    if config.wavelet_enabled:
        _emit(progress_callback, "denoise_wavelet", 60, "正在执行小波降噪")
        processed = _wavelet_denoise(processed, config)
        metadata["methods"].append("wavelet")
        metadata["wavelet"] = {
            "wavelet": config.wavelet,
            "level": config.wavelet_level,
            "threshold": config.wavelet_threshold,
        }
    if not metadata["methods"]:
        metadata["skip_reason"] = "no_method_enabled"

    _emit(progress_callback, "denoise_metrics", 90, "正在计算波形对比指标")
    processed = processed.astype(np.float32)
    metadata["applied"] = bool(metadata["methods"])
    metadata["metrics"] = _calculate_metrics(arr, processed)
    _emit(progress_callback, "denoise_complete", 100, "降噪处理完成")
    return processed, metadata


def _validate_config(audio: np.ndarray, sample_rate: int, config: DenoiseConfig) -> None:
    if int(sample_rate) <= 0:
        raise ValueError("sample_rate must be positive")
    if not config.enabled:
        return
    if config.bandpass_enabled:
        nyquist = float(sample_rate) / 2.0
        low = float(config.bandpass_low_hz)
        high = float(config.bandpass_high_hz)
        if not 0 < low < high < nyquist:
            raise ValueError("bandpass frequencies must satisfy 0 < low < high < Nyquist")
        if int(config.bandpass_order) < 1:
            raise ValueError("bandpass_order must be at least 1")
    if config.wavelet_enabled:
        import pywt

        wavelet = pywt.Wavelet(str(config.wavelet))
        max_level = pywt.dwt_max_level(int(audio.size), wavelet.dec_len)
        if int(config.wavelet_level) < 1 or int(config.wavelet_level) > max_level:
            raise ValueError(f"wavelet_level must be between 1 and {max_level} for this signal")
        if str(config.wavelet_threshold or "").lower() not in {"soft", "hard"}:
            raise ValueError("wavelet_threshold must be 'soft' or 'hard'")


def _calculate_metrics(raw: np.ndarray, processed: np.ndarray) -> dict[str, float]:
    raw64 = np.asarray(raw, dtype=np.float64)
    processed64 = np.asarray(processed, dtype=np.float64)
    if raw64.size == 0:
        return {
            "raw_ac_rms": 0.0,
            "processed_ac_rms": 0.0,
            "raw_peak_to_peak": 0.0,
            "processed_peak_to_peak": 0.0,
            "difference_rms": 0.0,
        }
    raw_centered = raw64 - float(np.mean(raw64))
    processed_centered = processed64 - float(np.mean(processed64))
    difference = raw64 - processed64
    return {
        "raw_ac_rms": float(np.sqrt(np.mean(raw_centered * raw_centered))),
        "processed_ac_rms": float(np.sqrt(np.mean(processed_centered * processed_centered))),
        "raw_peak_to_peak": float(np.ptp(raw64)),
        "processed_peak_to_peak": float(np.ptp(processed64)),
        "difference_rms": float(np.sqrt(np.mean(difference * difference))),
    }


def _bandpass(audio: np.ndarray, sample_rate: int, config: DenoiseConfig) -> np.ndarray:
    from scipy import signal

    nyquist = float(sample_rate) / 2.0
    low = max(1e-6, float(config.bandpass_low_hz)) / nyquist
    high = min(float(config.bandpass_high_hz), nyquist * 0.999) / nyquist
    if not 0 < low < high < 1:
        raise ValueError("bandpass frequencies must satisfy 0 < low < high < Nyquist")
    sos = signal.butter(int(config.bandpass_order), [low, high], btype="bandpass", output="sos")
    if audio.size < max(32, int(config.bandpass_order) * 6):
        return signal.sosfilt(sos, audio).astype(np.float32)
    return signal.sosfiltfilt(sos, audio).astype(np.float32)


def _wavelet_denoise(audio: np.ndarray, config: DenoiseConfig) -> np.ndarray:
    import pywt

    if audio.size == 0:
        return audio.astype(np.float32)
    coeffs = pywt.wavedec(audio, config.wavelet, level=int(config.wavelet_level))
    if len(coeffs) <= 1:
        return audio.astype(np.float32)
    detail = coeffs[-1]
    sigma = np.median(np.abs(detail)) / 0.6745 if detail.size else 0.0
    threshold = sigma * np.sqrt(2.0 * np.log(max(2, audio.size)))
    denoised = [coeffs[0]]
    mode = str(config.wavelet_threshold or "soft").lower()
    for coeff in coeffs[1:]:
        denoised.append(pywt.threshold(coeff, threshold, mode=mode))
    restored = pywt.waverec(denoised, config.wavelet)
    return restored[: audio.size].astype(np.float32)


def _emit(progress_callback: ProgressCallback | None, stage: str, percent: int, message: str) -> None:
    if progress_callback is not None:
        progress_callback(DiagnosisProgress(stage=stage, percent=percent, message=message))
