"""Feature extraction helpers for future machine-learning datasets."""

from __future__ import annotations

import numpy as np
import pandas as pd

from liteperm.models.core import MaterialSpectrum, MeasurementData


def extract_spectrum_features(measurement: MeasurementData, spectrum: MaterialSpectrum) -> dict[str, float]:
    min_index = int(np.argmin(measurement.magnitude_db))
    resonant_frequency = float(measurement.frequency_hz[min_index])
    minimum_s11_db = float(measurement.magnitude_db[min_index])
    threshold = minimum_s11_db + 3.0

    below_threshold = np.where(measurement.magnitude_db <= threshold)[0]
    if below_threshold.size >= 2:
        bandwidth = float(measurement.frequency_hz[below_threshold[-1]] - measurement.frequency_hz[below_threshold[0]])
    else:
        bandwidth = 0.0
    q_factor = float(resonant_frequency / bandwidth) if bandwidth > 0 else 0.0

    phase_gradient = np.gradient(measurement.phase_deg, measurement.frequency_hz)

    return {
        "resonant_frequency_hz": resonant_frequency,
        "frequency_shift_hz": float(resonant_frequency - measurement.frequency_hz[0]),
        "bandwidth_hz": bandwidth,
        "q_factor": q_factor,
        "minimum_s11_db": minimum_s11_db,
        "phase_slope": float(phase_gradient[min_index]),
        "impedance_real_mean": float(np.mean(spectrum.impedance.real)),
        "impedance_imag_mean": float(np.mean(spectrum.impedance.imag)),
        "epsilon_prime_mean": float(np.mean(spectrum.epsilon_prime)),
        "epsilon_double_prime_mean": float(np.mean(spectrum.epsilon_double_prime)),
        "loss_tangent_peak": float(np.max(spectrum.loss_tangent)),
        "conductivity_peak": float(np.max(spectrum.conductivity_s_per_m)),
    }


def features_to_frame(features: list[dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(features)

