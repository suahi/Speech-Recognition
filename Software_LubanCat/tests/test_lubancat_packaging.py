from __future__ import annotations

import json
from pathlib import Path

from voice_fault_diagnosis.capture.vk701n import resolve_sdk_library
from voice_fault_diagnosis.models import HardwareConfig
from voice_fault_diagnosis.paths import CONFIG_DIR, SOFTWARE_ROOT


def test_lubancat_hardware_config_uses_linux_sdk_path() -> None:
    config = json.loads((CONFIG_DIR / "hardware_vk701n.json").read_text(encoding="utf-8"))

    assert config["sdk_library_path"] == "vendor/vk701n/libVK70XNMC_DAQ_SHARED.so"
    assert ".dll" not in config["sdk_library_path"].lower()
    assert "\\" not in config["sdk_library_path"]
    assert config["initialize_all_profile"] == "code_source"


def test_relative_sdk_path_resolves_from_lubancat_project_root() -> None:
    resolved = resolve_sdk_library("vendor/vk701n/libVK70XNMC_DAQ_SHARED.so")

    assert resolved == (SOFTWARE_ROOT / "vendor" / "vk701n" / "libVK70XNMC_DAQ_SHARED.so").resolve()


def test_lubancat_hardware_defaults_use_initialize_all_profile() -> None:
    config = HardwareConfig()

    assert config.initialize_all_profile == "code_source"
