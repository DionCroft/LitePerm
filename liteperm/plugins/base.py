"""Base interfaces for transformation plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np

from liteperm.models.core import CalibrationProfile, MaterialSpectrum, MeasurementData, SensorGeometryProfile


@dataclass(slots=True)
class TransformationContext:
    measurement: MeasurementData
    geometry: SensorGeometryProfile
    gamma: np.ndarray
    impedance: np.ndarray
    admittance: np.ndarray
    calibration_profile: CalibrationProfile | None = None


class TransformationPlugin(ABC):
    @abstractmethod
    def name(self) -> str:
        """Return the unique plugin key."""

    @abstractmethod
    def description(self) -> str:
        """Return a concise description."""

    @abstractmethod
    def calculate(self, context: TransformationContext) -> MaterialSpectrum:
        """Calculate a material spectrum for the provided context."""

    @abstractmethod
    def validate(self, context: TransformationContext) -> list[str]:
        """Return validation issues. An empty list means the context is acceptable."""

    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """Return plugin metadata such as status, assumptions, and support level."""

