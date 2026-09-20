from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import sys
from typing import Any

import numpy as np


SOFTWARE_ROOT = Path(__file__).resolve().parents[1]
SRC = SOFTWARE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voice_fault_diagnosis.audio_io import SUPPORTED_AUDIO_SUFFIXES, load_audio
from voice_fault_diagnosis.inference.bearing import (
    FEATURE_VERSION,
    HEALTH_BANDS,
    HEALTH_DISCLAIMER,
    acoustic_anomaly,
    build_anomaly_baseline,
    extract_features,
    segment_audio,
)
from voice_fault_diagnosis.models import CLASS_IDS


SEED = 20_260_920
SEGMENT_SECONDS = 5.0
TARGET_SAMPLE_RATE = 16_000
MODEL_VERSION = "bearing_rf_v1"


def main() -> int:
    arguments = _parse_arguments()
    data_root = Path(arguments.data_root).resolve()
    output_dir = Path(arguments.output_dir).resolve()
    if not data_root.is_dir():
        raise SystemExit(f"数据目录不存在：{data_root}")
    files = discover_labeled_files(data_root)
    split = split_by_file(files, seed=SEED)
    train_rows, feature_names = build_feature_rows(split["train"], data_root)
    test_rows, test_feature_names = build_feature_rows(split["test"], data_root)
    if feature_names != test_feature_names:
        raise RuntimeError("训练与测试特征定义不一致。")
    train_values = np.vstack([row["features"] for row in train_rows])
    train_labels = np.asarray([row["label"] for row in train_rows], dtype=object)
    healthy_values = train_values[train_labels == "healthy"]
    if healthy_values.size == 0:
        raise RuntimeError("训练集缺少健康音频，不能构建演示性健康指数。")
    baseline = build_anomaly_baseline(healthy_values, feature_names)
    feature_config: dict[str, Any] = {
        "feature_version": FEATURE_VERSION,
        "target_sample_rate": TARGET_SAMPLE_RATE,
        "segment_seconds": SEGMENT_SECONDS,
        "feature_names": list(feature_names),
        "health_bands": {key: list(value) for key, value in HEALTH_BANDS.items()},
        "health_disclaimer": HEALTH_DISCLAIMER,
        "random_seed": SEED,
        **baseline,
    }
    train_scores = np.asarray([acoustic_anomaly(row["features"][None, :], feature_config) for row in train_rows])
    health_targets = build_demo_health_targets(train_labels, train_scores, train_rows)
    feature_config["anomaly_references"] = anomaly_references(train_labels, train_scores)

    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

    classifier = RandomForestClassifier(
        n_estimators=400,
        class_weight="balanced_subsample",
        max_features="sqrt",
        random_state=SEED,
        n_jobs=-1,
    )
    health_regressor = RandomForestRegressor(
        n_estimators=400,
        max_features="sqrt",
        random_state=SEED + 1,
        n_jobs=-1,
    )
    classifier.fit(train_values, train_labels)
    health_regressor.fit(train_values, health_targets)

    metrics = evaluate_by_file(
        classifier,
        health_regressor,
        test_rows,
        feature_config,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    import joblib

    joblib.dump(classifier, output_dir / "bearing_classifier.joblib")
    joblib.dump(health_regressor, output_dir / "bearing_health_index.joblib")
    (output_dir / "feature_config.json").write_text(
        json.dumps(feature_config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "training_metrics.json").write_text(
        json.dumps(
            {
                "model_version": MODEL_VERSION,
                "random_seed": SEED,
                "data_root_not_recorded": True,
                "file_counts": file_counts(split),
                "segment_counts": {"train": len(train_rows), "test": len(test_rows)},
                "classification": metrics,
                "health_index_disclaimer": HEALTH_DISCLAIMER,
                "limitations": [
                    "健康指数为演示性百分比，不是以小时计的真实剩余寿命。",
                    "间隙异常原始文件仅 2 段，测试集中仅 1 段，该类别泛化结论仅供演示。",
                    "训练/测试按原始文件隔离；5 秒片段只用于各自分区的特征扩充。",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_manifest(output_dir / "test_manifest.csv", split["test"], data_root)
    write_manifest(output_dir / "train_manifest.csv", split["train"], data_root)
    print(json.dumps({"output_dir": str(output_dir), "file_counts": file_counts(split), "metrics": metrics}, ensure_ascii=False))
    return 0


def discover_labeled_files(data_root: Path) -> list[tuple[Path, str]]:
    discovered: list[tuple[Path, str]] = []
    for path in sorted(data_root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_AUDIO_SUFFIXES:
            continue
        label = label_for_file(path.name)
        if label is not None:
            discovered.append((path, label))
    counts = {class_id: sum(label == class_id for _, label in discovered) for class_id in CLASS_IDS}
    if counts != {"healthy": 9, "bearing_damage": 42, "clearance": 2}:
        print(f"提示：发现的标签数量为 {counts}（预期数据集为 9/42/2）。")
    if any(count == 0 for count in counts.values()):
        raise RuntimeError(f"缺少至少一个类别的训练音频：{counts}")
    return discovered


def label_for_file(filename: str) -> str | None:
    stem = Path(filename).stem
    if stem.startswith("好"):
        return "healthy"
    if "轴承损伤" in stem:
        return "bearing_damage"
    if "间隙" in stem:
        return "clearance"
    return None


def split_by_file(files: list[tuple[Path, str]], *, seed: int) -> dict[str, list[tuple[Path, str]]]:
    grouped = {class_id: [] for class_id in CLASS_IDS}
    for path, label in files:
        grouped[label].append((path, label))
    train: list[tuple[Path, str]] = []
    test: list[tuple[Path, str]] = []
    for index, class_id in enumerate(CLASS_IDS):
        items = sorted(grouped[class_id], key=lambda item: item[0].as_posix().casefold())
        random.Random(seed + index).shuffle(items)
        test_count = max(1, round(len(items) * 0.20))
        test.extend(items[:test_count])
        train.extend(items[test_count:])
    return {"train": train, "test": test}


def build_feature_rows(files: list[tuple[Path, str]], data_root: Path) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    rows: list[dict[str, Any]] = []
    feature_names: tuple[str, ...] | None = None
    for source_path, label in files:
        samples, _ = load_audio(source_path, target_sample_rate=TARGET_SAMPLE_RATE)
        for segment_index, segment in enumerate(segment_audio(samples, TARGET_SAMPLE_RATE, SEGMENT_SECONDS)):
            extracted = extract_features(segment, TARGET_SAMPLE_RATE)
            if feature_names is None:
                feature_names = extracted.feature_names
            elif feature_names != extracted.feature_names:
                raise RuntimeError("特征名称不稳定，无法训练。")
            rows.append(
                {
                    "features": extracted.values,
                    "label": label,
                    "relative_path": source_path.relative_to(data_root).as_posix(),
                    "segment_index": segment_index,
                }
            )
    if not rows or feature_names is None:
        raise RuntimeError("没有可用于训练的音频片段。")
    return rows, feature_names


def build_demo_health_targets(labels: np.ndarray, scores: np.ndarray, rows: list[dict[str, Any]]) -> np.ndarray:
    targets = np.zeros(len(labels), dtype=float)
    for class_id in CLASS_IDS:
        indices = np.flatnonzero(labels == class_id)
        ordered = sorted(indices, key=lambda index: (float(scores[index]), rows[index]["relative_path"], rows[index]["segment_index"]))
        lower, upper = HEALTH_BANDS[class_id]
        if len(ordered) == 1:
            targets[ordered[0]] = (lower + upper) / 2.0
            continue
        for rank, index in enumerate(ordered):
            severity = rank / (len(ordered) - 1)
            targets[index] = upper - severity * (upper - lower)
    return targets


def anomaly_references(labels: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    result: dict[str, float] = {}
    for class_id in CLASS_IDS:
        values = scores[labels == class_id]
        result[class_id] = max(1e-6, float(np.quantile(values, 0.90)))
    return result


def evaluate_by_file(classifier, health_regressor, rows: list[dict[str, Any]], feature_config: dict[str, Any]) -> dict[str, Any]:
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["relative_path"]), []).append(row)
    truth: list[str] = []
    predicted: list[str] = []
    health_indices: list[int] = []
    for relative_path, file_rows in sorted(grouped.items()):
        values = np.vstack([row["features"] for row in file_rows])
        probabilities = classifier.predict_proba(values)
        order = [str(value) for value in classifier.classes_]
        average = probabilities.mean(axis=0)
        class_id = order[int(np.argmax(average))]
        raw = float(np.mean(health_regressor.predict(values)))
        anomaly = acoustic_anomaly(values, feature_config)
        lower, upper = HEALTH_BANDS[class_id]
        reference = max(float(feature_config["anomaly_references"][class_id]), 1e-6)
        calculated = upper - np.clip(anomaly / reference, 0.0, 1.0) * (upper - lower)
        health_indices.append(int(round(np.clip(0.70 * raw + 0.30 * calculated, lower, upper))))
        truth.append(str(file_rows[0]["label"]))
        predicted.append(class_id)
    return {
        "file_count": len(truth),
        "accuracy": float(accuracy_score(truth, predicted)),
        "macro_f1": float(f1_score(truth, predicted, labels=list(CLASS_IDS), average="macro", zero_division=0)),
        "confusion_matrix_labels": list(CLASS_IDS),
        "confusion_matrix": confusion_matrix(truth, predicted, labels=list(CLASS_IDS)).tolist(),
        "per_class": classification_report(truth, predicted, labels=list(CLASS_IDS), output_dict=True, zero_division=0),
        "health_index_min": min(health_indices),
        "health_index_max": max(health_indices),
    }


def file_counts(split: dict[str, list[tuple[Path, str]]]) -> dict[str, Any]:
    return {
        partition: {
            "total": len(items),
            **{class_id: sum(label == class_id for _, label in items) for class_id in CLASS_IDS},
        }
        for partition, items in split.items()
    }


def write_manifest(path: Path, files: list[tuple[Path, str]], data_root: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("relative_path", "label"))
        writer.writeheader()
        for source_path, label in sorted(files, key=lambda item: item[0].as_posix().casefold()):
            writer.writerow({"relative_path": source_path.relative_to(data_root).as_posix(), "label": label})


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="训练轴承三分类与演示性健康指数模型")
    parser.add_argument("--data-root", required=True, help="外部 data_v3 目录；原始音频不会复制到仓库")
    parser.add_argument("--output-dir", default=str(SOFTWARE_ROOT / "models" / "bearing"))
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
