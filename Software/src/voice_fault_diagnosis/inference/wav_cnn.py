from __future__ import annotations

from pathlib import Path
import pickle
from typing import Any

import numpy as np

from voice_fault_diagnosis.config import WavModelConfig
from voice_fault_diagnosis.models import PredictionResult


TARGET_SAMPLE_RATE = 16000
N_FFT = 1024
HOP_LENGTH = 512
N_COEFFICIENTS = 36
FIXED_FRAMES = 1 + 160000 // HOP_LENGTH


class WavCnnEngine:
    """In-process adaptation of suahi/Voice_detection_test inference.py."""

    def __init__(self, config: WavModelConfig) -> None:
        self.config = config
        self._model: Any | None = None
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None
        self._idx_to_code: dict[int, str] = {}

    @property
    def model_metadata(self) -> dict[str, str]:
        return {
            "name": "wav_cnn",
            "model_path": str(self.config.model_path),
            "mean_std_path": str(self.config.mean_std_path),
            "source_revision": self.config.source_revision,
        }

    def prepare(self) -> None:
        if self._model is not None:
            return
        import torch

        checkpoint = torch.load(self.config.model_path, map_location="cpu", weights_only=False)
        if not isinstance(checkpoint, dict) or "state_dict" not in checkpoint:
            raise ValueError("WAV 模型检查点缺少 state_dict。")
        num_classes = int(checkpoint.get("num_classes", 6))
        kind = str(checkpoint.get("kind", "new"))
        if kind != "new" or num_classes != 6:
            raise ValueError(f"仅支持 6 类新版 WAV CNN，当前检查点 kind={kind!r}, num_classes={num_classes}。")

        audio_cnn = _torch_modules()
        model = audio_cnn(in_channels=5, num_classes=num_classes, use_se=bool(checkpoint.get("use_se", False)))
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()
        with self.config.mean_std_path.open("rb") as handle:
            statistics = pickle.load(handle)
        if not isinstance(statistics, dict) or "mean" not in statistics or "std" not in statistics:
            raise ValueError("WAV 标准化文件必须包含 mean 和 std。")
        mean = np.asarray(statistics["mean"], dtype=np.float32)
        std = np.asarray(statistics["std"], dtype=np.float32)
        if mean.shape != (5, N_COEFFICIENTS, 1) or std.shape != mean.shape:
            raise ValueError(f"WAV 标准化形状不匹配：mean={mean.shape}, std={std.shape}。")
        class_to_idx = statistics.get("class_to_idx", {code: index for index, code in enumerate(self.config.labels)})
        if not isinstance(class_to_idx, dict):
            raise ValueError("WAV 标准化文件中的 class_to_idx 无效。")
        idx_to_code = {int(index): str(code) for code, index in class_to_idx.items()}
        if [idx_to_code.get(index) for index in range(num_classes)] != list(self.config.labels):
            raise ValueError("模型类别顺序与 pc_direct.json 的 model.labels 不一致。")

        self._model = model
        self._mean = mean
        self._std = np.where(np.abs(std) < 1e-8, 1.0, std).astype(np.float32)
        self._idx_to_code = idx_to_code

    def predict(self, wav_path: str | Path) -> PredictionResult:
        self.prepare()
        assert self._model is not None and self._mean is not None and self._std is not None
        path = Path(wav_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"待推理 WAV 不存在：{path}")
        features, source_samples = extract_wav_features(path)
        normalized = (features - self._mean) / (self._std + 1e-8)

        import torch

        with torch.no_grad():
            inputs = torch.tensor(normalized, dtype=torch.float32).unsqueeze(0)
            logits = self._model(inputs)
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()[0].astype(float)
        class_index = int(np.argmax(probabilities))
        code = self._idx_to_code[class_index]
        top_indices = np.argsort(probabilities)[::-1]
        top_k = [
            {
                "class_index": int(index),
                "label": self._idx_to_code[int(index)],
                "display_name": self.config.labels[self._idx_to_code[int(index)]],
                "confidence": float(probabilities[int(index)]),
            }
            for index in top_indices
        ]
        metadata = {
            **self.model_metadata,
            "wav_path": str(path),
            "source_sample_count": int(source_samples),
            "target_sample_rate": TARGET_SAMPLE_RATE,
            "feature_shape": list(features.shape),
            "display_name": self.config.labels[code],
        }
        return PredictionResult(
            model_name="wav_cnn",
            class_index=class_index,
            label=code,
            confidence=float(probabilities[class_index]),
            probabilities=[float(value) for value in probabilities],
            top_k=top_k,
            metadata=metadata,
        )


