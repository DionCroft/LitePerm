"""Lightweight Bayesian-style inverse solver using surrogate-guided search."""

from __future__ import annotations

import numpy as np

from liteperm.inverse.inverse_solvers.base import InverseSolverBase, SolverRunContext


class BayesianOptimisationSolver(InverseSolverBase):
    name = "Bayesian Optimisation"

    def solve(self, model, problem):
        context = SolverRunContext(model=model, problem=problem)
        bounds = np.asarray(problem.bounds(), dtype=float)
        lower = bounds[:, 0]
        upper = bounds[:, 1]
        rng = np.random.default_rng(int(problem.solver_options.get("seed", 7)))
        samples = []
        scores = []
        iterations = int(problem.solver_options.get("iterations", 24))
        initial_samples = max(6, len(bounds) * 3)

        for _ in range(initial_samples):
            candidate = rng.uniform(lower, upper)
            score, _ = context.evaluate(candidate)
            samples.append(candidate)
            scores.append(score)

        for _ in range(iterations):
            sample_array = np.asarray(samples, dtype=float)
            score_array = np.asarray(scores, dtype=float)
            candidate_pool = rng.uniform(lower, upper, size=(128, len(bounds)))
            distances = np.linalg.norm(candidate_pool[:, None, :] - sample_array[None, :, :], axis=2)
            kernel = np.exp(-(distances ** 2) / np.maximum(np.var(sample_array, axis=0).mean(), 1e-6))
            surrogate_mean = (kernel * score_array[None, :]).sum(axis=1) / np.maximum(kernel.sum(axis=1), 1e-9)
            uncertainty = 1.0 / np.maximum(kernel.sum(axis=1), 1e-9)
            acquisition = surrogate_mean - 0.25 * uncertainty
            candidate = candidate_pool[int(np.argmin(acquisition))]
            score, _ = context.evaluate(candidate)
            samples.append(candidate)
            scores.append(score)

        best_index = int(np.argmin(scores))
        return self._build_result(model=model, problem=problem, context=context, best_vector=np.asarray(samples[best_index], dtype=float))

