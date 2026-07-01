from __future__ import annotations

from pathlib import Path


SOFTWARE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = SOFTWARE_ROOT / "configs"
DATA_DIR = SOFTWARE_ROOT / "data"
RECORDS_DIR = DATA_DIR / "records"
VENDOR_VK701N_DIR = SOFTWARE_ROOT / "vendor" / "vk701n"
LEGACY_MODEL_DIR = SOFTWARE_ROOT / "models" / "legacy_cnn"
