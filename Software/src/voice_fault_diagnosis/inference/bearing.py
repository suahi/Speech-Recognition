from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np

from voice_fault_diagnosis.audio_io import AudioSourceInfo, load_audio
from voice_fault_diagnosis.config import BearingAppConfig, BearingModelConfig
from voice_fault_diagnosis.models import CLASS_IDS, BearingPredictionResult


FEATURE_VERSION = "bearing_acoustic_v1"
REMAINING_LIFE_ALGORITHM_VERSION = "acoustic_degradation_v1"
CLASS_RISK_WEIGHTS = {
    "healthy": 0.02,
    "bearing_damage": 0.68,
    "clearance": 0.92,
}


@dataclass(frozen=True)
class AudioFeatures:
    values: np.ndarray
    feature_names: tuple[str, ...]


class BearingDiagnosticEngine:
    """Lazy, CPU-only three-class bearing diagnosis with acoustic life estimation."""

    def __init__(self, config: BearingAppConfig | BearingModelConfig) -> None:
        self.config = config.model if isinstance(config, BearingAppConfig) else config
        self._classifier: Any | None = None
        self._feature_config: dict[str, Any] | None = None

    @property
    def model_metadata(self) -> dict[str, Any]:
        return {
            "model_name": "bearing_random_forest",
            "model_version": self.config.model_version,
            "classifier_path": str(self.config.classifier_path),
            "feature_config_path": str(self.config.feature_config_path),
            "remaining_life_algorithm_version": REMAINING_LIFE_ALGORITHM_VERSION,
        }

    def prepare(self) -> None:
        if self._classifier is not None:
            return
        try:
            import joblib
        except ImportError as exc:  # pragma: no cover - package dependency
            raise RuntimeError("缺少模型依赖 joblib，请重新安装项目依赖。") from exc
        for path, description in (
            (self.config.classifier_path, "分类模型"),
            (self.config.feature_config_path, "特征配置"),
        ):
            if not path.is_file():
                raise FileNotFoundError(f"缺少{description}：{path}。请先运行训练命令。")
        try:
            feature_config = json.loads(self.config.feature_config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError("特征配置文件损坏，无法加载模型。") from exc
        names = feature_config.get("feature_names") if isinstance(feature_config, dict) else None
        if not isinstance(names, list) or not names:
            raise ValueError("特征配置缺少 feature_names。")
        classifier = joblib.load(self.config.classifier_path)
        if not hasattr(classifier, "predict_proba"):
            raise ValueError("轴承模型文件格式无效，请重新训练。")
        self._classifier = classifier
        self._feature_config = feature_config

    def predict(self, audio_path: str | Path) -> BearingPredictionResult:
        samples, source_info = load_audio(audio_path)
        return self.predict_samples(samples, source_info=source_info, source_path=audio_path)

    def predict_samples(
        self,
        samples: np.ndarray,
        *,
        source_info: AudioSourceInfo,
        source_path: str | Path | None = None,
    ) -> BearingPredictionResult:
        self.prepare()
        assert self._classifier is not None
        assert self._feature_config is not None
        segment_seconds = float(self._feature_config.get("segment_seconds", 5.0))
        feature_names = tuple(str(name) for name in self._feature_config["feature_names"])
        segments = segment_audio(samples, source_info.decoded_sample_rate, segment_seconds)
        extracted = [extract_features(segment, source_info.decoded_sample_rate) for segment in segments]
        feature_rows = np.vstack([item.values for item in extracted])
        if tuple(feature_names) != extracted[0].feature_names:
            raise ValueError("当前特征实现与已训练模型不匹配，请重新训练模型。")

        probabilities_by_segment = np.asarray(self._classifier.predict_proba(feature_rows), dtype=float)
        class_order = [str(value) for value in self._classifier.classes_]
        probability_map = {
            class_id: float(np.mean(probabilities_by_segment[:, class_order.index(class_id)]))
            if class_id in class_order
            else 0.0
            for class_id in CLASS_IDS
        }
        class_id = max(CLASS_IDS, key=lambda item: probability_map[item])
        anomaly = acoustic_anomaly(feature_rows, self._feature_config)
        remaining_life_percent, remaining_life_level, class_risk, anomaly_risk = estimate_remaining_life(
            probability_map,
            anomaly,
            self._feature_config,
        )
        top_k = sorted(probability_map.items(), key=lambda item: item[1], reverse=True)
        metadata = {
            **self.model_metadata,
            "source_path": str(Path(source_path).resolve()) if source_path is not None else None,
            "audio": source_info.to_dict(),
            "segment_seconds": segment_seconds,
            "segment_count": len(segments),
            "feature_version": FEATURE_VERSION,
            "acoustic_anomaly": anomaly,
            "classification_risk": class_risk,
            "acoustic_anomaly_risk": anomaly_risk,
            "remaining_life_percent": remaining_life_percent,
            "top_k": [
                {"class_id": item, "category_name": self.config.labels[item], "probability": value}
                for item, value in top_k
            ],
        }
        return BearingPredictionResult(
            model_name="bearing_random_forest",
            class_id=class_id,
            category_name=self.config.labels[class_id],
            confidence=probability_map[class_id],
            probabilities=probability_map,
            remaining_life_percent=remaining_life_percent,
            remaining_life_level=remaining_life_level,
            segment_count=len(segments),
            metadata=metadata,
        )


def segment_audio(samples: np.ndarray, sample_rate: int, segment_seconds: float = 5.0) -> list[np.ndarray]:
    values = np.asarray(samples, dtype=np.float32).reshape(-1)
    if values.size == 0:
        raise ValueError("音频没有可用于分析的样本。")
    target = max(1, int(round(sample_rate * segment_seconds)))
    segments: list[np.ndarray] = []
    for start in range(0, values.size, target):
        segment = values[start : start + target]
        if segment.size < target:
            segment = np.pad(segment, (0, target - segment.size))
        segments.append(segment.astype(np.float32, copy=False))
    return segments


def extract_features(samples: np.ndarray, sample_rate: int = 16_000) -> AudioFeatures:
    """Small CPU-friendly acoustic vector: MFCC, energy and spectral statistics."""

    values = np.nan_to_num(np.asarray(samples, dtype=np.float32).reshape(-1), nan=0.0, posinf=0.0, neginf=0.0)
    if values.size < 32:
        values = np.pad(values, (0, 32 - values.size))
    try:
        import librosa
    except ImportError as exc:  # pragma: no cover - declared project dependency
        raise RuntimeError("缺少特征依赖 librosa，请重新安装项目依赖。") from exc
    n_fft = min(1024, max(64, 2 ** int(np.floor(np.log2(values.size)))))
    hop = max(32, n_fft // 4)
    mfcc = librosa.feature.mfcc(y=values, sr=sample_rate, n_mfcc=13, n_fft=n_fft, hop_length=hop)
    spectral = {
        "spectral_centroid": librosa.feature.spectral_centroid(y=values, sr=sample_rate, n_fft=n_fft, hop_length=hop)[0],
        "spectral_bandwidth": librosa.feature.spectral_bandwidth(y=values, sr=sample_rate, n_fft=n_fft, hop_length=hop)[0],
        "spectral_rolloff": librosa.feature.spectral_rolloff(y=values, sr=sample_rate, n_fft=n_fft, hop_length=hop)[0],
        "spectral_flatness": librosa.feature.spectral_flatness(y=values, n_fft=n_fft, hop_length=hop)[0],
        "zero_crossing_rate": librosa.feature.zero_crossing_rate(values, frame_length=n_fft, hop_length=hop)[0],
        "rms": librosa.feature.rms(y=values, frame_length=n_fft, hop_length=hop)[0],
    }
    names: list[str] = []
    output: list[float] = []
    for index in range(13):
        column = mfcc[index]
        names.extend((f"mfcc_{index + 1}_mean", f"mfcc_{index + 1}_std"))
        output.extend((_finite_mean(column), _finite_std(column)))
    for name, column in spectral.items():
        names.extend((f"{name}_mean", f"{name}_std"))
        output.extend((_finite_mean(column), _finite_std(column)))
    centered = values - _finite_mean(values)
    standard_deviation = max(_finite_std(values), 1e-8)
    normalized = centered / standard_deviation
    names.extend(("amplitude_mean", "amplitude_std", "amplitude_kurtosis", "peak_factor", "crest_factor"))
    rms_value = max(float(np.sqrt(np.mean(np.square(values)))), 1e-8)
    output.extend(
        (
            _finite_mean(np.abs(values)),
            standard_deviation,
            float(np.mean(np.power(normalized, 4))),
            float(np.max(np.abs(values))),
            float(np.max(np.abs(values)) / rms_value),
        )
    )
    return AudioFeatures(np.asarray(output, dtype=np.float32), tuple(names))


def build_anomaly_baseline(features: np.ndarray, feature_names: tuple[str, ...]) -> dict[str, Any]:
    preferred = ("rms_mean", "spectral_centroid_mean", "spectral_flatness_mean", "zero_crossing_rate_mean", "amplitude_kurtosis")
    indices = [feature_names.index(name) for name in preferred if name in feature_names]
    if not indices:
        indices = list(range(min(5, len(feature_names))))
    selected = np.asarray(features, dtype=float)[:, indices]
    median = np.median(selected, axis=0)
    mad = np.median(np.abs(selected - median), axis=0)
    scale = np.maximum(mad * 1.4826, 1e-6)
    return {
        "anomaly_feature_names": [feature_names[index] for index in indices],
        "anomaly_median": median.astype(float).tolist(),
        "anomaly_scale": scale.astype(float).tolist(),
    }


def acoustic_anomaly(features: np.ndarray, feature_config: dict[str, Any]) -> float:
    names = [str(name) for name in feature_config["feature_names"]]
    selected_names = [str(name) for name in feature_config["anomaly_feature_names"]]
    indices = [names.index(name) for name in selected_names]
    median = np.asarray(feature_config["anomaly_median"], dtype=float)
    scale = np.maximum(np.asarray(feature_config["anomaly_scale"], dtype=float), 1e-6)
    values = np.asarray(features, dtype=float)[:, indices]
    score = np.mean(np.abs((values - median) / scale), axis=1)
    return float(np.median(np.nan_to_num(score, nan=0.0, posinf=100.0, neginf=0.0)))


def estimate_remaining_life(
    probabilities: dict[str, float],
    anomaly: float,
    feature_config: dict[str, Any],
) -> tuple[float, str, float, float]:
    """Return a deterministic acoustic degradation estimate with two decimals.

    No lifetime labels are available in the supplied data, so this is a fixed
    calculation over classifier confidence and deviation from the healthy
    acoustic baseline rather than a trained RUL regressor.
    """

    healthy_reference = max(float(feature_config.get("healthy_anomaly_reference", 1.0)), 1e-6)
    classification_risk = float(
        sum(max(0.0, float(probabilities.get(class_id, 0.0))) * weight for class_id, weight in CLASS_RISK_WEIGHTS.items())
    )
    acoustic_anomaly_risk = float(1.0 - np.exp(-max(0.0, float(anomaly)) / healthy_reference))
    total_degradation = 0.72 * classification_risk + 0.28 * acoustic_anomaly_risk
    remaining_life_percent = round(float(np.clip(100.0 * (1.0 - total_degradation), 3.0, 99.80)), 2)
    if remaining_life_percent >= 70.0:
        level = "健康"
    elif remaining_life_percent >= 40.0:
        level = "预警"
    else:
        level = "检修"
    return remaining_life_percent, level, classification_risk, acoustic_anomaly_risk


def _finite_mean(values: np.ndarray) -> float:
    return float(np.mean(np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)))


def _finite_std(values: np.ndarray) -> float:
    return float(np.std(np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)))
