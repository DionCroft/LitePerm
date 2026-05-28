"""Implant-sensor research framework placeholders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TissueModel:
    name: str
    epsilon_real: float
    epsilon_imag: float
    conductivity_s_per_m: float
    notes: str = ""


@dataclass(slots=True)
class ImplantSensorEstimate:
    estimated_tissue_properties: dict[str, float]
    estimated_sensor_environment: dict[str, float]
    predicted_resonance_shift_hz: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ImplantSensorFramework:
    modality: str
    tissue_model: TissueModel
    geometry: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def supported_modalities(self) -> list[str]:
        return [
            "passive_resonant_sensor",
            "wireless_patch_sensor",
            "microstrip_implant_sensor",
            "future_ph_sensor",
            "future_infection_sensor",
        ]
