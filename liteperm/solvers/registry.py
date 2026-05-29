"""Registry and discovery helpers for full-wave solver adapters."""

from __future__ import annotations

from liteperm.solvers.base import FullWaveSolverAdapter, PlaceholderSolverAdapter
from liteperm.solvers.meep_adapter import MeepAdapter
from liteperm.solvers.openems_adapter import OpenEMSAdapter


def discover_solver_adapters() -> dict[str, FullWaveSolverAdapter]:
    return {
        "openems": OpenEMSAdapter(),
        "meep": MeepAdapter(),
        "hfss": PlaceholderSolverAdapter(
            name="hfss",
            description="ANSYS HFSS integration target for future LitePerm enterprise and academic workflows.",
            supported_sensor_types=["patch_antenna", "microstrip_resonator", "generic_resonator", "open_ended_coax_probe"],
        ),
        "cst": PlaceholderSolverAdapter(
            name="cst",
            description="CST Studio Suite integration target for future LitePerm high-fidelity simulation workflows.",
            supported_sensor_types=["patch_antenna", "microstrip_resonator", "generic_resonator", "open_ended_coax_probe"],
        ),
        "comsol": PlaceholderSolverAdapter(
            name="comsol",
            description="COMSOL Multiphysics integration target for future LitePerm multiphysics workflows.",
            supported_sensor_types=["patch_antenna", "microstrip_resonator", "generic_resonator", "open_ended_coax_probe"],
        ),
    }


def build_solver_adapter(name: str) -> FullWaveSolverAdapter:
    registry = discover_solver_adapters()
    key = str(name).strip().lower()
    if key not in registry:
        raise KeyError(f"Unknown full-wave solver adapter: {name}")
    return registry[key]


def solver_status_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, adapter in discover_solver_adapters().items():
        environment = adapter.validate_environment()
        rows.append(
            {
                "solver": name,
                "status": environment.get("status", "unknown"),
                "available": "yes" if environment.get("available") else "no",
                "version": environment.get("version", "unknown"),
                "supported_sensor_types": ", ".join(adapter.supported_sensor_types),
                "setup_guide": environment.get("setup_guide", ""),
            }
        )
    return rows
