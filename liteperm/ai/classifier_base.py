"""Base classifier interface for future material-learning workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class MaterialClassifier(ABC):
    @abstractmethod
    def fit(self, features: pd.DataFrame, labels: pd.Series) -> None:
        """Train a classifier on feature vectors."""

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """Return predicted labels and confidence scores."""

