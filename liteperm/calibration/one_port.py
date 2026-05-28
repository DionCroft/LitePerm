"""One-port calibration utilities for S11 measurements."""

from __future__ import annotations

from dataclasses import asdict

import numpy as np

from liteperm.models.core import MeasurementData, OnePortErrorTerms
from liteperm.utils.constants import NUMERIC_EPSILON


def _interpolate_complex(frequency_hz: np.ndarray, source_frequency_hz: np.ndarray, values: np.ndarray) -> np.ndarray:
    real = np.interp(frequency_hz, source_frequency_hz, values.real)
    imag = np.interp(frequency_hz, source_frequency_hz, values.imag)
    return real + 1j * imag


def solve_one_port_error_terms(
    open_measurement: MeasurementData,
    short_measurement: MeasurementData,
    load_measurement: MeasurementData,
    *,
    open_gamma: complex = complex(1.0, 0.0),
    short_gamma: complex = complex(-1.0, 0.0),
    load_gamma: complex = complex(0.0, 0.0),
    frequency_hz: np.ndarray | None = None,
) -> OnePortErrorTerms:
    common_frequency = np.asarray(frequency_hz if frequency_hz is not None else load_measurement.frequency_hz, dtype=float)
    m_open = _interpolate_complex(common_frequency, open_measurement.frequency_hz, open_measurement.s11)
    m_short = _interpolate_complex(common_frequency, short_measurement.frequency_hz, short_measurement.s11)
    m_load = _interpolate_complex(common_frequency, load_measurement.frequency_hz, load_measurement.s11)

    standards = [(m_open, open_gamma), (m_short, short_gamma), (m_load, load_gamma)]
    directivity = np.empty_like(common_frequency, dtype=complex)
    reflection_tracking = np.empty_like(common_frequency, dtype=complex)
    source_match = np.empty_like(common_frequency, dtype=complex)

    for index in range(common_frequency.size):
        matrix = np.array(
            [
                [1.0, gamma, gamma * measurement[index]]
                for measurement, gamma in standards
            ],
            dtype=complex,
        )
        vector = np.array([measurement[index] for measurement, _ in standards], dtype=complex)
        x_term, y_term, z_term = np.linalg.solve(matrix, vector)
        directivity[index] = x_term
        source_match[index] = z_term
        reflection_tracking[index] = y_term + x_term * z_term

    return OnePortErrorTerms(
        frequency_hz=common_frequency,
        directivity=directivity,
        reflection_tracking=reflection_tracking,
        source_match=source_match,
    )


def apply_one_port_calibration(
    measurement: MeasurementData,
    open_measurement: MeasurementData,
    short_measurement: MeasurementData,
    load_measurement: MeasurementData,
    *,
    open_gamma: complex = complex(1.0, 0.0),
    short_gamma: complex = complex(-1.0, 0.0),
    load_gamma: complex = complex(0.0, 0.0),
) -> tuple[MeasurementData, OnePortErrorTerms]:
    error_terms = solve_one_port_error_terms(
        open_measurement,
        short_measurement,
        load_measurement,
        open_gamma=open_gamma,
        short_gamma=short_gamma,
        load_gamma=load_gamma,
        frequency_hz=measurement.frequency_hz,
    )
    numerator = measurement.s11 - error_terms.directivity
    denominator = error_terms.reflection_tracking + error_terms.source_match * numerator
    corrected = numerator / np.where(np.abs(denominator) < NUMERIC_EPSILON, NUMERIC_EPSILON, denominator)
    corrected_measurement = measurement.copy_with_s11(
        corrected,
        source_name=f"{measurement.source_name or 'measurement'} (calibrated)",
        metadata_update={"calibration": asdict(error_terms)},
    )
    return corrected_measurement, error_terms

