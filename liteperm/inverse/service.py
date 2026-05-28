"""Orchestration helpers for inverse material estimation workflows."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pandas as pd

from liteperm.calibration.profiles import build_calibration_profile
from liteperm.inverse.common import InverseProblem, LayerDefinition, LayerStack
from liteperm.inverse.digital_twin import build_digital_twin
from liteperm.inverse.forward_models import build_forward_model
from liteperm.inverse.inverse_solvers import build_inverse_solver
from liteperm.inverse.parameter_space.sweep import ParameterSweepEngine
from liteperm.inverse.uncertainty.analysis import bootstrap_analysis, monte_carlo_analysis, sensitivity_analysis
from liteperm.models.core import CalibrationProfile, MeasurementData, SensorGeometryProfile


DEFAULT_LAYER_STACKS: dict[str, list[LayerDefinition]] = {
    "patch_antenna": [
        LayerDefinition("air", "Air", 1e-3, 1.0006, 0.0, 0.0, 0.0, role="air", mutable=False),
        LayerDefinition("protective_layer", "PTFE", 1.5e-4, 2.1, 0.00042, 0.0, 0.0002, role="protective_layer", mutable=True),
        LayerDefinition("material_under_test", "Unknown", 1.0e-3, 4.5, 0.15, 0.01, 0.03, role="material", mutable=True),
        LayerDefinition("substrate", "FR4", 1.6e-3, 4.3, 0.086, 0.0117, 0.02, role="substrate", mutable=False),
        LayerDefinition("ground_plane", "Copper", 3.5e-5, 1.0, 0.0, 5.8e7, 0.0, role="ground", mutable=False),
    ],
    "open_ended_coax_probe": [
        LayerDefinition("air", "Air", 5e-4, 1.0006, 0.0, 0.0, 0.0, role="air", mutable=False),
        LayerDefinition("protective_layer", "PTFE", 1e-4, 2.1, 0.00042, 0.0, 0.0002, role="protective_layer", mutable=True),
        LayerDefinition("material_under_test", "Unknown", 2e-3, 12.0, 1.5, 0.2, 0.1, role="material", mutable=True),
        LayerDefinition("sensor_layer", "Probe Aperture", 2e-4, 2.1, 0.01, 0.0, 0.005, role="sensor_layer", mutable=False),
    ],
    "microstrip_resonator": [
        LayerDefinition("air", "Air", 1e-3, 1.0006, 0.0, 0.0, 0.0, role="air", mutable=False),
        LayerDefinition("protective_layer", "Parylene", 5e-5, 3.1, 0.01, 0.0, 0.003, role="protective_layer", mutable=True),
        LayerDefinition("material_under_test", "Unknown", 1e-3, 6.0, 0.4, 0.05, 0.06, role="material", mutable=True),
        LayerDefinition("substrate", "Rogers 5880", 1.6e-3, 2.2, 0.00198, 0.000269, 0.0009, role="substrate", mutable=False),
        LayerDefinition("ground_plane", "Copper", 3.5e-5, 1.0, 0.0, 5.8e7, 0.0, role="ground", mutable=False),
    ],
    "generic_resonator": [
        LayerDefinition("material_under_test", "Unknown", 1e-3, 8.0, 0.3, 0.02, 0.04, role="material", mutable=True),
    ],
}


def default_layer_stack(sensor_type: str) -> LayerStack:
    sensor_key = sensor_type if sensor_type in DEFAULT_LAYER_STACKS else "generic_resonator"
    return LayerStack(layers=[replace(layer) for layer in DEFAULT_LAYER_STACKS[sensor_key]], metadata={"sensor_type": sensor_key})


def layer_stack_to_frame(layer_stack: LayerStack) -> pd.DataFrame:
    return pd.DataFrame([layer.to_dict() for layer in layer_stack.layers])


def layer_stack_from_frame(frame: pd.DataFrame) -> LayerStack:
    records = frame.to_dict(orient="records")
    return LayerStack(layers=[LayerDefinition.from_dict(record) for record in records], metadata={})


def build_inverse_problem(model, measurement: MeasurementData, *, parameter_names: list[str] | None = None, error_metric: str = "weighted_error", solver_options: dict[str, Any] | None = None) -> InverseProblem:
    parameter_definitions = model.parameters()
    if parameter_names:
        parameter_definitions = [definition for definition in parameter_definitions if definition.name in parameter_names]
    return InverseProblem(
        measured_measurement=measurement,
        forward_model_name=model.metadata().get("name", "Forward Model"),
        parameter_definitions=parameter_definitions,
        error_metric=error_metric,
        solver_options=solver_options or {},
        metadata=model.metadata(),
    )


def run_inverse_estimation(
    *,
    measurement: MeasurementData,
    geometry: SensorGeometryProfile,
    calibration_profile: CalibrationProfile | None,
    layer_stack: LayerStack,
    forward_model_key: str,
    solver_name: str,
    parameter_names: list[str] | None = None,
    error_metric: str = "weighted_error",
    solver_options: dict[str, Any] | None = None,
    run_monte_carlo: bool = False,
    run_bootstrap: bool = False,
    uncertainty_samples: int = 12,
) -> tuple[object, object, object]:
    calibration_profile = calibration_profile or build_calibration_profile("Default OSL")
    model = build_forward_model(forward_model_key, geometry=geometry, layer_stack=layer_stack)
    problem = build_inverse_problem(model, measurement, parameter_names=parameter_names, error_metric=error_metric, solver_options=solver_options)
    solver = build_inverse_solver(solver_name)
    result = solver.solve(model, problem)

    if result.uncertainty_summary is None and run_monte_carlo:
        result.uncertainty_summary = monte_carlo_analysis(
            model=model,
            problem=problem,
            solver_name=solver_name,
            samples=uncertainty_samples,
        )
    if run_bootstrap:
        bootstrap_summary = bootstrap_analysis(
            model=model,
            problem=problem,
            solver_name=solver_name,
            samples=max(6, uncertainty_samples // 2),
        )
        result.metadata["bootstrap_summary"] = bootstrap_summary.to_dict()

    result.sensitivity_result = sensitivity_analysis(model=model, problem=problem, baseline_parameters=result.best_parameters)
    twin = build_digital_twin(
        geometry_profile=geometry,
        calibration_profile=calibration_profile,
        layer_stack=layer_stack,
        measurement=measurement,
        inverse_result=result.to_dict(),
    )
    sweep_engine = ParameterSweepEngine()
    sweep_parameters = {}
    for definition in problem.parameter_definitions[:2]:
        center = result.best_parameters[definition.name]
        span = max((definition.upper_bound - definition.lower_bound) * 0.15, 1e-6)
        sweep_parameters[definition.target_path] = [
            max(definition.lower_bound, center - span),
            center,
            min(definition.upper_bound, center + span),
        ]
    sweep_result = sweep_engine.run(model=model, measured_measurement=measurement, parameter_grid=sweep_parameters or {problem.parameter_definitions[0].target_path: [problem.parameter_definitions[0].initial_value]}, error_metric=error_metric)
    return result, twin, sweep_result
