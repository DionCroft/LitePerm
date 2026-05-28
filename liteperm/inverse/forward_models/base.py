"""Base forward-model interface and utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from liteperm.inverse.common import ForwardSimulation, LayerStack, ParameterDefinition
from liteperm.models.core import SensorGeometryProfile
from liteperm.transform.network import gamma_to_admittance, gamma_to_impedance, impedance_to_gamma
from liteperm.utils.constants import C_0, DEFAULT_Z0, EPSILON_0, NUMERIC_EPSILON, TWO_PI


@dataclass(slots=True)
class ForwardModel(ABC):
    geometry: SensorGeometryProfile
    layer_stack: LayerStack
    z0: float = DEFAULT_Z0
    metadata_overrides: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def simulate(self, frequency_hz: np.ndarray) -> ForwardSimulation:
        """Return the predicted RF response for the supplied frequency axis."""

    @abstractmethod
    def validate(self) -> list[str]:
        """Return a list of validation warnings or issues."""

    @abstractmethod
    def parameters(self) -> list[ParameterDefinition]:
        """Return the default inverse parameter definitions for this model."""

    @abstractmethod
    def constraints(self) -> dict[str, Any]:
        """Return parameter or model constraints."""

    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """Return descriptive metadata."""

    def _stack_effective_epsilon(self, *, decay_length_m: float | None = None) -> complex:
        return self.layer_stack.effective_epsilon(decay_length_m=decay_length_m)

    def _effective_complex_permittivity_array(self, frequency_hz: np.ndarray, epsilon_complex: complex) -> np.ndarray:
        return np.full_like(np.asarray(frequency_hz, dtype=float), epsilon_complex, dtype=complex)

    def _make_field_distribution(self, width_m: float, length_m: float, field_scale: float = 1.0) -> dict[str, Any]:
        x = np.linspace(-width_m / 2, width_m / 2, 24)
        y = np.linspace(-length_m / 2, length_m / 2, 24)
        xx, yy = np.meshgrid(x, y)
        field = field_scale * np.abs(np.cos(np.pi * xx / max(width_m, 1e-6)) * np.sin(np.pi * yy / max(length_m, 1e-6)))
        return {"x_m": x.tolist(), "y_m": y.tolist(), "field_strength": field.tolist()}

    def _series_resonator_simulation(
        self,
        *,
        frequency_hz: np.ndarray,
        resonant_frequency_hz: float,
        q_factor: float,
        resistance_ohm: float,
        effective_permittivity_complex: complex,
        width_m: float,
        length_m: float,
        coupling_depth: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> ForwardSimulation:
        frequency_hz = np.asarray(frequency_hz, dtype=float)
        q_factor = max(float(q_factor), 1.0)
        normalized = frequency_hz / max(float(resonant_frequency_hz), 1.0)
        impedance = resistance_ohm * (1.0 + 1j * q_factor * (normalized - 1.0 / np.maximum(normalized, NUMERIC_EPSILON)))
        impedance *= complex(max(coupling_depth, 0.1), 0.0)
        gamma = impedance_to_gamma(impedance, z0=self.z0)
        admittance = gamma_to_admittance(gamma, z0=self.z0)
        return ForwardSimulation(
            frequency_hz=frequency_hz,
            s11=gamma,
            impedance=impedance,
            admittance=admittance,
            predicted_resonant_frequency_hz=float(resonant_frequency_hz),
            effective_permittivity_complex=self._effective_complex_permittivity_array(frequency_hz, effective_permittivity_complex),
            electric_field_distribution=self._make_field_distribution(width_m, length_m, field_scale=float(abs(effective_permittivity_complex))),
            metadata=metadata or self.metadata(),
            z0=self.z0,
        )


def microstrip_effective_permittivity(substrate_er: float, substrate_height_m: float, trace_width_m: float, external_er: complex) -> complex:
    width_height = max(trace_width_m / max(substrate_height_m, 1e-6), 1e-6)
    base = (substrate_er + external_er) / 2
    correction = (substrate_er - external_er) / 2 * 1 / np.sqrt(1 + 12 / width_height)
    return complex(base + correction)


def dielectric_notch_q(base_q: float, epsilon_complex: complex, conductivity: float, total_thickness_m: float) -> float:
    dielectric_loss = abs(epsilon_complex.imag) / max(abs(epsilon_complex.real), 1e-6)
    conductive_loss = max(conductivity, 0.0) * max(total_thickness_m, 1e-6) * 4
    return max(base_q / (1 + dielectric_loss * 15 + conductive_loss), 3.0)


def coax_probe_capacitance(inner_radius_m: float, outer_radius_m: float, effective_length_m: float) -> float:
    return max(2 * np.pi * EPSILON_0 * effective_length_m / np.log(max(outer_radius_m / max(inner_radius_m, 1e-9), 1.0001)), 1e-15)


def patch_resonant_frequency(length_m: float, substrate_height_m: float, effective_er: complex) -> float:
    fringing = 0.412 * substrate_height_m * ((effective_er.real + 0.3) * (length_m / max(substrate_height_m, 1e-6) + 0.264))
    fringing /= max((effective_er.real - 0.258) * (length_m / max(substrate_height_m, 1e-6) + 0.8), 1e-6)
    effective_length = length_m + 2 * fringing
    return float(C_0 / (2 * effective_length * np.sqrt(max(effective_er.real, 1e-6))))


def quarter_wave_resonant_frequency(length_m: float, effective_er: complex) -> float:
    return float(C_0 / (4 * max(length_m, 1e-6) * np.sqrt(max(effective_er.real, 1e-6))))


def angular_frequency(frequency_hz: np.ndarray) -> np.ndarray:
    return TWO_PI * np.asarray(frequency_hz, dtype=float)

