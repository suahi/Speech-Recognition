from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from voice_fault_diagnosis.models import CLASS_IDS
from voice_fault_diagnosis.paths import BEARING_CONFIG_PATH, SOFTWARE_ROOT


EXPECTED_CLASS_IDS = CLASS_IDS


class BearingConfigError(ValueError):
    """Raised when the offline bearing application configuration is invalid."""


@dataclass(frozen=True)
class BearingModelConfig:
    classifier_path: Path
    health_index_path: Path
    feature_config_path: Path
    model_version: str
    labels: dict[str, str]


@dataclass(frozen=True)
class BearingAppConfig:
    target_sample_rate: int
    segment_seconds: float
    model: BearingModelConfig
    source_path: Path


def load_bearing_config(path: str | Path = BEARING_CONFIG_PATH) -> BearingAppConfig:
    source_path = Path(path).resolve()
    if not source_path.is_file():
        raise BearingConfigError(f"找不到轴承诊断配置文件：{source_path}")
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BearingConfigError(f"轴承诊断配置不是有效 JSON：{source_path}") from exc
    if not isinstance(data, dict):
        raise BearingConfigError("轴承诊断配置根节点必须是对象。")

    audio_data = _required_object(data, "audio")
    model_data = _required_object(data, "model")
    sample_rate = int(_positive_number(audio_data.get("target_sample_rate"), "audio.target_sample_rate"))
    segment_seconds = _positive_number(audio_data.get("segment_seconds"), "audio.segment_seconds")

    labels_data = _required_object(model_data, "labels")
    if set(labels_data) != set(EXPECTED_CLASS_IDS):
        raise BearingConfigError("model.labels 必须完整配置 healthy、bearing_damage、clearance。")
    labels = {code: str(labels_data[code]).strip() for code in EXPECTED_CLASS_IDS}
    if any(not name for name in labels.values()):
        raise BearingConfigError("model.labels 中的中文名称不能为空。")

    classifier_path = _project_path(model_data.get("classifier_path"), "model.classifier_path")
    health_index_path = _project_path(model_data.get("health_index_path"), "model.health_index_path")
    feature_config_path = _project_path(model_data.get("feature_config_path"), "model.feature_config_path")
    missing = [str(item) for item in (classifier_path, health_index_path, feature_config_path) if not item.is_file()]
    if missing:
        raise BearingConfigError("缺少轴承模型文件，请先运行训练命令：" + "，".join(missing))
    model_version = str(model_data.get("model_version", "")).strip()
    if not model_version:
        raise BearingConfigError("model.model_version 不能为空。")

    return BearingAppConfig(
        target_sample_rate=sample_rate,
        segment_seconds=segment_seconds,
        model=BearingModelConfig(
            classifier_path=classifier_path,
            health_index_path=health_index_path,
            feature_config_path=feature_config_path,
            model_version=model_version,
            labels=labels,
        ),
        source_path=source_path,
    )


def _required_object(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise BearingConfigError(f"{key} 必须是对象。")
    return value


def _positive_number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise BearingConfigError(f"{name} 必须是正数。") from exc
    if number <= 0:
        raise BearingConfigError(f"{name} 必须大于 0。")
    return number


def _project_path(value: Any, name: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise BearingConfigError(f"{name} 必须是项目内的文件路径。")
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (SOFTWARE_ROOT / candidate).resolve()
    _require_project_file(resolved, name)
    return resolved


def _require_project_file(path: Path, name: str) -> None:
    try:
        path.relative_to(SOFTWARE_ROOT)
    except ValueError as exc:
        raise BearingConfigError(f"{name} 必须位于电脑端项目目录内。") from exc
    if not path.is_file():
        raise BearingConfigError(f"{name} 指向的文件不存在：{path}")
