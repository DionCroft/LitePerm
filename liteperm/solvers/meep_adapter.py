"""Meep adapter scaffold for future LitePerm full-wave integrations."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from liteperm.models.core import SensorGeometryProfile, SweepConfig
from liteperm.solvers.base import FullWaveSolverAdapter
from liteperm.solvers.job import SimulationJob
from liteperm.solvers.result import SimulationResult
from liteperm.solvers.utils import simulation_cache_key, write_json
from liteperm.solvers.validators import environment_status, validate_simulation_job


class MeepAdapter(FullWaveSolverAdapter):
    name = "meep"
    description = "Meep adapter scaffold for resonator-oriented future full-wave modelling."
    supported_sensor_types = [
        "microstrip_resonator",
        "generic_resonator",
        "patch_antenna",
        "open_ended_coax_probe",
    ]
    support_level = "scaffold"
    executable_candidates = ("meep", "meep.exe")

    def _find_executable(self) -> str:
        for candidate in self.executable_candidates:
            executable = shutil.which(candidate)
            if executable:
                return executable
        return ""

    def is_available(self) -> bool:
        return bool(self._find_executable())

    def validate_environment(self) -> dict[str, Any]:
        executable = self._find_executable()
        messages = [
            "The Meep adapter is present as a scaffold for future resonator and research workflows.",
            "LitePerm currently exports a placeholder project definition but does not yet execute full Meep simulations end-to-end.",
        ]
        return environment_status(
            available=bool(executable),
            status="scaffold" if executable else "missing",
            executable=executable,
            version="detected" if executable else "unknown",
            setup_guide="docs/meep_setup_guide.md",
            messages=messages if executable else ["Meep was not detected on this machine."] + messages,
            metadata=self.metadata(),
        )

    def build_job(
        self,
        sensor_model: SensorGeometryProfile,
        material_stack,
        sweep_config: SweepConfig,
        output_dir: str | Path,
        **kwargs: Any,
    ) -> SimulationJob:
        job = SimulationJob.from_sweep_config(
            job_id=kwargs.get("job_id", f"meep-{uuid4().hex[:8]}"),
            solver_name=self.name,
            sensor_type=sensor_model.sensor_type,
            geometry_profile=sensor_model,
            material_stack=material_stack,
            sweep_config=sweep_config,
            output_directory=output_dir,
            boundary_conditions=kwargs.get("boundary_conditions", {"x": "PML", "y": "PML", "z": "PML"}),
            mesh_settings=kwargs.get("mesh_settings", {"resolution": 20, "quality": "medium"}),
            excitation_settings=kwargs.get("excitation_settings", {"source_type": "gaussian"}),
            notes=kwargs.get("notes", "LitePerm Meep placeholder job"),
            cache_key=kwargs.get(
                "cache_key",
                simulation_cache_key(
                    solver_name=self.name,
                    sensor_type=sensor_model.sensor_type,
                    geometry_profile=sensor_model,
                    material_stack=material_stack,
                    sweep_config=sweep_config,
                    mesh_settings=kwargs.get("mesh_settings"),
                    boundary_conditions=kwargs.get("boundary_conditions"),
                    excitation_settings=kwargs.get("excitation_settings"),
                ),
            ),
            metadata=kwargs.get("metadata", {}),
        )
        issues = validate_simulation_job(job, supported_sensor_types=self.supported_sensor_types)
        if issues:
            raise ValueError("; ".join(issues))
        return job

    def export_geometry(self, job: SimulationJob) -> list[Path]:
        output_dir = job.output_path
        output_dir.mkdir(parents=True, exist_ok=True)
        project_file = output_dir / "meep_resonator_placeholder.py"
        project_file.write_text(
            '''"""LitePerm Meep placeholder export.

This file captures the intended Meep job configuration for future development.
"""

if __name__ == "__main__":
    print("LitePerm Meep scaffold placeholder")
''',
            encoding="utf-8",
        )
        manifest = write_json(output_dir / "meep_job.json", job.to_dict())
        job.status = "exported"
        return [project_file, manifest]

    def run(self, job: SimulationJob) -> SimulationResult:
        self.export_geometry(job)
        raise NotImplementedError(
            "The Meep adapter scaffold is available, but full simulation execution is not implemented in this LitePerm release."
        )

    def parse_results(self, job: SimulationJob) -> SimulationResult:
        raise FileNotFoundError(
            f"No parsed Meep result is available for job `{job.job_id}` yet. Export the scaffold and complete the solver workflow externally first."
        )

    def cleanup(self, job: SimulationJob) -> None:
        return None
