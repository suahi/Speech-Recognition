from __future__ import annotations

from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
from train_bearing_models import label_for_file, split_by_file


def test_filename_labels_follow_specification() -> None:
    assert label_for_file("好1.m4a") == "healthy"
    assert label_for_file("轴承损伤7.m4a") == "bearing_damage"
    assert label_for_file("间隙1.m4a") == "clearance"
    assert label_for_file("未标注.wav") is None


def test_fixed_split_is_file_level_and_has_expected_42_11_counts() -> None:
    files = [(Path(f"好/好{index}.m4a"), "healthy") for index in range(9)]
    files += [(Path(f"损伤/轴承损伤{index}.m4a"), "bearing_damage") for index in range(42)]
    files += [(Path(f"间隙/间隙{index}.m4a"), "clearance") for index in range(2)]
    first = split_by_file(files, seed=20_260_920)
    second = split_by_file(files, seed=20_260_920)
    assert first == second
    assert len(first["train"]) == 42
    assert len(first["test"]) == 11
    assert not {path for path, _ in first["train"]} & {path for path, _ in first["test"]}
