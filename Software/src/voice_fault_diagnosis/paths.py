from __future__ import annotations

from pathlib import Path


SOFTWARE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = SOFTWARE_ROOT / "configs"
BEARING_CONFIG_PATH = CONFIG_DIR / "bearing_demo.json"
DATA_DIR = SOFTWARE_ROOT / "data"
RECORDS_DIR = DATA_DIR / "records"
BEARING_MODEL_DIR = SOFTWARE_ROOT / "models" / "bearing"
