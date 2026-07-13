from __future__ import annotations

import ctypes.util
from importlib import metadata
import os
import platform
import sys
from pathlib import Path
from typing import Callable, Mapping


ARM64_MACHINES = {"aarch64", "arm64"}
LUBANCAT_QT_VERSION = "6.7.3"
APT_QT_XCB_PACKAGES = [
    "libxcb-cursor0",
    "libxcb-icccm4",
    "libxcb-image0",
    "libxcb-keysyms1",
    "libxcb-randr0",
    "libxcb-render-util0",
    "libxcb-shape0",
    "libxcb-xfixes0",
    "libxcb-xinerama0",
    "libxcb-xinput0",
]


def configure_lubancat_environment(project_root: Path) -> None:
    """Apply runtime defaults used by scripts/run_app.sh for direct python runs."""
    project_root = Path(project_root).resolve()
    _prepend_env_path("LD_LIBRARY_PATH", project_root / "vendor" / "vk701n")
    _prepend_env_path("PYTHONPATH", project_root / "src")

    if "QT_QPA_PLATFORM" not in os.environ:
        if os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("DISPLAY"):
            os.environ["QT_QPA_PLATFORM"] = "wayland"
        else:
            os.environ["QT_QPA_PLATFORM"] = "xcb"


def desktop_dependency_errors(
    *,
    system: str | None = None,
    machine: str | None = None,
    python_version: tuple[int, int] | None = None,
    environ: Mapping[str, str] | None = None,
    version_lookup: Callable[[str], str | None] | None = None,
    find_library: Callable[[str], str | None] | None = None,
) -> list[str]:
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    python_version = python_version or (sys.version_info.major, sys.version_info.minor)
    environ = environ or os.environ
    version_lookup = version_lookup or _distribution_version
    find_library = find_library or ctypes.util.find_library

    errors: list[str] = []
    if python_version < (3, 10) or python_version >= (3, 13):
        errors.append(
            f"Python {python_version[0]}.{python_version[1]} is not supported; use Python 3.10, 3.11, or 3.12."
        )

    numpy_version = version_lookup("numpy")
    if numpy_version is None:
        errors.append("NumPy is not installed.")
    elif not _version_in_range(numpy_version, lower=(1, 26), upper=(2, 0)):
        errors.append(
            f"NumPy {numpy_version} is installed, but LubanCat runtime requires numpy>=1.26,<2.0."
        )

    if system == "Linux" and machine in ARM64_MACHINES:
        essentials_version = _first_distribution_version(
            version_lookup,
            "PySide6_Essentials",
            "PySide6-Essentials",
        )
        shiboken_version = version_lookup("shiboken6")
        if essentials_version != LUBANCAT_QT_VERSION:
            errors.append(
                "PySide6_Essentials "
                f"{essentials_version or 'is not installed'}; LubanCat ARM64 requires {LUBANCAT_QT_VERSION}."
            )
        if shiboken_version != LUBANCAT_QT_VERSION:
            errors.append(
                f"shiboken6 {shiboken_version or 'is not installed'}; LubanCat ARM64 requires {LUBANCAT_QT_VERSION}."
            )

        qt_platform = (environ.get("QT_QPA_PLATFORM") or "xcb").split(":", 1)[0].lower()
        if qt_platform == "xcb" and not find_library("xcb-cursor"):
            errors.append("Qt xcb platform plugin dependency libxcb-cursor0 is not installed.")

    return errors


def format_desktop_dependency_error(errors: list[str], project_root: Path) -> str:
    project_root = Path(project_root).resolve()
    packages = " ".join(APT_QT_XCB_PACKAGES)
    requirements = project_root / "requirements-lubancat-aarch64.txt"
    lines = [
        "LubanCat desktop runtime check failed:",
        *[f"- {error}" for error in errors],
        "",
        "Repair the active Python environment and Qt xcb system packages:",
        f"  cd {project_root}",
        f"  python -m pip install --upgrade --force-reinstall --prefer-binary -r {requirements.name}",
        f"  python -m pip install --no-deps -e {project_root}",
        f"  sudo apt-get update && sudo apt-get install -y {packages}",
        "",
        "Then start with:",
        "  bash scripts/run_app.sh",
    ]
    return "\n".join(lines)


def _prepend_env_path(name: str, value: Path) -> None:
    text = str(value)
    current = os.environ.get(name, "")
    parts = [part for part in current.split(os.pathsep) if part]
    if text not in parts:
        os.environ[name] = os.pathsep.join([text, *parts])


def _distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _first_distribution_version(version_lookup: Callable[[str], str | None], *names: str) -> str | None:
    for name in names:
        version = version_lookup(name)
        if version is not None:
            return version
    return None


def _version_in_range(version: str, *, lower: tuple[int, int], upper: tuple[int, int]) -> bool:
    parsed = _major_minor(version)
    if parsed is None:
        return False
    return lower <= parsed < upper


def _major_minor(version: str) -> tuple[int, int] | None:
    parts: list[int] = []
    for chunk in version.replace("-", ".").split("."):
        if not chunk:
            continue
        digits = ""
        for char in chunk:
            if not char.isdigit():
                break
            digits += char
        if digits:
            parts.append(int(digits))
        if len(parts) == 2:
            return parts[0], parts[1]
    return None
