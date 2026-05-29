"""Utility helpers for full-wave solver integrations and caching."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from liteperm.inverse.common import LayerStack
from liteperm.models.core import SensorGeometryProfile, SweepConfig
from liteperm.utils.paths import PROJECTS_ROOT


def slugify_project_name(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_")
    return slug or "LitePerm_Project"


def project_simulation_root(project_name: str) -> Path:
    root = PROJECTS_ROOT / slugify_project_name(project_name) / "simulations"
    root.mkdir(parents=True, exist_ok=True)
    return root


def json_ready(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        if np.iscomplexobj(value):
            return {"real": value.real.tolist(), "imag": value.imag.tolist()}
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    return value


def simulation_cache_key(
    *,
    solver_name: str,
    sensor_type: str,
    geometry_profile: SensorGeometryProfile,
    material_stack: LayerStack,
    sweep_config: SweepConfig,
    mesh_settings: dict[str, Any] | None = None,
    boundary_conditions: dict[str, Any] | None = None,
    excitation_settings: dict[str, Any] | None = None,
) -> str:
    payload = {
        "solver_name": solver_name,
        "sensor_type": sensor_type,
        "geometry_profile": geometry_profile.to_dict(),
        "material_stack": material_stack.to_dict(),
        "sweep_config": sweep_config.to_dict(),
        "mesh_settings": mesh_settings or {},
        "boundary_conditions": boundary_conditions or {},
        "excitation_settings": excitation_settings or {},
    }
    encoded = json.dumps(json_ready(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def cache_directory(project_name: str, cache_key: str) -> Path:
    path = project_simulation_root(project_name) / cache_key
    path.mkdir(parents=True, exist_ok=True)
    return path


def sweep_config_from_frequency_axis(frequency_hz: np.ndarray) -> SweepConfig:
    axis = np.asarray(frequency_hz, dtype=float)
    return SweepConfig(
        start_frequency_hz=float(axis.min()),
        stop_frequency_hz=float(axis.max()),
        points=int(axis.size),
        output_power=0,
        sweep_speed="simulation",
        average_count=1,
        channel="S11",
    )


def write_json(path: str | Path, payload: Any) -> Path:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(json_ready(payload), indent=2, sort_keys=True), encoding="utf-8")
    return file_path


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
