import numpy as np

from liteperm.geometry.profiles import build_geometry_profile
from liteperm.inverse.forward_models import build_forward_model, discover_forward_models
from liteperm.inverse.service import build_inverse_problem, default_layer_stack, run_inverse_estimation
from liteperm.inverse.uncertainty.analysis import monte_carlo_analysis
from liteperm.synthetic import generate_synthetic_dataset


def test_forward_models_simulate_across_supported_registry():
    frequency_hz = np.linspace(0.8e9, 3.2e9, 81)

    for sensor_type in discover_forward_models():
        geometry = build_geometry_profile(sensor_type)
        layer_stack = default_layer_stack(sensor_type)
        model = build_forward_model(sensor_type, geometry=geometry, layer_stack=layer_stack)

        simulation = model.simulate(frequency_hz)

        assert simulation.frequency_hz.shape == frequency_hz.shape
        assert simulation.s11.shape == frequency_hz.shape
        assert simulation.predicted_resonant_frequency_hz > 0


def test_inverse_estimation_recovers_generic_material_permittivity():
    frequency_hz = np.linspace(0.5e9, 3.0e9, 121)
    geometry = build_geometry_profile("generic_resonator")

    truth_stack = default_layer_stack("generic_resonator")
    truth_stack.layers[0].epsilon_real = 9.2
    truth_stack.layers[0].epsilon_imag = 0.3
    truth_stack.layers[0].conductivity_s_per_m = 0.02

    measurement = build_forward_model("generic_resonator", geometry=geometry, layer_stack=truth_stack).simulate(frequency_hz).measurement

    guess_stack = default_layer_stack("generic_resonator")
    guess_stack.layers[0].epsilon_real = 4.0

    result, twin, sweep_result = run_inverse_estimation(
        measurement=measurement,
        geometry=geometry,
        calibration_profile=None,
        layer_stack=guess_stack,
        forward_model_key="generic_resonator",
        solver_name="least_squares",
        parameter_names=["material_epsilon_real"],
        error_metric="weighted_error",
        run_monte_carlo=False,
        run_bootstrap=False,
    )

    assert abs(result.best_parameters["material_epsilon_real"] - 9.2) < 0.5
    assert twin.sensor_type == "generic_resonator"
    assert not sweep_result.sweep_table.empty


def test_monte_carlo_uncertainty_returns_confidence_intervals():
    frequency_hz = np.linspace(0.5e9, 3.0e9, 61)
    geometry = build_geometry_profile("generic_resonator")
    layer_stack = default_layer_stack("generic_resonator")
    layer_stack.layers[0].epsilon_real = 7.4

    model = build_forward_model("generic_resonator", geometry=geometry, layer_stack=layer_stack)
    measurement = model.simulate(frequency_hz).measurement
    problem = build_inverse_problem(model, measurement, parameter_names=["material_epsilon_real"])

    summary = monte_carlo_analysis(
        model=model,
        problem=problem,
        solver_name="least_squares",
        samples=4,
        noise_scale=1e-4,
        seed=11,
    )

    assert "material_epsilon_real" in summary.confidence_intervals
    interval = summary.confidence_intervals["material_epsilon_real"]
    assert interval[0] <= summary.best_estimate["material_epsilon_real"] <= interval[1]


def test_synthetic_dataset_generator_builds_rows_for_inverse_workflows():
    frequency_hz = np.linspace(1.0e9, 2.5e9, 41)
    geometry = build_geometry_profile("patch_antenna")
    layer_stacks = []
    for epsilon_real in [3.2, 5.6, 8.1]:
        layer_stack = default_layer_stack("patch_antenna")
        material_layer = layer_stack.get_layer("material")
        assert material_layer is not None
        material_layer.epsilon_real = epsilon_real
        layer_stacks.append(layer_stack)

    dataset = generate_synthetic_dataset(
        sensor_type="patch_antenna",
        geometry=geometry,
        layer_stacks=layer_stacks,
        frequency_hz=frequency_hz,
    )

    assert len(dataset) == 3
    assert set(dataset["sensor_type"]) == {"patch_antenna"}
    assert "layer_stack" in dataset.columns
