from __future__ import annotations

import numpy as np


def voltage_to_legacy_bytes(voltage: np.ndarray, gain: float = 0.668) -> bytes:
    """Convert CH1 voltage to the byte stream consumed by the legacy CNN code.

    This intentionally mirrors CodeSource/python_continuous_sampling/GetSampleDataAndSave.py:
    voltage is scaled to an unsigned 24-bit range, written as little-endian 3-byte
    samples, then truncated to recvLen bytes before being queued.
    """

    arr = np.asarray(voltage, dtype=np.float64)
    if arr.size == 0:
        return b""
    scaled = np.clip((arr * float(gain) + 5.0) * 0.1, 0.0, 1.0)
    int_samples = np.asarray(scaled * 8388607.0, dtype=np.int64)
    triplets = np.empty(int_samples.size * 3, dtype=np.uint8)
    triplets[0::3] = int_samples & 0x0000FF
    triplets[1::3] = (int_samples & 0x00FF00) >> 8
    triplets[2::3] = (int_samples >> 16) & 0xFF
    return bytes(triplets[: int_samples.size])
