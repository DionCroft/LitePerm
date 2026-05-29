"""Export helpers for simulation results."""

from __future__ import annotations

from pathlib import Path

from liteperm.io.exporters import dataframe_to_csv_bytes, measurement_to_touchstone_bytes
from liteperm.solvers.result import SimulationResult


def export_touchstone(result: SimulationResult, destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(measurement_to_touchstone_bytes(result.measurement))
    return path


def export_csv(result: SimulationResult, destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dataframe_to_csv_bytes(result.to_dataframe()))
    return path
