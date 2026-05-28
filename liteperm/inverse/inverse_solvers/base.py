"""Base inverse-solver implementation utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from liteperm.inverse.common import (
    ForwardSimulation,
    InverseProblem,
    InverseResult,
    clone_with_parameter_updates,
    parameter_mapping,
    residual_measurement,
    simulation_to_measurement,
)
from liteperm.inverse.forward_models.base import ForwardModel
from liteperm.inverse.optimisers.error_metrics import compute_scalar_error, residual_vector


@dataclass(slots=True)
class SolverRunContext:
    model: ForwardModel
    problem: InverseProblem
    objective_history: list[float] = field(default_factory=list)
    parameter_history: list[dict[str, float]] = field(default_factory=list)

    def evaluate(self, vector: np.ndarray) -> tuple[float, ForwardSimulation]:
        updates = parameter_mapping(self.problem.parameter_definitions, vector)
        candidate_model = clone_with_parameter_updates(self.model, updates)
        simulation = candidate_model.simulate(self.problem.measured_measurement.frequency_hz)
        predicted = simulation_to_measurement(simulation)
        objective = compute_scalar_error(self.problem.measured_measurement, predicted, metric=self.problem.error_metric)
        parameter_snapshot = {
            definition.name: updates[definition.target_path]
            for definition in self.problem.parameter_definitions
            if definition.target_path in updates
        }
        self.objective_history.append(objective)
        self.parameter_history.append(parameter_snapshot)
        return objective, simulation

    def residual(self, vector: np.ndarray) -> np.ndarray:
        updates = parameter_mapping(self.problem.parameter_definitions, vector)
        candidate_model = clone_with_parameter_updates(self.model, updates)
        simulation = candidate_model.simulate(self.problem.measured_measurement.frequency_hz)
        predicted = simulation_to_measurement(simulation)
        objective = compute_scalar_error(self.problem.measured_measurement, predicted, metric=self.problem.error_metric)
        parameter_snapshot = {
            definition.name: updates[definition.target_path]
            for definition in self.problem.parameter_definitions
            if definition.target_path in updates
        }
        self.objective_history.append(objective)
        self.parameter_history.append(parameter_snapshot)
        return residual_vector(self.problem.measured_measurement, predicted, metric=self.problem.error_metric)


class InverseSolverBase(ABC):
    name = "base"

    @abstractmethod
    def solve(self, model: ForwardModel, problem: InverseProblem) -> InverseResult:
        """Estimate unknown parameters from a measured response."""

    def _build_result(
        self,
        *,
        model: ForwardModel,
        problem: InverseProblem,
        context: SolverRunContext,
        best_vector: np.ndarray,
    ) -> InverseResult:
        best_updates = parameter_mapping(problem.parameter_definitions, best_vector)
        best_model = clone_with_parameter_updates(model, best_updates)
        best_simulation = best_model.simulate(problem.measured_measurement.frequency_hz)
        predicted_measurement = simulation_to_measurement(best_simulation)
        residual = residual_measurement(problem.measured_measurement, predicted_measurement)
        objective_value = compute_scalar_error(problem.measured_measurement, predicted_measurement, metric=problem.error_metric)
        convergence_trace = []
        for step_index, (objective, parameters) in enumerate(zip(context.objective_history, context.parameter_history, strict=False)):
            trace_row = {"step": float(step_index), "objective": float(objective)}
            trace_row.update(parameters)
            convergence_trace.append(trace_row)
        return InverseResult(
            solver_name=self.name,
            error_metric=problem.error_metric,
            best_parameters={definition.name: best_updates[definition.target_path] for definition in problem.parameter_definitions},
            objective_value=objective_value,
            predicted_simulation=best_simulation,
            residual_measurement=residual,
            objective_history=context.objective_history,
            parameter_history=context.parameter_history,
            convergence_trace=convergence_trace,
            metadata={"forward_model": model.metadata()},
        )

