#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export LD_LIBRARY_PATH="${PROJECT_ROOT}/vendor/vk701n:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}"

cd "${PROJECT_ROOT}"
python run_app.py
