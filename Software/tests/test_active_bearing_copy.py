from __future__ import annotations

from pathlib import Path


def test_active_app_has_no_capture_hardware_copy() -> None:
    root = Path(__file__).resolve().parents[1]
    active_text = "\n".join(
        (root / relative_path).read_text(encoding="utf-8")
        for relative_path in (
            "README.md",
            "run_app.py",
            "configs/bearing_demo.json",
            "src/voice_fault_diagnosis/app/main_window.py",
            "src/voice_fault_diagnosis/config.py",
            "src/voice_fault_diagnosis/pipeline.py",
        )
    ).lower()
    for forbidden in ("vk701", "麦克风", "采集卡", "windows_c_example", "pc_direct", "arm64", "xcb"):
        assert forbidden not in active_text
