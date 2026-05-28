"""Least-squares inverse solver."""

from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares

from liteperm.inverse.common import InverseProblem
from liteperm.inverse.forward_models.base import ForwardModel
from liteperm.inverse.inverse_solvers.base import InverseSolverBase, SolverRunContext


class LeastSquaresSolver(InverseSolverBase):
    name = "Least Squares"

    def solve(self, model: ForwardModel, problem: InverseProblem):
        context = SolverRunContext(model=model, problem=problem)
        initial = problem.initial_vector()
        lower, upper = zip(*problem.bounds(), strict=True) if problem.bounds() else ([], [])
        result = least_squares(context.residual, initial, bounds=(np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)))
        return self._build_result(model=model, problem=problem, context=context, best_vector=result.x)

