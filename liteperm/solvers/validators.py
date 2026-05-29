"""Validation helpers for full-wave simulation jobs and adapters."""

from __future__ import annotations

from typing import Any

from liteperm.solvers.job import SimulationJob


def validate_simulation_job(job: SimulationJob, *, supported_sensor_types: list[str] | None = None) -> list[str]:
    issues: list[str] = []
    if job.number_of_points < 2:
        issues.append("Simulation sweeps require at least two frequency points.")
    if job.sweep_start_frequency_hz <= 0:
        issues.append("Simulation start frequency must be positive.")
    if job.sweep_stop_frequency_hz <= job.sweep_start_frequency_hz:
        issues.append("Simulation stop frequency must be greater than the start frequency.")
    if supported_sensor_types and job.sensor_type not in supported_sensor_types:
        issues.append(
            f"Solver `{job.solver_name}` does not support sensor type `{job.sensor_type}`. "
            f"Supported types: {', '.join(supported_sensor_types)}."
        )
    if not job.geometry_profile.parameters:
        issues.append("A populated geometry profile is required before exporting a simulation job.")
    if not job.material_stack.layers:
        issues.append("A material stack is required before exporting a simulation job.")
    return issues


def environment_status(
    *,
    available: bool,
    status: str,
    executable: str = "",
    version: str = "",
    setup_guide: str = "",
    messages: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "available": available,
        "status": status,
        "executable": executable,
        "version": version or "unknown",
        "setup_guide": setup_guide,
        "messages": messages or [],
        "metadata": metadata or {},
    }
