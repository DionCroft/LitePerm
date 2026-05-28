"""Inverse-solver registry."""

from liteperm.inverse.inverse_solvers.base import InverseSolverBase
from liteperm.inverse.inverse_solvers.bayesian_optimisation import BayesianOptimisationSolver
from liteperm.inverse.inverse_solvers.differential_evolution import DifferentialEvolutionSolver
from liteperm.inverse.inverse_solvers.least_squares import LeastSquaresSolver
from liteperm.inverse.inverse_solvers.mcmc import MCMCSolver
from liteperm.inverse.inverse_solvers.particle_swarm import ParticleSwarmSolver


def discover_inverse_solvers() -> dict[str, type[InverseSolverBase]]:
    return {
        "least_squares": LeastSquaresSolver,
        "differential_evolution": DifferentialEvolutionSolver,
        "particle_swarm": ParticleSwarmSolver,
        "bayesian_optimisation": BayesianOptimisationSolver,
        "mcmc": MCMCSolver,
    }


def build_inverse_solver(name: str, **kwargs) -> InverseSolverBase:
    registry = discover_inverse_solvers()
    key = name.lower()
    if key not in registry:
        raise KeyError(f"Unknown inverse solver: {name}")
    return registry[key](**kwargs)


__all__ = [
    "BayesianOptimisationSolver",
    "DifferentialEvolutionSolver",
    "InverseSolverBase",
    "LeastSquaresSolver",
    "MCMCSolver",
    "ParticleSwarmSolver",
    "build_inverse_solver",
    "discover_inverse_solvers",
]

