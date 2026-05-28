"""Base anomaly-detection interface for future sensing workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class AnomalyDetector(ABC):
    @abstractmethod
    def fit(self, features: pd.DataFrame) -> None:
        """Train or calibrate an anomaly detector."""

    @abstractmethod
    def score(self, features: pd.DataFrame) -> pd.DataFrame:
        """Return anomaly scores for one or more feature vectors."""

