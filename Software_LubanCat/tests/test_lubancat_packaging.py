from __future__ import annotations

import json

from voice_fault_diagnosis.capture.vk701n import resolve_sdk_library
from voice_fault_diagnosis.paths import LIGHT_CONFIG_PATH, SOFTWARE_ROOT
from voice_fault_diagnosis.runtime_checks import desktop_dependency_errors


def test_light_config_is_the_only_operator_facing_runtime_config() -> None:
    config = json.loads(LIGHT_CONFIG_PATH.read_text(encoding="utf-8"))

    assert config["hardware"]["sdk_library_path"] == "vendor/vk701n/libVK70XNMC_DAQ_SHARED.so"
    assert config["capture"]["duration_seconds"] == 10.0
    assert config["model"]["labels"] == {
        "C0": "静音",
        "C1": "风扇",
        "C2": "敲击",
        "C3": "摩擦",
        "C4": "气流",
        "C5": "人声",
    }


def test_relative_sdk_path_resolves_from_lubancat_project_root() -> None:
    assert resolve_sdk_library("vendor/vk701n/libVK70XNMC_DAQ_SHARED.so") == (
        SOFTWARE_ROOT / "vendor" / "vk701n" / "libVK70XNMC_DAQ_SHARED.so"
    ).resolve()


def test_lubancat_dependency_constraints_are_arm64_safe() -> None:
    pyproject = (SOFTWARE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    requirements = (SOFTWARE_ROOT / "requirements-lubancat-aarch64.txt").read_text(encoding="utf-8")

    assert 'requires-python = ">=3.10,<3.13"' in pyproject
    assert '"numpy>=1.26.0,<2.0"' in pyproject
    assert '"torch>=2.8,<2.13"' in pyproject
    assert "PyWavelets" not in pyproject
    assert "PyWavelets" not in requirements
    assert "PySide6_Essentials==6.7.3" in requirements


def test_desktop_runtime_preflight_accepts_lubancat_dependency_set() -> None:
    versions = {"numpy": "1.26.4", "PySide6_Essentials": "6.7.3", "shiboken6": "6.7.3"}

    assert desktop_dependency_errors(
        system="Linux",
        machine="aarch64",
        python_version=(3, 10),
        environ={"QT_QPA_PLATFORM": "xcb"},
        version_lookup=versions.get,
        find_library=lambda name: "/usr/lib/aarch64-linux-gnu/libxcb-cursor.so.0",
    ) == []


def test_single_page_ui_does_not_expose_legacy_workflow() -> None:
    main_window = (SOFTWARE_ROOT / "src" / "voice_fault_diagnosis" / "app" / "main_window.py").read_text(
        encoding="utf-8"
    )

    assert "声纹采集与六类识别" in main_window
    assert "开始采集" in main_window
    assert "停止并识别" in main_window
    assert "QTabWidget" not in main_window
    assert "DenoiseWorker" not in main_window
    assert "LegacyCnnEngine" not in main_window
