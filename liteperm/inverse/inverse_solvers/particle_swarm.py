"""Particle-swarm inverse solver."""

from __future__ import annotations

import numpy as np

from liteperm.inverse.forward_models.base import ForwardModel
from liteperm.inverse.inverse_solvers.base import InverseSolverBase, SolverRunContext


class ParticleSwarmSolver(InverseSolverBase):
    name = "Particle Swarm"

    def solve(self, model: ForwardModel, problem):
        context = SolverRunContext(model=model, problem=problem)
        bounds = np.asarray(problem.bounds(), dtype=float)
        lower = bounds[:, 0]
        upper = bounds[:, 1]
        dimensions = len(bounds)
        particles = int(problem.solver_options.get("particles", max(12, dimensions * 6)))
        iterations = int(problem.solver_options.get("iterations", 25))
        rng = np.random.default_rng(int(problem.solver_options.get("seed", 42)))

        positions = rng.uniform(lower, upper, size=(particles, dimensions))
        velocities = rng.normal(scale=0.05 * np.maximum(upper - lower, 1e-6), size=(particles, dimensions))
        personal_best = positions.copy()
        personal_scores = np.full(particles, np.inf)
        global_best = positions[0].copy()
        global_score = np.inf

        for _ in range(iterations):
            for index in range(particles):
                score, _ = context.evaluate(positions[index])
                if score < personal_scores[index]:
                    personal_scores[index] = score
                    personal_best[index] = positions[index].copy()
                if score < global_score:
                    global_score = score
                    global_best = positions[index].copy()
            inertia = 0.6
            cognitive = 1.4
            social = 1.4
            random_1 = rng.random(size=(particles, dimensions))
            random_2 = rng.random(size=(particles, dimensions))
            velocities = (
                inertia * velocities
                + cognitive * random_1 * (personal_best - positions)
                + social * random_2 * (global_best - positions)
            )
            positions = np.clip(positions + velocities, lower, upper)

        return self._build_result(model=model, problem=problem, context=context, best_vector=global_best)

