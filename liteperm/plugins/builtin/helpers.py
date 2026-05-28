"""Shared helpers used by built-in plugins."""

from __future__ import annotations

import numpy as np

from liteperm.models.core import MaterialSpectrum, SensorGeometryProfile
from liteperm.transform.network import compute_conductivity, compute_loss_tangent
from liteperm.utils.constants import EPSILON_0, NUMERIC_EPSILON, TWO_PI


def effective_capacitance(geometry: SensorGeometryProfile) -> float:
    sensor_type = geometry.sensor_type
    parameters = geometry.parameters

    if sensor_type == "open_ended_coax_probe":
        inner_radius_m = float(parameters.get("inner_radius_mm", 0.6)) * 1e-3
        outer_radius_m = float(parameters.get("outer_radius_mm", 2.05)) * 1e-3
        flange_radius_m = float(parameters.get("flange_radius_mm", 6.0)) * 1e-3
        effective_length_m = max(flange_radius_m, outer_radius_m)
        ratio = max(outer_radius_m / max(inner_radius_m, 1e-6), 1.0001)
        return max(2.0 * np.pi * EPSILON_0 * effective_length_m / np.log(ratio), 1e-15)

    if sensor_type == "patch_antenna":
        length_m = float(parameters.get("length_mm", 32.0)) * 1e-3
        width_m = float(parameters.get("width_mm", 38.0)) * 1e-3
        height_m = float(parameters.get("substrate_height_mm", 1.6)) * 1e-3
        return max(EPSILON_0 * length_m * width_m / max(height_m, 1e-6), 1e-15)

    effective_capacitance_pf = float(parameters.get("effective_capacitance_pf", 0.85))
    return max(effective_capacitance_pf * 1e-12, 1e-15)


def admittance_to_epsilon(frequency_hz: np.ndarray, admittance: np.ndarray, geometry: SensorGeometryProfile) -> np.ndarray:
    omega = TWO_PI * np.asarray(frequency_hz, dtype=float)
    c0 = effective_capacitance(geometry)
    return admittance / (1j * np.where(np.abs(omega) < NUMERIC_EPSILON, NUMERIC_EPSILON, omega) * c0)


def build_spectrum(
    *,
    frequency_hz: np.ndarray,
    gamma: np.ndarray,
    impedance: np.ndarray,
    admittance: np.ndarray,
    epsilon_complex: np.ndarray,
    method_name: str,
    metadata: dict[str, object],
) -> MaterialSpectrum:
    return MaterialSpectrum(
        frequency_hz=frequency_hz,
        epsilon_complex=epsilon_complex,
        impedance=impedance,
        admittance=admittance,
        gamma=gamma,
        conductivity_s_per_m=compute_conductivity(frequency_hz, epsilon_complex),
        loss_tangent=compute_loss_tangent(epsilon_complex),
        method=method_name,
        metadata=metadata,
    )

