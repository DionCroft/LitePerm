"""Uncertainty quantification and sensitivity analysis."""

from __future__ import annotations

import numpy as np

from liteperm.inverse.common import SensitivityResult, UncertaintySummary
from liteperm.inverse.inverse_solvers import build_inverse_solver
from liteperm.models.core import MeasurementData


def _build_uncertainty_summary(best_estimate: dict[str, float], distributions: dict[str, list[float]], method: str) -> UncertaintySummary:
    parameter_names = list(distributions)
    matrix = np.asarray([distributions[name] for name in parameter_names], dtype=float)
    confidence = {
        name: (float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5)))
        for name, values in distributions.items()
    }
    correlation = np.corrcoef(matrix).tolist() if matrix.shape[0] > 1 else [[1.0]]
    return UncertaintySummary(
        best_estimate=best_estimate,
        confidence_intervals=confidence,
        parameter_distributions=distributions,
        correlation_matrix=correlation,
        method=method,
    )


def monte_carlo_analysis(*, model, problem, solver_name: str, samples: int = 20, noise_scale: float = 0.01, seed: int = 123) -> UncertaintySummary:
    rng = np.random.default_rng(seed)
    distributions = {parameter.name: [] for parameter in problem.parameter_definitions}
    solver = build_inverse_solver(solver_name)
    for _ in range(samples):
        noisy_measurement = MeasurementData(
            frequency_hz=problem.measured_measurement.frequency_hz.copy(),
            s11=problem.measured_measurement.s11 + noise_scale * (rng.normal(size=problem.measured_measurement.s11.size) + 1j * rng.normal(size=problem.measured_measurement.s11.size)),
            z0=problem.measured_measurement.z0,
            source_name=f"{problem.measured_measurement.source_name} (MC sample)",
        )
        noisy_problem = problem.__class__(
            measured_measurement=noisy_measurement,
            forward_model_name=problem.forward_model_name,
            parameter_definitions=problem.parameter_definitions,
            error_metric=problem.error_metric,
            solver_options=problem.solver_options,
            metadata=problem.metadata,
        )
        result = solver.solve(model, noisy_problem)
        for key, value in result.best_parameters.items():
            distributions[key].append(float(value))
    best_estimate = {key: float(np.mean(values)) for key, values in distributions.items()}
    return _build_uncertainty_summary(best_estimate, distributions, "Monte Carlo")


def bootstrap_analysis(*, model, problem, solver_name: str, samples: int = 15, seed: int = 321) -> UncertaintySummary:
    rng = np.random.default_rng(seed)
    distributions = {parameter.name: [] for parameter in problem.parameter_definitions}
    solver = build_inverse_solver(solver_name)
    n = problem.measured_measurement.frequency_hz.size
    for _ in range(samples):
        indices = np.sort(rng.integers(0, n, size=n))
        boot_measurement = MeasurementData(
            frequency_hz=problem.measured_measurement.frequency_hz[indices],
            s11=problem.measured_measurement.s11[indices],
            z0=problem.measured_measurement.z0,
            source_name=f"{problem.measured_measurement.source_name} (bootstrap)",
        )
        boot_problem = problem.__class__(
            measured_measurement=boot_measurement,
            forward_model_name=problem.forward_model_name,
            parameter_definitions=problem.parameter_definitions,
            error_metric=problem.error_metric,
            solver_options=problem.solver_options,
            metadata=problem.metadata,
        )
        result = solver.solve(model, boot_problem)
        for key, value in result.best_parameters.items():
            distributions[key].append(float(value))
    best_estimate = {key: float(np.median(values)) for key, values in distributions.items()}
    return _build_uncertainty_summary(best_estimate, distributions, "Bootstrap")


def bayesian_credible_intervals(result) -> dict[str, tuple[float, float]]:
    if result.uncertainty_summary is None:
        return {}
    return result.uncertainty_summary.confidence_intervals


def sensitivity_analysis(*, model, problem, baseline_parameters: dict[str, float], perturbation_fraction: float = 0.05) -> SensitivityResult:
    from liteperm.inverse.common import clone_with_parameter_updates
    from liteperm.inverse.optimisers.error_metrics import compute_scalar_error

    baseline_model = clone_with_parameter_updates(model, {definition.target_path: baseline_parameters[definition.name] for definition in problem.parameter_definitions})
    baseline_simulation = baseline_model.simulate(problem.measured_measurement.frequency_hz)
    baseline_error = compute_scalar_error(problem.measured_measurement, baseline_simulation.measurement, metric=problem.error_metric)
    ranking = []
    heatmap = {}
    tornado = {}
    for definition in problem.parameter_definitions:
        baseline_value = baseline_parameters[definition.name]
        delta = max(abs(baseline_value) * perturbation_fraction, 1e-6)
        factors = np.linspace(-1.0, 1.0, 7)
        errors = []
        for factor in factors:
            candidate_value = float(np.clip(baseline_value + factor * delta, definition.lower_bound, definition.upper_bound))
            candidate_model = clone_with_parameter_updates(model, {definition.target_path: candidate_value})
            simulation = candidate_model.simulate(problem.measured_measurement.frequency_hz)
            errors.append(compute_scalar_error(problem.measured_measurement, simulation.measurement, metric=problem.error_metric))
        influence = max(errors) - min(errors)
        ranking.append({"parameter": definition.name, "influence": float(influence), "baseline_value": float(baseline_value)})
        heatmap[definition.name] = [float(value) for value in errors]
        tornado[definition.name] = [float(min(errors) - baseline_error), float(max(errors) - baseline_error)]
    ranking.sort(key=lambda item: item["influence"], reverse=True)
    return SensitivityResult(baseline_error=float(baseline_error), ranking=ranking, heatmap=heatmap, tornado=tornado, metadata={"perturbation_fraction": perturbation_fraction})


def error_propagation(*, uncertainty_summary: UncertaintySummary) -> dict[str, float]:
    propagated = {}
    for key, interval in uncertainty_summary.confidence_intervals.items():
        propagated[key] = float((interval[1] - interval[0]) / 2)
    return propagated

