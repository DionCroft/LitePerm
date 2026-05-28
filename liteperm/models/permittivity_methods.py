"""Permittivity inversion method registry."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from liteperm.models.core import MaterialSpectrum, MethodInfo, SensorGeometryProfile
from liteperm.transform.network import compute_conductivity, compute_loss_tangent
from liteperm.utils.constants import EPSILON_0, NUMERIC_EPSILON, TWO_PI


def _effective_capacitance(geometry: SensorGeometryProfile) -> float:
    sensor_type = geometry.sensor_type
    parameters = geometry.parameters

    if sensor_type == "open_ended_coax_probe":
        inner_radius_m = float(parameters.get("inner_radius_mm", 0.6)) * 1e-3
        outer_radius_m = float(parameters.get("outer_radius_mm", 2.05)) * 1e-3
        flange_radius_m = float(parameters.get("flange_radius_mm", 6.0)) * 1e-3
        effective_length_m = max(flange_radius_m, outer_radius_m)
        return max(
            2.0 * np.pi * EPSILON_0 * effective_length_m / np.log(max(outer_radius_m / inner_radius_m, 1.0001)),
            1e-15,
        )

    if sensor_type == "patch_antenna":
        length_m = float(parameters.get("length_mm", 32.0)) * 1e-3
        width_m = float(parameters.get("width_mm", 38.0)) * 1e-3
        height_m = float(parameters.get("substrate_height_mm", 1.6)) * 1e-3
        return max(EPSILON_0 * length_m * width_m / max(height_m, 1e-6), 1e-15)

    effective_capacitance_pf = float(parameters.get("effective_capacitance_pf", 0.85))
    return max(effective_capacitance_pf * 1e-12, 1e-15)


class BasePermittivityMethod(ABC):
    info: MethodInfo

    @abstractmethod
    def estimate(
        self,
        *,
        frequency_hz: np.ndarray,
        gamma: np.ndarray,
        impedance: np.ndarray,
        admittance: np.ndarray,
        geometry: SensorGeometryProfile,
    ) -> MaterialSpectrum:
        """Estimate complex permittivity from network data."""

    def _build_spectrum(
        self,
        *,
        frequency_hz: np.ndarray,
        gamma: np.ndarray,
        impedance: np.ndarray,
        admittance: np.ndarray,
        epsilon_complex: np.ndarray,
    ) -> MaterialSpectrum:
        return MaterialSpectrum(
            frequency_hz=frequency_hz,
            epsilon_complex=epsilon_complex,
            impedance=impedance,
            admittance=admittance,
            gamma=gamma,
            conductivity_s_per_m=compute_conductivity(frequency_hz, epsilon_complex),
            loss_tangent=compute_loss_tangent(epsilon_complex),
            method=self.info.display_name,
            metadata={"assumptions": self.info.assumptions, "validation_status": self.info.validation_status},
        )


class StuchlyMethod(BasePermittivityMethod):
    info = MethodInfo(
        key="stuchly",
        display_name="Stuchly",
        description="Admittance-based quasi-static OECP inversion with a geometry-derived cell constant.",
        assumptions="Best used as a first-pass reconstruction for open-ended probes and other capacitive sensors.",
    )

    def estimate(
        self,
        *,
        frequency_hz: np.ndarray,
        gamma: np.ndarray,
        impedance: np.ndarray,
        admittance: np.ndarray,
        geometry: SensorGeometryProfile,
    ) -> MaterialSpectrum:
        omega = TWO_PI * np.asarray(frequency_hz, dtype=float)
        c0 = _effective_capacitance(geometry)
        epsilon_complex = admittance / (1j * np.where(omega < NUMERIC_EPSILON, NUMERIC_EPSILON, omega) * c0)
        return self._build_spectrum(
            frequency_hz=frequency_hz,
            gamma=gamma,
            impedance=impedance,
            admittance=admittance,
            epsilon_complex=epsilon_complex,
        )


class MarslandMethod(BasePermittivityMethod):
    info = MethodInfo(
        key="marsland",
        display_name="Marsland",
        description="Stuchly-style inversion with additional frequency-dependent fringing correction.",
        assumptions="Experimental correction intended to stabilise broadband sweeps for flange-backed probes.",
    )

    def estimate(
        self,
        *,
        frequency_hz: np.ndarray,
        gamma: np.ndarray,
        impedance: np.ndarray,
        admittance: np.ndarray,
        geometry: SensorGeometryProfile,
    ) -> MaterialSpectrum:
        base = StuchlyMethod().estimate(
            frequency_hz=frequency_hz,
            gamma=gamma,
            impedance=impedance,
            admittance=admittance,
            geometry=geometry,
        )
        flange_radius_mm = float(geometry.parameters.get("flange_radius_mm", 6.0))
        correction = 1.0 + 0.015 * np.sqrt(np.asarray(frequency_hz, dtype=float) / np.max(frequency_hz)) + 0.0025 * flange_radius_mm
        epsilon_complex = base.epsilon_complex / correction
        return self._build_spectrum(
            frequency_hz=frequency_hz,
            gamma=gamma,
            impedance=impedance,
            admittance=admittance,
            epsilon_complex=epsilon_complex,
        )


class KomarovMethod(BasePermittivityMethod):
    info = MethodInfo(
        key="komarov",
        display_name="Komarov",
        description="Dispersive correction layer applied to the geometry-normalised admittance inversion.",
        assumptions="Experimental placeholder for full-wave Komarov-style models; useful for architecture validation.",
    )

    def estimate(
        self,
        *,
        frequency_hz: np.ndarray,
        gamma: np.ndarray,
        impedance: np.ndarray,
        admittance: np.ndarray,
        geometry: SensorGeometryProfile,
    ) -> MaterialSpectrum:
        base = StuchlyMethod().estimate(
            frequency_hz=frequency_hz,
            gamma=gamma,
            impedance=impedance,
            admittance=admittance,
            geometry=geometry,
        )
        outer_radius_mm = float(geometry.parameters.get("outer_radius_mm", 2.05))
        dispersive_term = 1.0 + 1j * 0.01 * (outer_radius_mm / 2.05) * (np.asarray(frequency_hz, dtype=float) / np.max(frequency_hz))
        epsilon_complex = base.epsilon_complex / dispersive_term
        return self._build_spectrum(
            frequency_hz=frequency_hz,
            gamma=gamma,
            impedance=impedance,
            admittance=admittance,
            epsilon_complex=epsilon_complex,
        )


METHOD_REGISTRY: dict[str, BasePermittivityMethod] = {
    "stuchly": StuchlyMethod(),
    "marsland": MarslandMethod(),
    "komarov": KomarovMethod(),
}

