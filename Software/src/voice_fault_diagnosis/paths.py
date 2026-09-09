from __future__ import annotations

from pathlib import Path


SOFTWARE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = SOFTWARE_ROOT / "configs"
PC_CONFIG_PATH = CONFIG_DIR / "pc_direct.json"
DATA_DIR = SOFTWARE_ROOT / "data"
RECORDS_DIR = DATA_DIR / "records"
VENDOR_VK701N_DIR = SOFTWARE_ROOT / "vendor" / "vk701n"
WAV_CNN_MODEL_DIR = SOFTWARE_ROOT / "models" / "wav_cnn"
