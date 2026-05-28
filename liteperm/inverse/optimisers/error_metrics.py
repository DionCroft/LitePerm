"""Error metrics for inverse-model optimisation."""

from __future__ import annotations

import numpy as np

from liteperm.models.core import MeasurementData


def residual_vector(measured: MeasurementData, predicted: MeasurementData, *, metric: str = "complex_error") -> np.ndarray:
    metric = metric.lower()
    if metric == "complex_error":
        return np.concatenate([(measured.s11 - predicted.s11).real, (measured.s11 - predicted.s11).imag])
    if metric == "magnitude_error":
        return measured.magnitude_db - predicted.magnitude_db
    if metric == "phase_error":
        return measured.phase_deg - predicted.phase_deg
    if metric == "weighted_error":
        magnitude_residual = measured.magnitude_db - predicted.magnitude_db
        phase_residual = (measured.phase_deg - predicted.phase_deg) / 180.0
        return np.concatenate([1.5 * magnitude_residual, phase_residual])
    if metric == "multi_objective_error":
        return np.concatenate(
            [
                measured.magnitude_db - predicted.magnitude_db,
                (measured.phase_deg - predicted.phase_deg) / 180.0,
                (measured.s11 - predicted.s11).real,
                (measured.s11 - predicted.s11).imag,
            ]
        )
    if metric in {"rmse", "mse", "mae"}:
        return np.abs(measured.s11 - predicted.s11)
    raise KeyError(f"Unknown error metric: {metric}")


def compute_scalar_error(measured: MeasurementData, predicted: MeasurementData, *, metric: str = "weighted_error") -> float:
    metric = metric.lower()
    residual = residual_vector(measured, predicted, metric=metric)
    if metric == "mae":
        return float(np.mean(np.abs(residual)))
    if metric == "mse":
        return float(np.mean(np.abs(residual) ** 2))
    return float(np.sqrt(np.mean(np.abs(residual) ** 2)))

