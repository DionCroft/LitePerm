"""Metropolis-Hastings style inverse solver."""

from __future__ import annotations

import numpy as np

from liteperm.inverse.inverse_solvers.base import InverseSolverBase, SolverRunContext


class MCMCSolver(InverseSolverBase):
    name = "MCMC"

    def solve(self, model, problem):
        context = SolverRunContext(model=model, problem=problem)
        bounds = np.asarray(problem.bounds(), dtype=float)
        lower = bounds[:, 0]
        upper = bounds[:, 1]
        rng = np.random.default_rng(int(problem.solver_options.get("seed", 19)))
        current = problem.initial_vector()
        current_score, _ = context.evaluate(current)
        best = current.copy()
        best_score = current_score
        steps = int(problem.solver_options.get("steps", 120))
        proposal_scale = 0.08 * np.maximum(upper - lower, 1e-6)
        accepted_vectors: list[np.ndarray] = []

        for _ in range(steps):
            proposal = np.clip(current + rng.normal(scale=proposal_scale), lower, upper)
            proposal_score, _ = context.evaluate(proposal)
            log_acceptance = -(proposal_score - current_score)
            if np.log(rng.random()) < log_acceptance:
                current = proposal
                current_score = proposal_score
                accepted_vectors.append(proposal.copy())
                if proposal_score < best_score:
                    best = proposal.copy()
                    best_score = proposal_score

        result = self._build_result(model=model, problem=problem, context=context, best_vector=best)
        if accepted_vectors:
            accepted_array = np.asarray(accepted_vectors, dtype=float)
            parameter_distributions = {}
            confidence_intervals = {}
            for index, definition in enumerate(problem.parameter_definitions):
                distribution = accepted_array[:, index].tolist()
                parameter_distributions[definition.name] = distribution
                confidence_intervals[definition.name] = (
                    float(np.percentile(accepted_array[:, index], 2.5)),
                    float(np.percentile(accepted_array[:, index], 97.5)),
                )
            from liteperm.inverse.common import UncertaintySummary

            result.uncertainty_summary = UncertaintySummary(
                best_estimate=result.best_parameters,
                confidence_intervals=confidence_intervals,
                parameter_distributions=parameter_distributions,
                correlation_matrix=np.corrcoef(accepted_array.T).tolist(),
                method="MCMC posterior samples",
            )
        return result

