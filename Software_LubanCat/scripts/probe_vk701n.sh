#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export LD_LIBRARY_PATH="${PROJECT_ROOT}/vendor/vk701n:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}"

cd "${PROJECT_ROOT}"
python tools/probe_vk701n.py \
  --profile legacy \
  --library vendor/vk701n/libVK70XNMC_DAQ_SHARED.so \
  --port 8234 \
  --device-no 0 \
  --sample-rate 50000 \
  --bit-mode 24 \
  --input-range-volts 5.0 \
  --read-points 5000 \
  --blocking-timeout-ms 1000
