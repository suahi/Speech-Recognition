#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "${PROJECT_ROOT}[desktop,test]"

cat <<'EOF'

Install finished.

Before running acquisition:
1. Put the VK701N-SD and LubanCat on the same network.
2. Close the vendor DAQ application on other machines.
3. Run: bash scripts/probe_vk701n.sh
4. If recvLen is stable and non-zero, run: bash scripts/run_app.sh

If torch is not available for your LubanCat image, install a matching ARM64 CPU
wheel first, then rerun this script.
EOF
