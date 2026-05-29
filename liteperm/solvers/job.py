"""Formal simulation-job model for full-wave solver integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from liteperm.inverse.common import LayerStack
from liteperm.models.core import SensorGeometryProfile, SweepConfig


VALID_JOB_STATUSES = {
    "created",
    "validated",
    "exported",
    "running",
    "completed",
    "failed",
    "cancelled",
}


@dataclass(slots=True)
class SimulationJob:
    job_id: str
    solver_name: str
    sensor_type: str
    geometry_profile: SensorGeometryProfile
    material_stack: LayerStack
    sweep_start_frequency_hz: float
    sweep_stop_frequency_hz: float
    number_of_points: int
    boundary_conditions: dict[str, Any] = field(default_factory=dict)
    mesh_settings: dict[str, Any] = field(default_factory=dict)
    excitation_settings: dict[str, Any] = field(default_factory=dict)
    output_directory: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: str = "created"
    notes: str = ""
    cache_key: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.geometry_profile, dict):
            self.geometry_profile = SensorGeometryProfile.from_dict(self.geometry_profile)
        if isinstance(self.material_stack, dict):
            self.material_stack = LayerStack.from_dict(self.material_stack)

        self.solver_name = str(self.solver_name).strip().lower()
        self.sensor_type = str(self.sensor_type).strip().lower() or self.geometry_profile.sensor_type
        self.sweep_start_frequency_hz = float(self.sweep_start_frequency_hz)
        self.sweep_stop_frequency_hz = float(self.sweep_stop_frequency_hz)
        self.number_of_points = int(self.number_of_points)
        self.output_directory = str(Path(self.output_directory)) if self.output_directory else ""

        if self.status not in VALID_JOB_STATUSES:
            raise ValueError(f"Unsupported simulation job status: {self.status}")
        if self.number_of_points < 2:
            raise ValueError("Simulation jobs require at least two frequency points.")
        if self.sweep_stop_frequency_hz <= self.sweep_start_frequency_hz:
            raise ValueError("Stop frequency must be greater than start frequency.")

    @property
    def output_path(self) -> Path:
        return Path(self.output_directory)

    @property
    def sweep_config(self) -> SweepConfig:
        return SweepConfig(
            start_frequency_hz=self.sweep_start_frequency_hz,
            stop_frequency_hz=self.sweep_stop_frequency_hz,
            points=self.number_of_points,
            output_power=int(self.excitation_settings.get("output_power", 0)),
            sweep_speed=str(self.metadata.get("sweep_speed", "simulation")),
            average_count=1,
            channel="S11",
        )

    @property
    def frequency_axis_hz(self) -> np.ndarray:
        return np.linspace(
            self.sweep_start_frequency_hz,
            self.sweep_stop_frequency_hz,
            self.number_of_points,
            dtype=float,
        )

    @classmethod
    def from_sweep_config(
        cls,
        *,
        job_id: str,
        solver_name: str,
        sensor_type: str,
        geometry_profile: SensorGeometryProfile,
        material_stack: LayerStack,
        sweep_config: SweepConfig,
        output_directory: str | Path,
        boundary_conditions: dict[str, Any] | None = None,
        mesh_settings: dict[str, Any] | None = None,
        excitation_settings: dict[str, Any] | None = None,
        notes: str = "",
        cache_key: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "SimulationJob":
        return cls(
            job_id=job_id,
            solver_name=solver_name,
            sensor_type=sensor_type,
            geometry_profile=geometry_profile,
            material_stack=material_stack,
            sweep_start_frequency_hz=float(sweep_config.start_frequency_hz),
            sweep_stop_frequency_hz=float(sweep_config.stop_frequency_hz),
            number_of_points=int(sweep_config.points),
            boundary_conditions=boundary_conditions or {},
            mesh_settings=mesh_settings or {},
            excitation_settings=excitation_settings or {"output_power": int(sweep_config.output_power)},
            output_directory=str(output_directory),
            notes=notes,
            cache_key=cache_key,
            metadata=(metadata or {}) | {"sweep_speed": sweep_config.sweep_speed},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "solver_name": self.solver_name,
            "sensor_type": self.sensor_type,
            "geometry_profile": self.geometry_profile.to_dict(),
            "material_stack": self.material_stack.to_dict(),
            "sweep_start_frequency_hz": float(self.sweep_start_frequency_hz),
            "sweep_stop_frequency_hz": float(self.sweep_stop_frequency_hz),
            "number_of_points": int(self.number_of_points),
            "boundary_conditions": self.boundary_conditions,
            "mesh_settings": self.mesh_settings,
            "excitation_settings": self.excitation_settings,
            "output_directory": self.output_directory,
            "timestamp": self.timestamp,
            "status": self.status,
            "notes": self.notes,
            "cache_key": self.cache_key,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SimulationJob":
        return cls(
            job_id=payload.get("job_id", ""),
            solver_name=payload.get("solver_name", ""),
            sensor_type=payload.get("sensor_type", "generic_resonator"),
            geometry_profile=SensorGeometryProfile.from_dict(payload.get("geometry_profile", {})),
            material_stack=LayerStack.from_dict(payload.get("material_stack", {})),
            sweep_start_frequency_hz=float(payload.get("sweep_start_frequency_hz", 0.0)),
            sweep_stop_frequency_hz=float(payload.get("sweep_stop_frequency_hz", 1.0)),
            number_of_points=int(payload.get("number_of_points", 2)),
            boundary_conditions=payload.get("boundary_conditions", {}),
            mesh_settings=payload.get("mesh_settings", {}),
            excitation_settings=payload.get("excitation_settings", {}),
            output_directory=payload.get("output_directory", ""),
            timestamp=payload.get("timestamp", datetime.now(UTC).isoformat()),
            status=payload.get("status", "created"),
            notes=payload.get("notes", ""),
            cache_key=payload.get("cache_key", ""),
            metadata=payload.get("metadata", {}),
        )
