from __future__ import annotations

from typing import Any

import numpy as np

from voice_fault_diagnosis.models import DenoiseConfig


def apply_denoise(
    audio: np.ndarray,
    sample_rate: int,
    config: DenoiseConfig,
) -> tuple[np.ndarray, dict[str, Any]]:
    arr = np.asarray(audio, dtype=np.float32)
    metadata: dict[str, Any] = {"enabled": bool(config.enabled)}
    if not config.enabled:
        return arr.copy(), metadata

    processed = arr.astype(np.float32, copy=True)
    if config.bandpass_enabled:
        processed = _bandpass(processed, sample_rate, config)
        metadata["bandpass"] = {
            "low_hz": config.bandpass_low_hz,
            "high_hz": config.bandpass_high_hz,
            "order": config.bandpass_order,
        }
    if config.wavelet_enabled:
        processed = _wavelet_denoise(processed, config)
        metadata["wavelet"] = {
            "wavelet": config.wavelet,
            "level": config.wavelet_level,
            "threshold": config.wavelet_threshold,
        }
    return processed.astype(np.float32), metadata


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
