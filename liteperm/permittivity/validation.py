"""Validation helpers for permittivity-first measurement workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from liteperm.models.core import CalibrationProfile, MaterialSpectrum, MeasurementData


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(slots=True)
class ValidationCheck:
    name: str
    score: float
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": float(self.score),
            "passed": bool(self.passed),
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ValidationCheck":
        return cls(
            name=payload.get("name", ""),
            score=float(payload.get("score", 0.0)),
            passed=bool(payload.get("passed", False)),
            detail=payload.get("detail", ""),
        )


@dataclass(slots=True)
class PermittivityValidationResult:
    confidence_score: float
    confidence_label: str
    checks: list[ValidationCheck] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence_score": float(self.confidence_score),
            "confidence_label": self.confidence_label,
            "checks": [check.to_dict() for check in self.checks],
            "summary": self.summary,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PermittivityValidationResult":
        return cls(
            confidence_score=float(payload.get("confidence_score", 0.0)),
            confidence_label=payload.get("confidence_label", "Low"),
            checks=[ValidationCheck.from_dict(item) for item in payload.get("checks", [])],
            summary=payload.get("summary", ""),
            metadata=payload.get("metadata", {}),
        )

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([check.to_dict() for check in self.checks])


def _label_from_score(score: float) -> str:
    if score >= 80:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def validate_permittivity_measurement(
    spectrum: MaterialSpectrum,
    measurement: MeasurementData,
    *,
    calibration_profile: CalibrationProfile | None = None,
    reference_materials: list[dict[str, Any]] | None = None,
) -> PermittivityValidationResult:
    epsilon_prime = np.asarray(spectrum.epsilon_prime, dtype=float)
    epsilon_double_prime = np.asarray(spectrum.epsilon_double_prime, dtype=float)
    conductivity = np.asarray(spectrum.conductivity_s_per_m, dtype=float)
    loss_tangent = np.asarray(spectrum.loss_tangent, dtype=float)

    checks: list[ValidationCheck] = []

    out_of_range_fraction = np.mean((epsilon_prime < 0.8) | (epsilon_prime > 150.0))
    out_of_range_fraction += np.mean((epsilon_double_prime < -0.1) | (epsilon_double_prime > 80.0))
    out_of_range_fraction /= 2.0
    range_score = 20.0 * (1.0 - _clamp(float(out_of_range_fraction)))
    checks.append(
        ValidationCheck(
            name="Permittivity Range",
            score=range_score,
            passed=range_score >= 14.0,
            detail="Checks whether epsilon' and epsilon'' stay within plausible broadband dielectric ranges.",
        )
    )

    loss_outliers = np.mean((loss_tangent < 0.0) | (loss_tangent > 6.0))
    conductivity_outliers = np.mean((conductivity < 0.0) | (conductivity > 50.0))
    loss_score = 20.0 * (1.0 - _clamp(float((loss_outliers + conductivity_outliers) / 2.0)))
    checks.append(
        ValidationCheck(
            name="Loss and Conductivity",
            score=loss_score,
            passed=loss_score >= 14.0,
            detail="Checks whether loss tangent and conductivity remain physically plausible for a practical measurement.",
        )
    )

    epsilon_gradient = np.diff(epsilon_prime, prepend=epsilon_prime[0])
    epsilon_noise_proxy = np.std(epsilon_gradient) / max(np.mean(np.abs(epsilon_prime)), 1e-6)
    s11_noise_proxy = np.std(np.diff(np.abs(measurement.s11), prepend=np.abs(measurement.s11[0])))
    noise_score = 20.0 * (1.0 - _clamp(float(epsilon_noise_proxy / 0.3 + s11_noise_proxy / 0.15) / 2.0))
    checks.append(
        ValidationCheck(
            name="Noise Level",
            score=noise_score,
            passed=noise_score >= 12.0,
            detail="Estimates whether the permittivity spectrum and measured S11 appear excessively noisy.",
        )
    )

    frequency_axis = np.asarray(measurement.frequency_hz, dtype=float)
    monotonic = bool(np.all(np.diff(frequency_axis) > 0))
    span_hz = float(frequency_axis.max() - frequency_axis.min())
    density_score = 1.0 if frequency_axis.size >= 101 else 0.75 if frequency_axis.size >= 51 else 0.45
    span_score = 1.0 if span_hz >= 100e6 else 0.7 if span_hz >= 25e6 else 0.35
    stability_score = 20.0 * ((1.0 if monotonic else 0.0) * 0.45 + density_score * 0.3 + span_score * 0.25)
    checks.append(
        ValidationCheck(
            name="Frequency Stability",
            score=stability_score,
            passed=stability_score >= 12.0,
            detail="Checks frequency monotonicity, sweep span, and point density.",
        )
    )

    calibration_score_components: list[float] = []
    if calibration_profile is None:
        calibration_score_components.append(0.4)
    else:
        standards = [
            abs(calibration_profile.open_gamma - complex(1.0, 0.0)),
            abs(calibration_profile.short_gamma - complex(-1.0, 0.0)),
            abs(calibration_profile.load_gamma - complex(0.0, 0.0)),
        ]
        standards_score = 1.0 - _clamp(float(np.mean(standards)))
        calibration_score_components.append(standards_score)
        calibration_score_components.append(1.0 if len(calibration_profile.reference_materials) >= 2 else 0.65 if calibration_profile.reference_materials else 0.4)
    calibration_score = 20.0 * float(np.mean(calibration_score_components))
    checks.append(
        ValidationCheck(
            name="Calibration Quality",
            score=calibration_score,
            passed=calibration_score >= 10.0,
            detail="Checks OSL completeness and the presence of reference-material context in the active calibration profile.",
        )
    )

    valid_reference_count = 0
    if reference_materials:
        valid_reference_count = sum(1 for material in reference_materials if material)
    else:
        valid_reference_count = len(calibration_profile.reference_materials) if calibration_profile is not None else 0
    reference_score = 20.0 * (1.0 if valid_reference_count >= 2 else 0.7 if valid_reference_count == 1 else 0.45)
    checks.append(
        ValidationCheck(
            name="Reference Consistency",
            score=reference_score,
            passed=reference_score >= 10.0,
            detail="Rewards measurements that carry clear reference-material context for later comparison and validation.",
        )
    )

    confidence_score = float(sum(check.score for check in checks))
    confidence_label = _label_from_score(confidence_score)
    summary = {
        "High": "The measurement appears physically plausible and well supported by the current calibration and sweep setup.",
        "Medium": "The measurement is usable, but LitePerm detected one or more issues that should be reviewed before publication-grade reporting.",
        "Low": "The measurement likely needs recalibration, a cleaner sweep, or better reference-material context before it should be trusted.",
    }[confidence_label]
    return PermittivityValidationResult(
        confidence_score=confidence_score,
        confidence_label=confidence_label,
        checks=checks,
        summary=summary,
        metadata={
            "mean_epsilon_prime": float(np.mean(epsilon_prime)),
            "mean_epsilon_double_prime": float(np.mean(epsilon_double_prime)),
            "mean_loss_tangent": float(np.mean(loss_tangent)),
            "mean_conductivity_s_per_m": float(np.mean(conductivity)),
        },
    )
