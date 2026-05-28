"""Differential-evolution inverse solver."""

from __future__ import annotations

import numpy as np
from scipy.optimize import differential_evolution

from liteperm.inverse.forward_models.base import ForwardModel
from liteperm.inverse.inverse_solvers.base import InverseSolverBase, SolverRunContext


class DifferentialEvolutionSolver(InverseSolverBase):
    name = "Differential Evolution"

    def solve(self, model: ForwardModel, problem):
        context = SolverRunContext(model=model, problem=problem)

        def objective(vector):
            value, _ = context.evaluate(np.asarray(vector, dtype=float))
            return value

        result = differential_evolution(objective, bounds=problem.bounds(), polish=True, maxiter=int(problem.solver_options.get("maxiter", 30)))
        return self._build_result(model=model, problem=problem, context=context, best_vector=np.asarray(result.x, dtype=float))

