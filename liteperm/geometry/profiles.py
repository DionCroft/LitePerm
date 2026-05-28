"""Geometry profile creation and persistence."""

from __future__ import annotations

from pathlib import Path

from liteperm.models.core import SensorGeometryProfile
from liteperm.utils.paths import GEOMETRY_LIBRARY_ROOT, ensure_runtime_directories
from liteperm.utils.yaml_io import dump_yaml, load_yaml, write_yaml


DEFAULT_GEOMETRIES: dict[str, dict[str, float | str]] = {
    "patch_antenna": {
        "length_mm": 32.0,
        "width_mm": 38.0,
        "substrate_height_mm": 1.6,
        "substrate_permittivity": 4.3,
        "feed_position_mm": 7.0,
        "ground_plane_length_mm": 60.0,
        "ground_plane_width_mm": 60.0,
        "sensing_region_length_mm": 18.0,
        "sensing_region_width_mm": 18.0,
        "protective_layer_thickness_mm": 0.1,
    },
    "open_ended_coax_probe": {
        "inner_radius_mm": 0.6,
        "outer_radius_mm": 2.05,
        "flange_radius_mm": 6.0,
        "cable_permittivity": 2.1,
    },
    "microstrip_resonator": {
        "line_length_mm": 42.0,
        "line_width_mm": 3.2,
        "substrate_height_mm": 1.6,
        "substrate_permittivity": 3.48,
        "coupling_gap_mm": 0.4,
        "sensing_window_length_mm": 15.0,
    },
    "csrr_structure": {
        "outer_radius_mm": 8.0,
        "ring_width_mm": 0.8,
        "gap_mm": 0.5,
        "substrate_height_mm": 1.6,
        "substrate_permittivity": 3.48,
    },
    "generic_resonator": {
        "effective_capacitance_pf": 0.85,
        "effective_volume_mm3": 1000.0,
        "user_parameter_1": 0.0,
        "user_parameter_2": 0.0,
    },
}


def build_geometry_profile(
    sensor_type: str,
    *,
    name: str | None = None,
    parameters: dict[str, float | str] | None = None,
    notes: str = "",
) -> SensorGeometryProfile:
    if sensor_type not in DEFAULT_GEOMETRIES:
        raise KeyError(f"Unsupported sensor type: {sensor_type}")
    merged = dict(DEFAULT_GEOMETRIES[sensor_type])
    if parameters:
        merged.update(parameters)
    return SensorGeometryProfile(
        name=name or sensor_type.replace("_", " ").title(),
        sensor_type=sensor_type,
        parameters=merged,
        notes=notes,
    )


def save_geometry_profile(path: str | Path, profile: SensorGeometryProfile) -> Path:
    return write_yaml(path, profile.to_dict())


def load_geometry_profile(path: str | Path) -> SensorGeometryProfile:
    payload = load_yaml(path) or {}
    return SensorGeometryProfile(
        name=payload.get("name", "Imported Geometry"),
        sensor_type=payload.get("sensor_type", "generic_resonator"),
        parameters=payload.get("parameters", {}),
        notes=payload.get("notes", ""),
        metadata=payload.get("metadata", {}),
    )


def geometry_profile_to_yaml(profile: SensorGeometryProfile) -> str:
    return dump_yaml(profile.to_dict())


def save_geometry_profile_to_library(profile: SensorGeometryProfile) -> Path:
    ensure_runtime_directories()
    destination = GEOMETRY_LIBRARY_ROOT / f"{profile.name.replace(' ', '_').lower()}.yaml"
    return save_geometry_profile(destination, profile)


def list_saved_geometry_profiles() -> list[dict[str, str]]:
    ensure_runtime_directories()
    profiles = []
    for path in sorted(GEOMETRY_LIBRARY_ROOT.glob("*.yaml")):
        profiles.append({"name": path.stem, "path": str(path)})
    return profiles
