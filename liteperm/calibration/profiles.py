"""Calibration profile storage."""

from __future__ import annotations

from pathlib import Path

from liteperm.models.core import CalibrationProfile
from liteperm.utils.yaml_io import dump_yaml, load_yaml, write_yaml


def _complex_from_mapping(value: dict[str, float] | complex | None, fallback: complex) -> complex:
    if value is None:
        return fallback
    if isinstance(value, complex):
        return value
    return complex(float(value.get("real", fallback.real)), float(value.get("imag", fallback.imag)))


def build_calibration_profile(
    name: str,
    *,
    reference_materials: list[str] | None = None,
    open_gamma: complex = complex(1.0, 0.0),
    short_gamma: complex = complex(-1.0, 0.0),
    load_gamma: complex = complex(0.0, 0.0),
    notes: str = "",
    metadata: dict[str, str] | None = None,
) -> CalibrationProfile:
    return CalibrationProfile(
        name=name,
        open_gamma=open_gamma,
        short_gamma=short_gamma,
        load_gamma=load_gamma,
        reference_materials=reference_materials or [],
        notes=notes,
        metadata=metadata or {},
    )


def save_calibration_profile(path: str | Path, profile: CalibrationProfile) -> Path:
    return write_yaml(path, profile.to_dict())


def load_calibration_profile(path: str | Path) -> CalibrationProfile:
    payload = load_yaml(path) or {}
    standards = payload.get("actual_standards", {})
    return CalibrationProfile(
        name=payload.get("name", "Imported Calibration"),
        open_gamma=_complex_from_mapping(standards.get("open_gamma"), complex(1.0, 0.0)),
        short_gamma=_complex_from_mapping(standards.get("short_gamma"), complex(-1.0, 0.0)),
        load_gamma=_complex_from_mapping(standards.get("load_gamma"), complex(0.0, 0.0)),
        reference_materials=payload.get("reference_materials", []),
        notes=payload.get("notes", ""),
        metadata=payload.get("metadata", {}),
    )


def calibration_profile_to_yaml(profile: CalibrationProfile) -> str:
    return dump_yaml(profile.to_dict())

