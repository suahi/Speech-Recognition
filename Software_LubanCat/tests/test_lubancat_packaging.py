from __future__ import annotations

import json
from pathlib import Path

from voice_fault_diagnosis.capture.vk701n import resolve_sdk_library
from voice_fault_diagnosis.models import HardwareConfig
from voice_fault_diagnosis.paths import CONFIG_DIR, SOFTWARE_ROOT
from voice_fault_diagnosis.runtime_checks import desktop_dependency_errors


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


def test_lubancat_dependency_constraints_are_arm64_safe() -> None:
    pyproject = (SOFTWARE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    requirements = (SOFTWARE_ROOT / "requirements-lubancat-aarch64.txt").read_text(encoding="utf-8")

    assert 'requires-python = ">=3.10,<3.13"' in pyproject
    assert '"numpy>=1.26.0,<2.0"' in pyproject
    assert '"torch>=2.8,<2.13"' in pyproject
    assert '"PySide6_Essentials==6.7.3; platform_system == \'Linux\'' in pyproject
    assert "platform_machine == 'aarch64'" in pyproject
    assert '"PySide6>=6.7,<6.11; platform_system != \'Linux\'' in pyproject
    assert "matplotlib" not in pyproject
    assert "numpy>=1.26.0,<2.0" in requirements
    assert "shiboken6==6.7.3" in requirements
    assert "PySide6_Essentials==6.7.3" in requirements


def test_lubancat_scripts_create_venv_and_export_runtime_paths() -> None:
    scripts_dir = SOFTWARE_ROOT / "scripts"
    install_script = (scripts_dir / "install_lubancat.sh").read_text(encoding="utf-8")
    run_script = (scripts_dir / "run_app.sh").read_text(encoding="utf-8")
    probe_script = (scripts_dir / "probe_vk701n.sh").read_text(encoding="utf-8")
    test_script = (scripts_dir / "test_lubancat.sh").read_text(encoding="utf-8")

    assert "uname -m" in install_script
    assert "python3-venv" in install_script
    assert "--prefer-binary" in install_script
    assert "--force-reinstall" in install_script
    assert "requirements-lubancat-aarch64.txt" in install_script
    assert "Dependency check:" in install_script
    assert "QT_QPA_PLATFORM" in run_script
    for script in (run_script, probe_script, test_script):
        assert '.venv/bin/activate' in script
        assert "LD_LIBRARY_PATH" in script
        assert "PYTHONPATH" in script


def test_lubancat_text_files_keep_lf_line_endings() -> None:
    attributes = (SOFTWARE_ROOT / ".gitattributes").read_text(encoding="utf-8")

    assert "*.sh text eol=lf" in attributes
    assert "*.py text eol=lf" in attributes
    assert "*.toml text eol=lf" in attributes
    assert "*.txt text eol=lf" in attributes


def test_lubancat_ui_exposes_diagnosis_progress_and_utf8_labels() -> None:
    main_window = (SOFTWARE_ROOT / "src" / "voice_fault_diagnosis" / "app" / "main_window.py").read_text(
        encoding="utf-8"
    )

    assert "诊断进度" in main_window
    assert "停止并诊断" in main_window
    assert "模型已预热" in main_window
    assert "progress_changed" in main_window
    assert "QProgressBar" in main_window


def test_direct_startup_preflight_reports_numpy_2_and_missing_xcb_cursor() -> None:
    versions = {
        "numpy": "2.0.2",
        "PySide6_Essentials": "6.7.3",
        "shiboken6": "6.7.3",
    }

    errors = desktop_dependency_errors(
        system="Linux",
        machine="aarch64",
        python_version=(3, 10),
        environ={"QT_QPA_PLATFORM": "xcb"},
        version_lookup=versions.get,
        find_library=lambda name: None,
    )

    assert any("NumPy 2.0.2" in error for error in errors)
    assert any("libxcb-cursor0" in error for error in errors)


def test_direct_startup_preflight_accepts_lubancat_dependency_set() -> None:
    versions = {
        "numpy": "1.26.4",
        "PySide6_Essentials": "6.7.3",
        "shiboken6": "6.7.3",
    }

    errors = desktop_dependency_errors(
        system="Linux",
        machine="aarch64",
        python_version=(3, 10),
        environ={"QT_QPA_PLATFORM": "xcb"},
        version_lookup=versions.get,
        find_library=lambda name: "/usr/lib/aarch64-linux-gnu/libxcb-cursor.so.0",
    )

    assert errors == []
