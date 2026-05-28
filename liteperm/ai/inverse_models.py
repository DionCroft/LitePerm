"""Architecture placeholders for AI-assisted inverse modelling."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class NeuralInverseModel(ABC):
    @abstractmethod
    def fit(self, features: pd.DataFrame, targets: pd.DataFrame) -> None:
        """Train a neural inverse model."""

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """Predict material properties from RF features."""


class PhysicsInformedModel(ABC):
    @abstractmethod
    def fit(self, features: pd.DataFrame, targets: pd.DataFrame) -> None:
        """Train a physics-informed inverse model."""

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """Predict material properties with physics-informed constraints."""


class SurrogateModel(ABC):
    @abstractmethod
    def fit(self, features: pd.DataFrame, targets: pd.DataFrame) -> None:
        """Train a fast surrogate model for forward or inverse estimation."""

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """Return surrogate predictions."""


class HybridPhysicsAIModel(ABC):
    @abstractmethod
    def fit(self, features: pd.DataFrame, targets: pd.DataFrame) -> None:
        """Train a hybrid model combining learned and physics-based components."""

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """Predict inverse-model outputs using a hybrid architecture."""

