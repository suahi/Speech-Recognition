from __future__ import annotations

import json
from pathlib import Path
import pickle
from typing import Any

import numpy as np

from voice_fault_diagnosis.config import load_json
from voice_fault_diagnosis.models import PredictionResult
from voice_fault_diagnosis.paths import CONFIG_DIR, LEGACY_MODEL_DIR


class LegacyCnnEngine:
    def __init__(
        self,
        model_dir: str | Path = LEGACY_MODEL_DIR,
        manifest_path: str | Path | None = None,
        labels_path: str | Path | None = None,
    ) -> None:
        self.model_dir = Path(model_dir).resolve()
        self.manifest_path = Path(manifest_path).resolve() if manifest_path else self.model_dir / "manifest.json"
        self.manifest = load_json(self.manifest_path, {})
        self.model_path = (self.model_dir / self.manifest.get("model_path", "best_model_cnn.pt")).resolve()
        self.mean_std_path = (self.model_dir / self.manifest.get("mean_std_path", "mean_std.pkl")).resolve()
        configured_labels = labels_path or self.manifest.get("labels_path") or (CONFIG_DIR / "labels.json")
        self.labels_path = self._resolve_labels_path(configured_labels)
        self.labels = self._load_labels()
        self._model = None
        self._mean = None
        self._std = None

    def predict(self, legacy_input: bytes) -> PredictionResult:
        if not legacy_input:
            raise ValueError("legacy_input is empty")
        self._ensure_loaded()
        features, raw_samples, real, imaginary = extract_legacy_features(
            legacy_input,
            sample_rate=int(self.manifest.get("sample_rate", 50000)),
            n_fft=int(self.manifest.get("feature_n_fft", 1024)),
        )
        normalized = (features - self._mean) / self._std

        import torch
        import torch.nn.functional as F

        tensor = torch.tensor(np.asarray([normalized]), dtype=torch.float32).unsqueeze(1)
        with torch.no_grad():
            logits = self._model(tensor)
            probabilities = F.softmax(logits, dim=1).cpu().numpy()[0].astype(float)
        class_index = int(np.argmax(probabilities))
        confidence = float(probabilities[class_index])
        top_indices = np.argsort(probabilities)[::-1][: min(5, probabilities.size)]
        top_k = [
            {
                "class_index": int(index),
                "label": self._label_for(int(index)),
                "confidence": float(probabilities[int(index)]),
            }
            for index in top_indices
        ]
        return PredictionResult(
            model_name=str(self.manifest.get("name", "legacy_cnn")),
            class_index=class_index,
            label=self._label_for(class_index),
            confidence=confidence,
            probabilities=[float(item) for item in probabilities],
            top_k=top_k,
            metadata={
                "feature_shape": list(features.shape),
                "raw_sample_count": int(raw_samples.size),
                "stft_real_count": int(real.size),
                "stft_imaginary_count": int(imaginary.size),
                "model_path": str(self.model_path),
                "mean_std_path": str(self.mean_std_path),
                "labels_path": str(self.labels_path),
            },
        )

    def _ensure_loaded(self) -> None:
        if self._model is None:
            import audiomodel  # noqa: F401
            import torch

            self._model = torch.load(self.model_path, map_location="cpu", weights_only=False)
            self._model.eval()
        if self._mean is None or self._std is None:
            with self.mean_std_path.open("rb") as handle:
                mean_std = pickle.load(handle)
            self._mean = np.asarray(mean_std["mean"], dtype=np.float32)
            self._std = np.asarray(mean_std["std"], dtype=np.float32)
            self._std = np.where(np.abs(self._std) < 1e-9, 1.0, self._std)

    def _resolve_labels_path(self, configured: str | Path) -> Path:
        path = Path(configured)
        if path.is_absolute():
            return path
        candidate = (self.model_dir / path).resolve()
        if candidate.exists():
            return candidate
        return (CONFIG_DIR / path).resolve()

    def _load_labels(self) -> list[str]:
        labels = load_json(self.labels_path, [])
        if not isinstance(labels, list) or not labels:
            labels = [f"class_{index}" for index in range(int(self.manifest.get("num_classes", 10)))]
        return [str(item) for item in labels]

    def _label_for(self, class_index: int) -> str:
        if 0 <= class_index < len(self.labels):
            return self.labels[class_index]
        return f"class_{class_index}"


def extract_legacy_features(
    raw_bytes: bytes,
    sample_rate: int = 50000,
    n_fft: int = 1024,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    import librosa

    y = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32)
    mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sample_rate, n_mfcc=36, n_fft=n_fft).T, axis=0)
    real = np.real(
        librosa.stft(y, n_fft=128, hop_length=None, window="hann", center=True, pad_mode="reflect")
    ).flatten()
    imaginary = np.imag(
        librosa.stft(y, n_fft=128, hop_length=None, window="hann", center=True, pad_mode="reflect")
    ).flatten()
    mel = np.mean(
        librosa.feature.melspectrogram(y=y, sr=sample_rate, n_mels=36, fmax=sample_rate // 2, n_fft=n_fft).T,
        axis=0,
    )
    chroma_stft = np.mean(librosa.feature.chroma_stft(y=y, sr=sample_rate, n_chroma=36, n_fft=n_fft).T, axis=0)
    chroma_cq = np.mean(librosa.feature.chroma_cqt(y=y, sr=sample_rate, n_chroma=36).T, axis=0)
    chroma_cens = np.mean(librosa.feature.chroma_cens(y=y, sr=sample_rate, n_chroma=36).T, axis=0)
    features = np.reshape(np.vstack((mfccs, mel, chroma_stft, chroma_cq, chroma_cens)), (36, 5))
    return features.astype(np.float32), y, real.astype(np.float32), imaginary.astype(np.float32)