def extract_wav_features(wav_path: str | Path) -> tuple[np.ndarray, int]:
    """Load mono WAV at 16 kHz and reproduce the reference feature pipeline."""

    import librosa

    samples, _ = librosa.load(str(wav_path), sr=TARGET_SAMPLE_RATE, mono=True)
    samples = np.asarray(samples, dtype=np.float32)
    features = _raw_features(samples, librosa)
    return _align_time(features), int(samples.size)


def _raw_features(samples: np.ndarray, librosa: Any) -> list[np.ndarray]:
    return [
        librosa.feature.mfcc(
            y=samples,
            sr=TARGET_SAMPLE_RATE,
            n_mfcc=N_COEFFICIENTS,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
        ),
        librosa.feature.melspectrogram(
            y=samples,
            sr=TARGET_SAMPLE_RATE,
            n_mels=N_COEFFICIENTS,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
        ),
        librosa.feature.chroma_stft(
            y=samples,
            sr=TARGET_SAMPLE_RATE,
            n_chroma=N_COEFFICIENTS,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
        ),
        librosa.feature.chroma_cqt(
            y=samples,
            sr=TARGET_SAMPLE_RATE,
            n_chroma=N_COEFFICIENTS,
            hop_length=HOP_LENGTH,
        ),
        librosa.feature.chroma_cens(
            y=samples,
            sr=TARGET_SAMPLE_RATE,
            n_chroma=N_COEFFICIENTS,
            hop_length=HOP_LENGTH,
        ),
    ]


def _align_time(features: list[np.ndarray]) -> np.ndarray:
    result = np.zeros((5, N_COEFFICIENTS, FIXED_FRAMES), dtype=np.float32)
    for channel, feature in enumerate(features):
        frames = min(feature.shape[1], FIXED_FRAMES)
        result[channel, :, :frames] = feature[:, :frames]
    return result


class SEBlock:  # dynamically derives from nn.Module only when PyTorch is imported below
    pass


def _torch_modules():
    import torch.nn as nn

    class _SEBlock(nn.Module):
        def __init__(self, channels: int, reduction: int = 16) -> None:
            super().__init__()
            self.se = nn.Sequential(
                nn.AdaptiveAvgPool2d(1),
                nn.Flatten(),
                nn.Linear(channels, channels // reduction, bias=False),
                nn.ReLU(inplace=True),
                nn.Linear(channels // reduction, channels, bias=False),
                nn.Sigmoid(),
            )

        def forward(self, values):
            scale = self.se(values).view(values.size(0), values.size(1), 1, 1)
            return values * scale

    class _AudioCNN(nn.Module):
        def __init__(self, in_channels: int = 5, num_classes: int = 6, use_se: bool = False) -> None:
            super().__init__()
            self.relu = nn.LeakyReLU(0.01, inplace=True)
            self.pool = nn.MaxPool2d(2)
            self.gap = nn.AdaptiveAvgPool2d(1)
            self.drop = nn.Dropout(0.3)
            self.conv1 = nn.Conv2d(in_channels, 64, 3, padding=1)
            self.bn1 = nn.BatchNorm2d(64)
            self.conv2 = nn.Conv2d(64, 128, 3, padding=1)
            self.bn2 = nn.BatchNorm2d(128)
            self.conv3 = nn.Conv2d(128, 256, 3, padding=1)
            self.bn3 = nn.BatchNorm2d(256)
            self.conv4 = nn.Conv2d(256, 512, 3, padding=1)
            self.bn4 = nn.BatchNorm2d(512)
            self.se1 = _SEBlock(64) if use_se else None
            self.se2 = _SEBlock(128) if use_se else None
            self.se3 = _SEBlock(256) if use_se else None
            self.se4 = _SEBlock(512) if use_se else None
            self.fc1 = nn.Linear(512, 128)
            self.fc2 = nn.Linear(128, num_classes)

        def forward(self, values):
            values = self.relu(self.bn1(self.conv1(values)))
            if self.se1 is not None:
                values = self.se1(values)
            values = self.pool(self.relu(self.bn2(self.conv2(values))))
            if self.se2 is not None:
                values = self.se2(values)
            values = self.relu(self.bn3(self.conv3(values)))
            if self.se3 is not None:
                values = self.se3(values)
            values = self.pool(self.relu(self.bn4(self.conv4(values))))
            if self.se4 is not None:
                values = self.se4(values)
            values = self.gap(values)
            values = values.flatten(1)
            values = self.drop(values)
            values = self.relu(self.fc1(values))
            return self.fc2(values)

    return _AudioCNN
