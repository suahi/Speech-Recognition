#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
VENV_DIR="${VENV_DIR:-${PROJECT_ROOT}/.venv}"
SKIP_APT="${SKIP_APT:-0}"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements-lubancat-aarch64.txt"

system_name="$(uname -s)"
machine_name="$(uname -m)"
case "${machine_name}" in
  aarch64|arm64)
    is_arm64=1
    ;;
  *)
    is_arm64=0
    ;;
esac

if [[ "${system_name}" != "Linux" || "${is_arm64}" != "1" ]]; then
  echo "Warning: this installer targets LubanCat ARM64 Linux; detected ${system_name}/${machine_name}."
fi

if [[ "${SKIP_APT}" != "1" ]] && command -v apt-get >/dev/null 2>&1; then
  apt_cmd=(apt-get)
  if [[ "$(id -u)" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      apt_cmd=(sudo apt-get)
    else
      apt_cmd=()
      echo "Skipping system packages because sudo is unavailable. Rerun as root if Qt cannot start."
    fi
  fi

  if [[ "${#apt_cmd[@]}" -gt 0 ]]; then
    "${apt_cmd[@]}" update
    DEBIAN_FRONTEND=noninteractive "${apt_cmd[@]}" install -y \
      python3-pip \
      python3-venv \
      libasound2 \
      libdbus-1-3 \
      libegl1 \
      libgl1 \
      libgomp1 \
      libsndfile1 \
      libxkbcommon-x11-0 \
      libxcb-cursor0 \
      libxcb-icccm4 \
      libxcb-image0 \
      libxcb-keysyms1 \
      libxcb-randr0 \
      libxcb-render-util0 \
      libxcb-shape0 \
      libxcb-xfixes0 \
      libxcb-xinerama0 \
      libxcb-xinput0
  fi
else
  echo "Skipping apt packages. Set SKIP_APT=0 on Debian/Ubuntu if Qt platform plugins are missing."
fi

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  if [[ ! -d "${VENV_DIR}" ]]; then
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  fi
  # shellcheck source=/dev/null
  source "${VENV_DIR}/bin/activate"
fi

python -m pip install --upgrade pip setuptools wheel
if [[ "${system_name}" == "Linux" && "${is_arm64}" == "1" ]]; then
  python -m pip install --upgrade --force-reinstall --prefer-binary \
    "numpy>=1.26.0,<2.0" \
    "scipy>=1.11.4,<1.13" \
    "shiboken6==6.7.3" \
    "PySide6_Essentials==6.7.3"
  python -m pip install --upgrade --prefer-binary -r "${REQUIREMENTS_FILE}"
  python -m pip install --no-deps -e "${PROJECT_ROOT}"
else
  python -m pip install --prefer-binary -e "${PROJECT_ROOT}[desktop,test]"
fi

python - <<'PY'
import platform

import librosa
import numpy
import scipy
import torch
from PySide6 import QtCore, QtWidgets

print("Dependency check:")
print(f"  python={platform.python_version()} machine={platform.machine()}")
print(f"  numpy={numpy.__version__}")
print(f"  scipy={scipy.__version__}")
print(f"  librosa={librosa.__version__}")
print(f"  torch={torch.__version__}")
print(f"  Qt={QtCore.qVersion()} widgets={QtWidgets.__name__}")
PY

cat <<'EOF'

Install finished.

Before running acquisition:
1. Put the VK701N-SD and LubanCat on the same network.
2. Close the vendor DAQ application on other machines.
3. Run: bash scripts/probe_vk701n.sh
4. If recvLen is stable and non-zero, run: bash scripts/run_app.sh

Useful overrides:
  PYTHON=/path/to/python3 bash scripts/install_lubancat.sh
  VENV_DIR=/home/cat/oilstream-venv bash scripts/install_lubancat.sh
  SKIP_APT=1 bash scripts/install_lubancat.sh

To repair an existing conda/miniforge environment such as (oil):
  python -m pip install --upgrade --force-reinstall --prefer-binary -r requirements-lubancat-aarch64.txt
  python -m pip install --no-deps -e .
EOF
