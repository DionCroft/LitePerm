"""Core S-parameter, impedance, and admittance conversions."""

from __future__ import annotations

import numpy as np

from liteperm.utils.constants import DEFAULT_Z0, EPSILON_0, NUMERIC_EPSILON, TWO_PI


def frequency_to_angular(frequency_hz: np.ndarray) -> np.ndarray:
    return TWO_PI * np.asarray(frequency_hz, dtype=float)


def gamma_to_impedance(gamma: np.ndarray, *, z0: float = DEFAULT_Z0) -> np.ndarray:
    gamma = np.asarray(gamma, dtype=complex)
    denominator = np.where(np.abs(1 - gamma) < NUMERIC_EPSILON, NUMERIC_EPSILON, 1 - gamma)
    return z0 * (1 + gamma) / denominator


def impedance_to_gamma(impedance: np.ndarray, *, z0: float = DEFAULT_Z0) -> np.ndarray:
    impedance = np.asarray(impedance, dtype=complex)
    denominator = np.where(np.abs(impedance + z0) < NUMERIC_EPSILON, NUMERIC_EPSILON, impedance + z0)
    return (impedance - z0) / denominator


def impedance_to_admittance(impedance: np.ndarray) -> np.ndarray:
    impedance = np.asarray(impedance, dtype=complex)
    return 1 / np.where(np.abs(impedance) < NUMERIC_EPSILON, NUMERIC_EPSILON, impedance)


def admittance_to_impedance(admittance: np.ndarray) -> np.ndarray:
    admittance = np.asarray(admittance, dtype=complex)
    return 1 / np.where(np.abs(admittance) < NUMERIC_EPSILON, NUMERIC_EPSILON, admittance)


def gamma_to_admittance(gamma: np.ndarray, *, z0: float = DEFAULT_Z0) -> np.ndarray:
    return impedance_to_admittance(gamma_to_impedance(gamma, z0=z0))


def compute_loss_tangent(epsilon_complex: np.ndarray) -> np.ndarray:
    epsilon_complex = np.asarray(epsilon_complex, dtype=complex)
    epsilon_prime = np.where(np.abs(epsilon_complex.real) < NUMERIC_EPSILON, NUMERIC_EPSILON, epsilon_complex.real)
    return -epsilon_complex.imag / epsilon_prime


def compute_conductivity(frequency_hz: np.ndarray, epsilon_complex: np.ndarray) -> np.ndarray:
    epsilon_complex = np.asarray(epsilon_complex, dtype=complex)
    return frequency_to_angular(frequency_hz) * EPSILON_0 * (-epsilon_complex.imag)

