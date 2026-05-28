"""Extensible placeholder interfaces for future machine-learning support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(slots=True)
class InferenceRequest:
    features: pd.DataFrame
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InferenceResult:
    labels: list[str]
    scores: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class FeatureExtractor(ABC):
    @abstractmethod
    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Convert dielectric spectra into machine-learning features."""


class MaterialClassifier(ABC):
    @abstractmethod
    def predict(self, request: InferenceRequest) -> InferenceResult:
        """Predict material classes for a feature matrix."""


class AnomalyDetector(ABC):
    @abstractmethod
    def score(self, request: InferenceRequest) -> InferenceResult:
        """Generate anomaly scores for unseen measurements."""

