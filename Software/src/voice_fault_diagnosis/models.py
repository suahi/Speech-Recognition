from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


CLASS_IDS = ("healthy", "bearing_damage", "clearance")


@dataclass(frozen=True)
class BearingPredictionResult:
    """One deterministic bearing diagnosis produced from an imported audio file."""

    model_name: str
    class_id: str
    category_name: str
    confidence: float
    probabilities: dict[str, float]
    health_index: int
    health_level: str
    segment_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Kept as the public result name used by the pipeline contract.
PredictionResult = BearingPredictionResult
