from __future__ import annotations

from pathlib import Path
import re

from voice_fault_diagnosis.capture.vk701n import INPUT_RANGE_CODES, resolve_sdk_library
from voice_fault_diagnosis.config import EXPECTED_LABEL_CODES, load_pc_config
from voice_fault_diagnosis.paths import SOFTWARE_ROOT
from voice_fault_diagnosis.runtime_checks import PE_MACHINE_AMD64, read_pe_machine


def test_default_pc_config_and_relative_assets() -> None:
    config = load_pc_config()

    assert config.source_path.name == "pc_direct.json"
    assert config.capture_duration_seconds == 10.0
    assert config.hardware.server_port == 8234
    assert config.hardware.adc_channel == 2
    assert config.hardware.sample_rate == 50000
    assert config.hardware.bit_mode == 24
    assert config.hardware.input_range_volts == 5.0
    assert config.hardware.initialize_all_profile == "windows_c_example"
    assert Path(config.hardware.sdk_library_path).is_absolute()
    assert Path(config.hardware.sdk_library_path).is_relative_to(SOFTWARE_ROOT)
    assert config.model.model_path.is_relative_to(SOFTWARE_ROOT)
    assert tuple(config.model.labels) == EXPECTED_LABEL_CODES


def test_relative_sdk_resolution_and_x64_pe_header() -> None:
    dll_path = resolve_sdk_library("vendor/vk701n/VK70xNMC_DAQ2.dll")

    assert dll_path == (SOFTWARE_ROOT / "vendor" / "vk701n" / "VK70xNMC_DAQ2.dll").resolve()
    assert read_pe_machine(dll_path) == PE_MACHINE_AMD64


def test_input_range_mapping_matches_vendor_api() -> None:
    assert INPUT_RANGE_CODES == {
        10.0: 0,
        5.0: 1,
        2.5: 2,
        1.0: 3,
        0.5: 4,
        0.1: 5,
        0.02: 6,
        0.001: 7,
    }


def test_loading_config_does_not_construct_sdk(monkeypatch) -> None:
    import voice_fault_diagnosis.capture.vk701n as capture_module

    def forbidden(*args, **kwargs):
        raise AssertionError("SDK must remain lazy during config load")

    monkeypatch.setattr(capture_module, "CtypesVk701nSdk", forbidden)
    config = load_pc_config()

    assert config.hardware.adc_channel == 2


def test_active_pc_text_has_no_board_runtime_language() -> None:
    files = [
        *sorted((SOFTWARE_ROOT / "src").rglob("*.py")),
        SOFTWARE_ROOT / "configs" / "pc_direct.json",
        SOFTWARE_ROOT / "README.md",
    ]
    forbidden = ("鲁班猫", "ARM64", "xcb")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)

    for term in forbidden:
        assert term not in combined
    assert re.search(r"\.so\b", combined, flags=re.IGNORECASE) is None
