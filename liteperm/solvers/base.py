"""Base abstractions for full-wave solver integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from liteperm.inverse.common import LayerStack
from liteperm.models.core import SensorGeometryProfile, SweepConfig
from liteperm.solvers.job import SimulationJob
from liteperm.solvers.result import SimulationResult


class FullWaveSolverAdapter(ABC):
    name = "base"
    description = "Base full-wave solver adapter"
    supported_sensor_types: list[str] = []
    support_level = "placeholder"

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the solver runtime is available on this machine."""

    @abstractmethod
    def validate_environment(self) -> dict[str, Any]:
        """Return structured environment and setup information."""

    @abstractmethod
    def build_job(
        self,
        sensor_model: SensorGeometryProfile,
        material_stack: LayerStack,
        sweep_config: SweepConfig,
        output_dir: str | Path,
        **kwargs: Any,
    ) -> SimulationJob:
        """Create a formal simulation job."""

    @abstractmethod
    def export_geometry(self, job: SimulationJob) -> list[Path]:
        """Export geometry and project files required by the external solver."""

    @abstractmethod
    def run(self, job: SimulationJob) -> SimulationResult:
        """Execute a simulation job and return the resulting S-parameters."""

    @abstractmethod
    def parse_results(self, job: SimulationJob) -> SimulationResult:
        """Parse previously written solver outputs from disk."""

    @abstractmethod
    def cleanup(self, job: SimulationJob) -> None:
        """Perform any adapter-specific cleanup once the job is complete."""

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "supported_sensor_types": self.supported_sensor_types,
            "support_level": self.support_level,
        }


class PlaceholderSolverAdapter(FullWaveSolverAdapter):
    def __init__(self, *, name: str, description: str, supported_sensor_types: list[str], setup_guide: str = "") -> None:
        self.name = name
        self.description = description
        self.supported_sensor_types = supported_sensor_types
        self.support_level = "placeholder"
        self.setup_guide = setup_guide

    def is_available(self) -> bool:
        return False

    def validate_environment(self) -> dict[str, Any]:
        return {
            "available": False,
            "status": "placeholder",
            "executable": "",
            "version": "not_applicable",
            "setup_guide": self.setup_guide,
            "messages": [
                f"{self.name} is registered as a future solver target for LitePerm, but this adapter is not implemented yet."
            ],
            "metadata": self.metadata(),
        }

    def build_job(
        self,
        sensor_model: SensorGeometryProfile,
        material_stack: LayerStack,
        sweep_config: SweepConfig,
        output_dir: str | Path,
        **kwargs: Any,
    ) -> SimulationJob:
        raise NotImplementedError(f"{self.name} is only available as a placeholder in this LitePerm release.")

    def export_geometry(self, job: SimulationJob) -> list[Path]:
        raise NotImplementedError(f"{self.name} geometry export is not implemented.")

    def run(self, job: SimulationJob) -> SimulationResult:
        raise NotImplementedError(f"{self.name} simulation execution is not implemented.")

    def parse_results(self, job: SimulationJob) -> SimulationResult:
        raise NotImplementedError(f"{self.name} result parsing is not implemented.")

    def cleanup(self, job: SimulationJob) -> None:
        return None
