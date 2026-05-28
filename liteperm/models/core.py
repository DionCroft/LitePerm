"""Core data models used across the LitePerm application."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from liteperm.utils.constants import DEFAULT_Z0, NUMERIC_EPSILON


@dataclass(slots=True)
class MeasurementData:
    frequency_hz: np.ndarray
    s11: np.ndarray
    z0: float = DEFAULT_Z0
    source_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.frequency_hz = np.asarray(self.frequency_hz, dtype=float)
        self.s11 = np.asarray(self.s11, dtype=complex)
        if self.frequency_hz.ndim != 1 or self.s11.ndim != 1:
            raise ValueError("Measurement arrays must be one-dimensional.")
        if self.frequency_hz.size != self.s11.size:
            raise ValueError("Frequency and S11 arrays must have the same length.")
        if self.frequency_hz.size == 0:
            raise ValueError("Measurement arrays cannot be empty.")

    @property
    def magnitude(self) -> np.ndarray:
        return np.abs(self.s11)

    @property
    def magnitude_db(self) -> np.ndarray:
        return 20.0 * np.log10(np.maximum(self.magnitude, NUMERIC_EPSILON))

    @property
    def phase_deg(self) -> np.ndarray:
        return np.rad2deg(np.angle(self.s11))

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "frequency_hz": self.frequency_hz,
                "s11_real": self.s11.real,
                "s11_imag": self.s11.imag,
                "s11_magnitude": self.magnitude,
                "s11_db": self.magnitude_db,
                "s11_phase_deg": self.phase_deg,
            }
        )

    def copy_with_s11(
        self,
        s11: np.ndarray,
        *,
        source_name: str | None = None,
        metadata_update: dict[str, Any] | None = None,
    ) -> "MeasurementData":
        updated_metadata = dict(self.metadata)
        if metadata_update:
            updated_metadata.update(metadata_update)
        return MeasurementData(
            frequency_hz=self.frequency_hz.copy(),
            s11=np.asarray(s11, dtype=complex),
            z0=self.z0,
            source_name=source_name or self.source_name,
            metadata=updated_metadata,
        )


@dataclass(slots=True)
class OnePortErrorTerms:
    frequency_hz: np.ndarray
    directivity: np.ndarray
    reflection_tracking: np.ndarray
    source_match: np.ndarray


@dataclass(slots=True)
class CalibrationProfile:
    name: str
    open_gamma: complex = complex(1.0, 0.0)
    short_gamma: complex = complex(-1.0, 0.0)
    load_gamma: complex = complex(0.0, 0.0)
    reference_materials: list[str] = field(default_factory=list)
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "actual_standards": {
                "open_gamma": self.open_gamma,
                "short_gamma": self.short_gamma,
                "load_gamma": self.load_gamma,
            },
            "reference_materials": self.reference_materials,
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class SensorGeometryProfile:
    name: str
    sensor_type: str
    parameters: dict[str, float | str]
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: float | str | None = None) -> float | str | None:
        return self.parameters.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sensor_type": self.sensor_type,
            "parameters": self.parameters,
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class MaterialSpectrum:
    frequency_hz: np.ndarray
    epsilon_complex: np.ndarray
    impedance: np.ndarray
    admittance: np.ndarray
    gamma: np.ndarray
    conductivity_s_per_m: np.ndarray
    loss_tangent: np.ndarray
    method: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.frequency_hz = np.asarray(self.frequency_hz, dtype=float)
        self.epsilon_complex = np.asarray(self.epsilon_complex, dtype=complex)
        self.impedance = np.asarray(self.impedance, dtype=complex)
        self.admittance = np.asarray(self.admittance, dtype=complex)
        self.gamma = np.asarray(self.gamma, dtype=complex)
        self.conductivity_s_per_m = np.asarray(self.conductivity_s_per_m, dtype=float)
        self.loss_tangent = np.asarray(self.loss_tangent, dtype=float)

    @property
    def epsilon_prime(self) -> np.ndarray:
        return self.epsilon_complex.real

    @property
    def epsilon_double_prime(self) -> np.ndarray:
        return -self.epsilon_complex.imag

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "frequency_hz": self.frequency_hz,
                "epsilon_prime": self.epsilon_prime,
                "epsilon_double_prime": self.epsilon_double_prime,
                "loss_tangent": self.loss_tangent,
                "conductivity_s_per_m": self.conductivity_s_per_m,
                "gamma_real": self.gamma.real,
                "gamma_imag": self.gamma.imag,
                "impedance_real_ohm": self.impedance.real,
                "impedance_imag_ohm": self.impedance.imag,
                "admittance_real_s": self.admittance.real,
                "admittance_imag_s": self.admittance.imag,
            }
        )


@dataclass(frozen=True, slots=True)
class MethodInfo:
    key: str
    display_name: str
    description: str
    assumptions: str
    validation_status: str = "experimental"

