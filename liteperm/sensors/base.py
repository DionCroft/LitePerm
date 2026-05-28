"""Base classes for sensor-model specialisation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from liteperm.models.core import CalibrationProfile, SensorGeometryProfile


@dataclass(slots=True)
class SensorModel(ABC):
    geometry: SensorGeometryProfile
    substrate: str
    calibration: CalibrationProfile
    frequency_range_hz: tuple[float, float]
    measurement_method: str

    @property
    @abstractmethod
    def sensor_family(self) -> str:
        """Human-readable sensor family name."""

    def summary(self) -> dict[str, object]:
        return {
            "sensor_family": self.sensor_family,
            "geometry_name": self.geometry.name,
            "sensor_type": self.geometry.sensor_type,
            "substrate": self.substrate,
            "calibration": self.calibration.name,
            "frequency_range_hz": self.frequency_range_hz,
            "measurement_method": self.measurement_method,
            "parameters": self.geometry.parameters,
        }

