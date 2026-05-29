"""Permittivity-first measurement services for LitePerm Phase 5."""

from liteperm.permittivity.engine import PermittivityMeasurementResult, run_permittivity_measurement
from liteperm.permittivity.matching import compare_to_reference_materials, comparisons_to_frame, identify_closest_materials, normalise_material_payload
from liteperm.permittivity.validation import PermittivityValidationResult, ValidationCheck, validate_permittivity_measurement

__all__ = [
    "PermittivityMeasurementResult",
    "PermittivityValidationResult",
    "ValidationCheck",
    "run_permittivity_measurement",
    "validate_permittivity_measurement",
    "compare_to_reference_materials",
    "identify_closest_materials",
    "comparisons_to_frame",
    "normalise_material_payload",
]
