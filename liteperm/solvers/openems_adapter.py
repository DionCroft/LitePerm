"""openEMS adapter scaffold for LitePerm full-wave workflows."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from liteperm.io.parsers import load_measurement
from liteperm.models.core import SensorGeometryProfile, SweepConfig
from liteperm.solvers.base import FullWaveSolverAdapter
from liteperm.solvers.exporters import export_csv, export_touchstone
from liteperm.solvers.job import SimulationJob
from liteperm.solvers.result import SimulationResult
from liteperm.solvers.utils import simulation_cache_key, write_json
from liteperm.solvers.validators import environment_status, validate_simulation_job


class OpenEMSAdapter(FullWaveSolverAdapter):
    name = "openems"
    description = "openEMS adapter with exported patch-sensor projects and LitePerm baseline result parsing."
    supported_sensor_types = [
        "patch_antenna",
        "open_ended_coax_probe",
        "microstrip_resonator",
        "generic_resonator",
    ]
    support_level = "adapter_scaffold"
    executable_candidates = ("openEMS", "openEMS.exe")

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
        if executable:
            return environment_status(
                available=True,
                status="available",
                executable=executable,
                version="detected",
                setup_guide="docs/openems_setup_guide.md",
                messages=[
                    "openEMS was detected. LitePerm will export a baseline project scaffold and generate a forward-response baseline for workflow validation."
                ],
                metadata=self.metadata(),
            )
        return environment_status(
            available=False,
            status="missing",
            setup_guide="docs/openems_setup_guide.md",
            messages=[
                "openEMS was not detected on this machine.",
                "Install openEMS first, then restart LitePerm and rerun the simulation.",
            ],
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
            job_id=kwargs.get("job_id", f"openems-{uuid4().hex[:8]}"),
            solver_name=self.name,
            sensor_type=sensor_model.sensor_type,
            geometry_profile=sensor_model,
            material_stack=material_stack,
            sweep_config=sweep_config,
            output_directory=output_dir,
            boundary_conditions=kwargs.get(
                "boundary_conditions",
                {"x": "PML", "y": "PML", "z": "PML", "ground_plane": "PEC"},
            ),
            mesh_settings=kwargs.get("mesh_settings", {"quality": "medium", "cells_per_wavelength": 20}),
            excitation_settings=kwargs.get("excitation_settings", {"port": "lumped_feed", "output_power": 0}),
            notes=kwargs.get("notes", "LitePerm openEMS simulation job"),
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
        project_script = output_dir / "openems_patch_antenna_project.py"
        geometry_payload = {
            "job": job.to_dict(),
            "notes": [
                "This scaffold captures the geometry, sweep, and material stack that LitePerm would hand to openEMS.",
                "Patch antenna geometry is the first supported example in this adapter pathway.",
            ],
        }
        script = f'''"""LitePerm openEMS project scaffold.

This file is intentionally simple and documents the exported simulation inputs.
Extend it with your preferred Python-based openEMS workflow.
"""

JOB = {geometry_payload!r}

if __name__ == "__main__":
    print("LitePerm openEMS scaffold")
    print("Job ID:", JOB["job"]["job_id"])
    print("Sensor:", JOB["job"]["sensor_type"])
'''
        project_script.write_text(script, encoding="utf-8")
        geometry_file = write_json(output_dir / "geometry_export.json", geometry_payload)
        job.status = "exported"
        write_json(output_dir / "simulation_job.json", job.to_dict())
        return [project_script, geometry_file]

    def run(self, job: SimulationJob) -> SimulationResult:
        environment = self.validate_environment()
        if not environment["available"]:
            raise RuntimeError(
                "openEMS is not installed. See docs/openems_setup_guide.md for setup steps before running LitePerm full-wave simulations."
            )

        output_dir = job.output_path
        output_dir.mkdir(parents=True, exist_ok=True)
        self.export_geometry(job)
        job.status = "running"
        write_json(output_dir / "simulation_job.json", job.to_dict())

        started_at = time.perf_counter()
        from liteperm.inverse.forward_models import build_forward_model

        baseline_model = build_forward_model(
            job.sensor_type,
            geometry=job.geometry_profile,
            layer_stack=job.material_stack,
        )
        baseline_simulation = baseline_model.simulate(job.frequency_axis_hz)
        solver_metadata = baseline_simulation.metadata | {
            "solver_name": self.name,
            "sensor_type": job.sensor_type,
            "cache_key": job.cache_key,
            "job_id": job.job_id,
            "execution_mode": "adapter_scaffold",
            "adapter_note": "openEMS environment detected; LitePerm exported a solver scaffold and generated a baseline response for integration testing.",
        }
        result = SimulationResult.from_measurement(
            baseline_simulation.measurement,
            solver_metadata=solver_metadata,
            runtime_seconds=time.perf_counter() - started_at,
            output_files={},
        )
        touchstone_path = export_touchstone(result, output_dir / "simulated_response.s1p")
        csv_path = export_csv(result, output_dir / "simulated_response.csv")
        result.touchstone_export_path = str(touchstone_path)
        result.csv_export_path = str(csv_path)
        result.output_files = {
            "touchstone": str(touchstone_path),
            "csv": str(csv_path),
            "job": str(output_dir / "simulation_job.json"),
            "geometry": str(output_dir / "geometry_export.json"),
        }
        job.status = "completed"
        write_json(output_dir / "simulation_job.json", job.to_dict())
        write_json(output_dir / "simulation_result.json", result.to_dict())
        return result

    def parse_results(self, job: SimulationJob) -> SimulationResult:
        output_dir = job.output_path
        touchstone_path = output_dir / "simulated_response.s1p"
        csv_path = output_dir / "simulated_response.csv"
        metadata_path = output_dir / "simulation_result.json"
        if metadata_path.exists():
            return SimulationResult.from_dict(json.loads(metadata_path.read_text(encoding="utf-8")))
        if touchstone_path.exists():
            measurement = load_measurement(touchstone_path)
            return SimulationResult.from_measurement(
                measurement,
                solver_metadata={
                    "solver_name": self.name,
                    "sensor_type": job.sensor_type,
                    "cache_key": job.cache_key,
                    "job_id": job.job_id,
                },
                output_files={"touchstone": str(touchstone_path)},
                touchstone_export_path=str(touchstone_path),
                csv_export_path=str(csv_path) if csv_path.exists() else "",
            )
        if csv_path.exists():
            measurement = load_measurement(csv_path)
            return SimulationResult.from_measurement(
                measurement,
                solver_metadata={
                    "solver_name": self.name,
                    "sensor_type": job.sensor_type,
                    "cache_key": job.cache_key,
                    "job_id": job.job_id,
                },
                output_files={"csv": str(csv_path)},
                csv_export_path=str(csv_path),
            )
        raise FileNotFoundError(f"No simulation outputs were found for job `{job.job_id}` in `{output_dir}`.")

    def cleanup(self, job: SimulationJob) -> None:
        return None
