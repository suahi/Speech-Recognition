from __future__ import annotations

import json
import wave

import numpy as np

from voice_fault_diagnosis.diagnostics.sound_capture import (
    MONITOR_MAX_GAIN_DB,
    analyze_capture_pair,
    create_monitor_audio,
    save_capture_check,
    suggest_input_range,
)
from voice_fault_diagnosis.models import HardwareConfig


def test_capture_pair_finds_channel_with_strong_mechanical_response() -> None:
    sample_rate = 8000
    sample_count = sample_rate * 2
    rng = np.random.default_rng(7)
    quiet = rng.normal(0.0, 0.0001, size=(sample_count, 4)).astype(np.float32)
    noise = rng.normal(0.0, 0.0001, size=(sample_count, 4)).astype(np.float32)
    time_axis = np.arange(sample_count, dtype=np.float32) / sample_rate
    noise[:, 1] += 0.003 * np.sin(2.0 * np.pi * 1000.0 * time_axis)

    report = analyze_capture_pair(
        quiet,
        noise,
        sample_rate=sample_rate,
        input_range_volts=0.1,
        selected_channel=2,
    )

    assert report.overall_status == "strong"
    assert report.recommended_channel == 2
    assert report.recommended_input_range_volts == 0.02
    channel = report.channels[1]
    assert channel.status == "strong"
    assert channel.ac_rms_increase_db >= 10.0
    assert channel.band_power_increase_db >= 10.0
    assert abs(channel.noise.dominant_frequency_hz - 1000.0) < 10.0


def test_capture_pair_marks_clipping_and_nonfinite_data() -> None:
    sample_rate = 4000
    quiet = np.zeros((sample_rate, 4), dtype=np.float32)
    noise = np.zeros((sample_rate, 4), dtype=np.float32)
    noise[:20, 0] = 0.1
    quiet[0, 1] = np.nan

    report = analyze_capture_pair(quiet, noise, sample_rate, 0.1, selected_channel=1)

    assert report.channels[0].status == "clipped"
    assert report.channels[0].noise.clipping_ratio > 0.001
    assert report.channels[1].status == "invalid"
    assert report.overall_status == "clipped"
    assert report.recommended_channel == 1
    assert report.recommended_input_range_volts == 0.5


def test_input_range_suggestion_keeps_twenty_percent_peak_headroom() -> None:
    assert suggest_input_range(0.055, 5.0) == 0.1
    assert suggest_input_range(0.018, 5.0) == 0.1
    assert suggest_input_range(0.0, 5.0) == 5.0


def test_monitor_audio_is_linear_capped_and_keeps_main_frequency() -> None:
    sample_rate = 50000
    time_axis = np.arange(sample_rate, dtype=np.float32) / sample_rate
    voltage = 0.02 + 0.002 * np.sin(2.0 * np.pi * 1000.0 * time_axis)

    monitor, metadata = create_monitor_audio(voltage, sample_rate, 5.0)

    assert monitor.shape == voltage.shape
    assert monitor.dtype == np.float32
    assert metadata["highpass_applied"] is True
    assert metadata["gain_db"] <= MONITOR_MAX_GAIN_DB + 1e-6
    assert float(np.max(np.abs(monitor))) <= 10.0 ** (-1.0 / 20.0) + 1e-6
    spectrum = np.abs(np.fft.rfft(monitor))
    frequencies = np.fft.rfftfreq(monitor.size, 1.0 / sample_rate)
    dominant = float(frequencies[int(np.argmax(spectrum[1:])) + 1])
    assert abs(dominant - 1000.0) <= 1.0


def test_monitor_audio_does_not_invent_sound_for_silence() -> None:
    monitor, metadata = create_monitor_audio(np.zeros(1000, dtype=np.float32), 50000, 5.0)

    assert np.count_nonzero(monitor) == 0
    assert metadata["gain_db"] == 0.0


def test_capture_check_saves_voltage_report_and_all_wavs(tmp_path) -> None:
    sample_rate = 8000
    sample_count = sample_rate // 2
    time_axis = np.arange(sample_count, dtype=np.float32) / sample_rate
    quiet = np.zeros((sample_count, 4), dtype=np.float32)
    noise = np.zeros((sample_count, 4), dtype=np.float32)
    noise[:, 2] = 0.005 * np.sin(2.0 * np.pi * 500.0 * time_axis)
    hardware = HardwareConfig(
        sample_rate=sample_rate,
        adc_channel=3,
        input_range_volts=0.1,
    )
    progress: list[tuple[int, str]] = []

    result = save_capture_check(
        quiet,
        noise,
        hardware,
        output_root=tmp_path,
        progress_callback=lambda percent, message: progress.append((percent, message)),
    )

    np.testing.assert_array_equal(np.load(result.output_dir / "quiet_voltage.npy"), quiet)
    np.testing.assert_array_equal(np.load(result.output_dir / "noise_voltage.npy"), noise)
    assert (result.output_dir / "report.json").exists()
    assert (result.output_dir / "summary.txt").exists()
    assert len(list(result.output_dir.glob("*_raw.wav"))) == 8
    assert len(list(result.output_dir.glob("*_monitor.wav"))) == 8
    report_json = json.loads((result.output_dir / "report.json").read_text(encoding="utf-8"))
    assert report_json["recommended_channel"] == 3
    assert len(report_json["audio_files"]) == 8
    assert progress[-1][0] == 100
    with wave.open(str(result.output_dir / "noise_ch3_monitor.wav"), "rb") as handle:
        assert handle.getframerate() == sample_rate
        assert handle.getnframes() == sample_count
