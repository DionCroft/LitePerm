"""Full-wave forward-model wrapper for solver-backed inverse workflows."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np

from liteperm.inverse.common import ForwardSimulation, ParameterDefinition
from liteperm.inverse.forward_models.base import ForwardModel
from liteperm.inverse.forward_models.generic_resonator import GenericResonatorModel
from liteperm.inverse.forward_models.microstrip_resonator import MicrostripResonatorModel
from liteperm.inverse.forward_models.open_ended_coax_probe import OpenEndedCoaxProbeModel
from liteperm.inverse.forward_models.patch_antenna import PatchAntennaModel
from liteperm.solvers.registry import build_solver_adapter
from liteperm.solvers.utils import cache_directory, simulation_cache_key, sweep_config_from_frequency_axis


ANALYTICAL_MODEL_REGISTRY = {
    "patch_antenna": PatchAntennaModel,
    "open_ended_coax_probe": OpenEndedCoaxProbeModel,
    "microstrip_resonator": MicrostripResonatorModel,
    "generic_resonator": GenericResonatorModel,
}


class FullWaveForwardModel(ForwardModel):
    def _analytical_model(self) -> ForwardModel:
        model_cls = ANALYTICAL_MODEL_REGISTRY.get(self.geometry.sensor_type, GenericResonatorModel)
        return model_cls(
            geometry=self.geometry,
            layer_stack=self.layer_stack,
            z0=self.z0,
            metadata_overrides=dict(self.metadata_overrides),
        )

    def _annotate(self, simulation: ForwardSimulation, **metadata: Any) -> ForwardSimulation:
        simulation.metadata.update(metadata)
        return simulation

    def _fallback_or_raise(self, frequency_hz: np.ndarray, *, backend: str, reason: str) -> ForwardSimulation:
        if not self.metadata_overrides.get("allow_analytical_fallback", False):
            raise RuntimeError(reason)
        fallback = self._analytical_model().simulate(frequency_hz)
        return self._annotate(
            fallback,
            forward_backend="analytical_fallback",
            requested_backend=backend,
            fallback_reason=reason,
        )

    def simulate(self, frequency_hz: np.ndarray) -> ForwardSimulation:
        backend = str(self.metadata_overrides.get("simulation_backend", "analytical")).strip().lower()
        frequency_hz = np.asarray(frequency_hz, dtype=float)
        analytical_model = self._analytical_model()

        if backend == "analytical":
            return self._annotate(
                analytical_model.simulate(frequency_hz),
                forward_backend="analytical",
                requested_backend="analytical",
                solver_name="analytical",
            )

        if backend == "surrogate":
            return self._fallback_or_raise(
                frequency_hz,
                backend=backend,
                reason="Surrogate full-wave forward models are reserved for a future LitePerm release.",
            )

        solver_name = str(self.metadata_overrides.get("solver_name", "openems")).strip().lower()
        adapter = build_solver_adapter(solver_name)
        sweep_config = sweep_config_from_frequency_axis(frequency_hz)
        project_name = str(self.metadata_overrides.get("project_name", "LitePerm Research"))
        mesh_settings = dict(self.metadata_overrides.get("mesh_settings", {}))
        boundary_conditions = dict(self.metadata_overrides.get("boundary_conditions", {}))
        excitation_settings = dict(self.metadata_overrides.get("excitation_settings", {}))
        cache_key = simulation_cache_key(
            solver_name=solver_name,
            sensor_type=self.geometry.sensor_type,
            geometry_profile=self.geometry,
            material_stack=self.layer_stack,
            sweep_config=sweep_config,
            mesh_settings=mesh_settings,
            boundary_conditions=boundary_conditions,
            excitation_settings=excitation_settings,
        )
        output_dir = cache_directory(project_name, cache_key)
        job = adapter.build_job(
            self.geometry,
            self.layer_stack,
            sweep_config,
            output_dir,
            mesh_settings=mesh_settings,
            boundary_conditions=boundary_conditions,
            excitation_settings=excitation_settings,
            cache_key=cache_key,
            metadata={"project_name": project_name, "invoked_from": "inverse_model"},
        )

        result_path = output_dir / "simulation_result.json"
        try:
            if backend == "cached":
                if not result_path.exists() and not (output_dir / "simulated_response.s1p").exists():
                    raise FileNotFoundError(
                        f"No cached simulation result exists for `{solver_name}` with cache key `{cache_key}`."
                    )
                result = adapter.parse_results(job)
            else:
                force_rerun = bool(self.metadata_overrides.get("force_rerun", False))
                if result_path.exists() and not force_rerun:
                    result = adapter.parse_results(job)
                else:
                    result = adapter.run(job)
        except Exception as error:
            return self._fallback_or_raise(frequency_hz, backend=backend, reason=str(error))

        simulation = result.to_forward_simulation(layer_stack=self.layer_stack)
        simulation.metadata.update(
            {
                "forward_backend": backend,
                "requested_backend": backend,
                "solver_name": solver_name,
                "cache_key": cache_key,
                "project_name": project_name,
            }
        )
        return simulation

    def validate(self) -> list[str]:
        issues = self._analytical_model().validate()
        backend = str(self.metadata_overrides.get("simulation_backend", "analytical")).strip().lower()
        if backend == "analytical":
            issues.append("FullWaveForwardModel is currently using the analytical backend for speed and solver-free validation.")
            return issues

        solver_name = str(self.metadata_overrides.get("solver_name", "openems")).strip().lower()
        adapter = build_solver_adapter(solver_name)
        environment = adapter.validate_environment()
        if not environment.get("available") and backend != "cached":
            issues.append(
                f"{solver_name} is not installed on this machine. See {environment.get('setup_guide', 'the setup guide')} before running full-wave jobs."
            )
        for message in environment.get("messages", []):
            issues.append(message)
        return issues

    def parameters(self) -> list[ParameterDefinition]:
        return [replace(definition) for definition in self._analytical_model().parameters()]

    def constraints(self) -> dict[str, Any]:
        base_constraints = dict(self._analytical_model().constraints())
        base_constraints.update({"supports_cached_results": True, "supports_solver_execution": True})
        return base_constraints

    def metadata(self) -> dict[str, Any]:
        backend = str(self.metadata_overrides.get("simulation_backend", "analytical")).strip().lower()
        solver_name = str(self.metadata_overrides.get("solver_name", "openems")).strip().lower()
        return {
            "name": "Full-Wave Forward Model",
            "description": "Solver-backed forward model wrapper for simulation-assisted inverse electromagnetic modelling.",
            "support_level": "phase4",
            "simulation_backend": backend,
            "solver_name": solver_name,
            "sensor_type": self.geometry.sensor_type,
            "future_integrations": ["openEMS", "Meep", "HFSS", "CST", "COMSOL", "surrogate_models"],
        }
