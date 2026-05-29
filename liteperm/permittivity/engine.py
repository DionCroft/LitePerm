"""Permittivity-first measurement orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from liteperm.models.core import CalibrationProfile, MaterialSpectrum, MeasurementData, SensorGeometryProfile
from liteperm.permittivity.matching import compare_to_reference_materials, identify_closest_materials
from liteperm.permittivity.validation import PermittivityValidationResult, validate_permittivity_measurement
from liteperm.transform.permittivity import compute_material_spectrum
from liteperm.utils.resources import load_reference_materials


@dataclass(slots=True)
class PermittivityMeasurementResult:
    spectrum: MaterialSpectrum
    processed_measurement: MeasurementData
    validation: PermittivityValidationResult
    reference_comparisons: list[dict[str, Any]] = field(default_factory=list)
    identified_materials: list[dict[str, Any]] = field(default_factory=list)
    confidence_estimate: str = "Low"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spectrum": self.spectrum.to_dict(),
            "processed_measurement": self.processed_measurement.to_dict(),
            "validation": self.validation.to_dict(),
            "reference_comparisons": self.reference_comparisons,
            "identified_materials": self.identified_materials,
            "confidence_estimate": self.confidence_estimate,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PermittivityMeasurementResult":
        from liteperm.models.core import MaterialSpectrum, MeasurementData
        from liteperm.permittivity.validation import PermittivityValidationResult

        return cls(
            spectrum=MaterialSpectrum.from_dict(payload.get("spectrum", {})),
            processed_measurement=MeasurementData.from_dict(payload.get("processed_measurement", {})),
            validation=PermittivityValidationResult.from_dict(payload.get("validation", {})),
            reference_comparisons=payload.get("reference_comparisons", []),
            identified_materials=payload.get("identified_materials", []),
            confidence_estimate=payload.get("confidence_estimate", "Low"),
            metadata=payload.get("metadata", {}),
        )

    def comparisons_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.reference_comparisons)


def run_permittivity_measurement(
    measurement: MeasurementData,
    geometry: SensorGeometryProfile,
    *,
    method: str = "stuchly",
    calibration_profile: CalibrationProfile | None = None,
    open_measurement: MeasurementData | None = None,
    short_measurement: MeasurementData | None = None,
    load_measurement: MeasurementData | None = None,
    reference_materials: list[dict[str, Any]] | None = None,
) -> PermittivityMeasurementResult:
    spectrum, processed_measurement = compute_material_spectrum(
        measurement,
        geometry,
        method=method,
        calibration_profile=calibration_profile,
        open_measurement=open_measurement,
        short_measurement=short_measurement,
        load_measurement=load_measurement,
    )

    if reference_materials is None:
        reference_materials = list(load_reference_materials().values())

    validation = validate_permittivity_measurement(
        spectrum,
        processed_measurement,
        calibration_profile=calibration_profile,
        reference_materials=reference_materials,
    )
    reference_comparisons = compare_to_reference_materials(spectrum, reference_materials)
    identified_materials = identify_closest_materials(spectrum, reference_materials, limit=5)
    return PermittivityMeasurementResult(
        spectrum=spectrum,
        processed_measurement=processed_measurement,
        validation=validation,
        reference_comparisons=reference_comparisons,
        identified_materials=identified_materials,
        confidence_estimate=validation.confidence_label,
        metadata={"method": method, "sensor_type": geometry.sensor_type},
    )
