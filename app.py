from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from liteperm.acquisition import AcquisitionPipeline
from liteperm.ai.dataset_builder import build_experiment_dataset
from liteperm.calibration import (
    build_calibration_profile,
    calibration_profile_to_yaml,
    list_saved_calibration_profiles,
    load_calibration_profile,
    save_calibration_profile_to_library,
)
from liteperm.database import ExperimentDatabase, MaterialDatabase
from liteperm.devices import create_device, discover_device_candidates
from liteperm.geometry import (
    DEFAULT_GEOMETRIES,
    build_geometry_profile,
    geometry_profile_to_yaml,
    list_saved_geometry_profiles,
    load_geometry_profile,
    save_geometry_profile_to_library,
)
from liteperm.inverse.common import InverseResult, LayerStack, ParameterSweepResult
from liteperm.inverse.forward_models import build_forward_model, discover_forward_models
from liteperm.inverse.inverse_solvers import discover_inverse_solvers
from liteperm.inverse.service import default_layer_stack, layer_stack_from_frame, layer_stack_to_frame, run_inverse_estimation
from liteperm.inverse.validation import generate_validation_report
from liteperm.inverse.visualisation import (
    build_confidence_interval_plot,
    build_convergence_plot,
    build_layer_stack_viewer,
    build_measured_vs_predicted_plot,
    build_parameter_space_3d,
    build_residual_plot,
    build_sensitivity_heatmap,
    build_smith_comparison_plot,
    build_tornado_plot,
)
from liteperm.io.exporters import figure_to_image_bytes, spectrum_to_csv_bytes
from liteperm.io.parsers import load_measurement
from liteperm.models.core import CalibrationProfile, ExperimentMetadata, MeasurementData, SensorGeometryProfile, SweepConfig
from liteperm.plugins.manager import discover_plugins, get_runnable_plugins
from liteperm.sensors import build_sensor_model
from liteperm.synthetic import generate_synthetic_dataset
from liteperm.transform.permittivity import compute_material_spectrum
from liteperm.utils.resources import get_reference_material_by_name, list_reference_material_names, load_reference_materials
from liteperm.visualisation.plots import (
    build_admittance_plot,
    build_epsilon_plot,
    build_impedance_plot,
    build_loss_tangent_plot,
    build_magnitude_plot,
    build_nyquist_plot,
    build_phase_plot,
    build_smith_chart,
)


APP_ROOT = Path(__file__).resolve().parent
EXAMPLE_ROOT = APP_ROOT / "examples"


@st.cache_resource
def get_experiment_database() -> ExperimentDatabase:
    return ExperimentDatabase()


@st.cache_resource
def get_material_database() -> MaterialDatabase:
    return MaterialDatabase()


def initialise_state() -> None:
    defaults: dict[str, Any] = {
        "measurement": None,
        "processed_measurement": None,
        "open_measurement": None,
        "short_measurement": None,
        "load_measurement": None,
        "calibration_profile": build_calibration_profile("Default OSL"),
        "geometry_profile": build_geometry_profile("open_ended_coax_probe"),
        "last_spectrum": None,
        "device": None,
        "device_kind": "future_device",
        "device_port": "SIMULATED",
        "live_running": False,
        "live_last_result": None,
        "live_render_nonce": 0,
        "last_saved_experiment_id": "",
        "inverse_layer_stack": default_layer_stack("open_ended_coax_probe"),
        "inverse_result": None,
        "inverse_digital_twin": None,
        "inverse_sweep_result": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def parse_uploaded_measurement(uploaded_file) -> MeasurementData:
    return load_measurement(BytesIO(uploaded_file.getvalue()), filename=uploaded_file.name)


def reset_inverse_state(*, preserve_layer_stack: bool = True) -> None:
    st.session_state["inverse_result"] = None
    st.session_state["inverse_digital_twin"] = None
    st.session_state["inverse_sweep_result"] = None
    if not preserve_layer_stack:
        st.session_state["inverse_layer_stack"] = default_layer_stack(st.session_state["geometry_profile"].sensor_type)


def render_measurement_summary(measurement: MeasurementData) -> None:
    start_ghz = measurement.frequency_hz.min() / 1e9
    stop_ghz = measurement.frequency_hz.max() / 1e9
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Samples", f"{measurement.frequency_hz.size}")
    metric_2.metric("Start", f"{start_ghz:.4f} GHz")
    metric_3.metric("Stop", f"{stop_ghz:.4f} GHz")
    metric_4.metric("Span", f"{stop_ghz - start_ghz:.4f} GHz")


def render_figure_export(figure, prefix: str) -> None:
    export_format = st.selectbox("Figure export format", ["png", "svg", "pdf"], key=f"{prefix}_export_format")
    try:
        image_payload = figure_to_image_bytes(figure, format=export_format)
    except Exception as error:  # pragma: no cover - depends on local image export backend
        st.info(f"Figure export unavailable in this environment: {error}")
        return

    st.download_button(
        label=f"Download {export_format.upper()}",
        data=image_payload,
        file_name=f"{prefix}.{export_format}",
        mime=f"image/{export_format}",
        key=f"{prefix}_download",
    )


def geometry_editor(current_profile: SensorGeometryProfile) -> SensorGeometryProfile:
    sensor_type_options = list(DEFAULT_GEOMETRIES)
    current_sensor_type = current_profile.sensor_type if current_profile.sensor_type in sensor_type_options else sensor_type_options[0]
    sensor_type = st.selectbox(
        "Sensor type",
        options=sensor_type_options,
        index=sensor_type_options.index(current_sensor_type),
        format_func=lambda item: item.replace("_", " ").title(),
    )

    base_parameters = dict(DEFAULT_GEOMETRIES[sensor_type])
    if current_profile.sensor_type == sensor_type:
        base_parameters.update(current_profile.parameters)

    edited_parameters: dict[str, float | str] = {}
    for parameter_name, parameter_value in base_parameters.items():
        label = parameter_name.replace("_", " ").title()
        if isinstance(parameter_value, str):
            edited_parameters[parameter_name] = st.text_input(label, value=parameter_value, key=f"geometry_{sensor_type}_{parameter_name}")
        else:
            edited_parameters[parameter_name] = float(
                st.number_input(
                    label,
                    value=float(parameter_value),
                    step=0.1,
                    key=f"geometry_{sensor_type}_{parameter_name}",
                )
            )

    profile_name = st.text_input("Geometry profile name", value=current_profile.name, key="geometry_profile_name")
    notes = st.text_area("Geometry notes", value=current_profile.notes, key="geometry_profile_notes")
    return build_geometry_profile(sensor_type, name=profile_name, parameters=edited_parameters, notes=notes)


def calibration_editor(reference_names: list[str], current_profile: CalibrationProfile) -> CalibrationProfile:
    name = st.text_input("Calibration profile name", value=current_profile.name, key="calibration_profile_name")
    standard_columns = st.columns(3)
    with standard_columns[0]:
        open_real = st.number_input("Open real", value=float(current_profile.open_gamma.real), key="open_real")
        open_imag = st.number_input("Open imag", value=float(current_profile.open_gamma.imag), key="open_imag")
    with standard_columns[1]:
        short_real = st.number_input("Short real", value=float(current_profile.short_gamma.real), key="short_real")
        short_imag = st.number_input("Short imag", value=float(current_profile.short_gamma.imag), key="short_imag")
    with standard_columns[2]:
        load_real = st.number_input("Load real", value=float(current_profile.load_gamma.real), key="load_real")
        load_imag = st.number_input("Load imag", value=float(current_profile.load_gamma.imag), key="load_imag")

    selected_references: list[str] = []
    reference_options = ["None"] + reference_names
    for index in range(4):
        default_name = current_profile.reference_materials[index] if index < len(current_profile.reference_materials) else "None"
        selection = st.selectbox(
            f"Reference material {index + 1}",
            options=reference_options,
            index=reference_options.index(default_name) if default_name in reference_options else 0,
            key=f"reference_material_{index + 1}",
        )
        if selection != "None":
            selected_references.append(selection)

    notes = st.text_area("Calibration notes", value=current_profile.notes, key="calibration_notes")
    return build_calibration_profile(
        name,
        reference_materials=selected_references,
        open_gamma=complex(open_real, open_imag),
        short_gamma=complex(short_real, short_imag),
        load_gamma=complex(load_real, load_imag),
        notes=notes,
    )


def compute_current_spectrum(selected_plugin: str, apply_calibration: bool):
    measurement = st.session_state["measurement"]
    if measurement is None:
        return None, None

    calibration_profile = st.session_state["calibration_profile"]
    open_measurement = st.session_state["open_measurement"]
    short_measurement = st.session_state["short_measurement"]
    load_measurement = st.session_state["load_measurement"]
    can_calibrate = all(item is not None for item in [open_measurement, short_measurement, load_measurement])

    spectrum, working_measurement = compute_material_spectrum(
        measurement,
        st.session_state["geometry_profile"],
        method=selected_plugin,
        calibration_profile=calibration_profile if apply_calibration and can_calibrate else None,
        open_measurement=open_measurement if apply_calibration and can_calibrate else None,
        short_measurement=short_measurement if apply_calibration and can_calibrate else None,
        load_measurement=load_measurement if apply_calibration and can_calibrate else None,
    )
    st.session_state["processed_measurement"] = working_measurement
    return spectrum, working_measurement


def load_example_dataset(example_name: str) -> None:
    if example_name == "None":
        return
    st.session_state["measurement"] = load_measurement(EXAMPLE_ROOT / example_name)
    st.session_state["processed_measurement"] = None
    st.session_state["last_spectrum"] = None
    reset_inverse_state()


def connect_selected_device(device_kind: str, port: str) -> str:
    existing_device = st.session_state.get("device")
    if existing_device is not None:
        try:
            existing_device.disconnect()
        except Exception:
            pass

    device = create_device(device_kind, port=port)
    device.connect()
    st.session_state["device"] = device
    st.session_state["device_kind"] = device_kind
    st.session_state["device_port"] = port
    return f"{device.get_device_info().name} connected on `{port}`"


def disconnect_device() -> None:
    device = st.session_state.get("device")
    if device is not None:
        try:
            device.disconnect()
        finally:
            st.session_state["device"] = None
            st.session_state["live_running"] = False


def render_live_capture_results(result, live_placeholder) -> None:
    st.session_state["live_last_result"] = result
    st.session_state["measurement"] = result.raw_measurement
    st.session_state["processed_measurement"] = result.processed_measurement
    st.session_state["last_spectrum"] = result.spectrum
    reset_inverse_state()
    st.session_state["live_render_nonce"] = int(st.session_state.get("live_render_nonce", 0)) + 1
    render_nonce = st.session_state["live_render_nonce"]
    capture_index = result.raw_measurement.metadata.get("capture_index", "latest")
    key_suffix = f"{capture_index}_{render_nonce}"

    with live_placeholder.container():
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                build_magnitude_plot(result.raw_measurement),
                use_container_width=True,
                key=f"live_magnitude_chart_{key_suffix}",
            )
            st.plotly_chart(
                build_phase_plot(result.raw_measurement),
                use_container_width=True,
                key=f"live_phase_chart_{key_suffix}",
            )
        with right:
            st.plotly_chart(
                build_smith_chart(result.raw_measurement),
                use_container_width=True,
                key=f"live_smith_chart_{key_suffix}",
            )
            st.plotly_chart(
                build_epsilon_plot(result.spectrum),
                use_container_width=True,
                key=f"live_epsilon_chart_{key_suffix}",
            )


def build_research_metadata(default_name: str) -> ExperimentMetadata:
    measurement = st.session_state.get("measurement")
    geometry_profile = st.session_state["geometry_profile"]
    calibration_profile = st.session_state["calibration_profile"]
    device = st.session_state.get("device")
    frequency_range = (0.0, 0.0)
    if measurement is not None:
        frequency_range = (float(measurement.frequency_hz.min()), float(measurement.frequency_hz.max()))

    experiment_name = st.text_input("Experiment Name", value=default_name, key="research_experiment_name")
    researcher = st.text_input("Researcher", value="Researcher", key="research_researcher")
    project_name = st.text_input("Project Name", value="LitePerm Research", key="research_project_name")
    description = st.text_area("Description", value="", key="research_description")
    metadata_columns = st.columns(2)
    with metadata_columns[0]:
        temperature_c = st.number_input("Temperature (C)", value=25.0, step=0.1, key="research_temperature")
        humidity_percent = st.number_input("Humidity (%)", value=40.0, step=0.1, key="research_humidity")
        material_under_test = st.text_input("Material Under Test", value="Unknown", key="research_material")
    with metadata_columns[1]:
        sensor_type = st.text_input("Sensor Type", value=geometry_profile.sensor_type, key="research_sensor_type")
        notes = st.text_area("Notes", value="", key="research_notes")
        tags = st.text_input("Tags", value="phase3,inverse-modelling,rf-sensing", key="research_tags")

    return ExperimentMetadata(
        experiment_name=experiment_name,
        researcher=researcher,
        project_name=project_name,
        description=description,
        temperature_c=float(temperature_c),
        humidity_percent=float(humidity_percent),
        sensor_type=sensor_type,
        calibration_profile_name=calibration_profile.name,
        geometry_profile_name=geometry_profile.name,
        frequency_range_hz=frequency_range,
        material_under_test=material_under_test,
        notes=notes,
        tags=[token.strip() for token in tags.split(",") if token.strip()],
        device_name=device.get_device_info().name if device is not None else "",
        device_port=device.port if device is not None else "",
    )


def ensure_inverse_layer_stack(sensor_type: str) -> None:
    current_stack = st.session_state.get("inverse_layer_stack")
    if current_stack is None or current_stack.metadata.get("sensor_type") != sensor_type:
        st.session_state["inverse_layer_stack"] = default_layer_stack(sensor_type)


def render_inverse_layer_stack_editor(sensor_type: str):
    ensure_inverse_layer_stack(sensor_type)
    layer_stack = st.session_state["inverse_layer_stack"]
    editor_frame = layer_stack_to_frame(layer_stack)
    edited_frame = st.data_editor(
        editor_frame,
        num_rows="dynamic",
        use_container_width=True,
        key=f"inverse_layer_stack_editor_{sensor_type}",
    )
    updated_stack = layer_stack_from_frame(pd.DataFrame(edited_frame))
    updated_stack.metadata["sensor_type"] = sensor_type
    st.session_state["inverse_layer_stack"] = updated_stack
    return updated_stack


def render_inverse_summary(result) -> None:
    best_parameters = result.best_parameters
    epsilon_real = best_parameters.get("material_epsilon_real", best_parameters.get("material_under_test_epsilon_real", float("nan")))
    epsilon_imag = best_parameters.get("material_epsilon_imag", best_parameters.get("material_under_test_epsilon_imag", float("nan")))
    conductivity = best_parameters.get(
        "material_conductivity_s_per_m",
        best_parameters.get("material_under_test_conductivity_s_per_m", float("nan")),
    )
    thickness = best_parameters.get("material_thickness_m", best_parameters.get("material_under_test_thickness_m", float("nan")))
    loss_tangent = abs(epsilon_imag) / max(abs(epsilon_real), 1e-9) if pd.notna(epsilon_real) and pd.notna(epsilon_imag) else float("nan")
    metrics = st.columns(5)
    metrics[0].metric("Objective", f"{result.objective_value:.4f}")
    metrics[1].metric("epsilon'", f"{epsilon_real:.4f}" if pd.notna(epsilon_real) else "n/a")
    metrics[2].metric("epsilon''", f"{epsilon_imag:.4f}" if pd.notna(epsilon_imag) else "n/a")
    metrics[3].metric("Conductivity", f"{conductivity:.4f} S/m" if pd.notna(conductivity) else "n/a")
    metrics[4].metric("Thickness", f"{thickness * 1e3:.4f} mm" if pd.notna(thickness) else "n/a")
    st.caption(f"Estimated loss tangent: {loss_tangent:.4f}" if pd.notna(loss_tangent) else "Estimated loss tangent: n/a")


def build_inverse_solver_options(solver_key: str) -> dict[str, Any]:
    solver_options: dict[str, Any] = {}
    if solver_key == "least_squares":
        st.caption("Least-squares uses bounded local optimisation and works best when your initial geometry is already close to the measurement.")
        return solver_options

    option_columns = st.columns(3)
    if solver_key == "differential_evolution":
        with option_columns[0]:
            solver_options["maxiter"] = int(st.number_input("DE iterations", min_value=5, value=30, step=5, key="inverse_de_maxiter"))
    elif solver_key == "particle_swarm":
        with option_columns[0]:
            solver_options["particles"] = int(st.number_input("Particles", min_value=8, value=24, step=4, key="inverse_pso_particles"))
        with option_columns[1]:
            solver_options["iterations"] = int(st.number_input("PSO iterations", min_value=5, value=25, step=5, key="inverse_pso_iterations"))
        with option_columns[2]:
            solver_options["seed"] = int(st.number_input("PSO seed", min_value=0, value=42, step=1, key="inverse_pso_seed"))
    elif solver_key == "bayesian_optimisation":
        with option_columns[0]:
            solver_options["iterations"] = int(st.number_input("BO iterations", min_value=6, value=24, step=3, key="inverse_bo_iterations"))
        with option_columns[1]:
            solver_options["seed"] = int(st.number_input("BO seed", min_value=0, value=7, step=1, key="inverse_bo_seed"))
    elif solver_key == "mcmc":
        with option_columns[0]:
            solver_options["steps"] = int(st.number_input("MCMC steps", min_value=20, value=120, step=20, key="inverse_mcmc_steps"))
        with option_columns[1]:
            solver_options["seed"] = int(st.number_input("MCMC seed", min_value=0, value=19, step=1, key="inverse_mcmc_seed"))
    return solver_options


def render_inverse_modelling_tab(
    *,
    forward_models: dict[str, type],
    inverse_solvers: dict[str, type],
) -> None:
    st.subheader("Inverse Electromagnetic Modelling")

    measurement = st.session_state["measurement"]
    processed_measurement = st.session_state.get("processed_measurement")
    if measurement is None:
        st.warning("Import or capture a measurement before running inverse electromagnetic modelling.")
        return

    geometry_profile = st.session_state["geometry_profile"]
    forward_model_options = list(forward_models)
    default_forward_model = geometry_profile.sensor_type if geometry_profile.sensor_type in forward_models else "generic_resonator"
    if geometry_profile.sensor_type not in forward_models:
        st.info(
            f"`{geometry_profile.sensor_type}` does not yet have a dedicated forward model, so LitePerm is using the generic resonator baseline."
        )

    control_columns = st.columns(4)
    with control_columns[0]:
        input_response_mode = st.selectbox(
            "Input response",
            options=["raw", "processed"],
            index=1 if processed_measurement is not None else 0,
            format_func=lambda item: "Processed / calibrated S11" if item == "processed" else "Raw measured S11",
            key="inverse_input_response_mode",
        )
    with control_columns[1]:
        forward_model_key = st.selectbox(
            "Forward model",
            options=forward_model_options,
            index=forward_model_options.index(default_forward_model),
            format_func=lambda item: item.replace("_", " ").title(),
            key="inverse_forward_model_key",
        )
    with control_columns[2]:
        solver_key = st.selectbox(
            "Inverse solver",
            options=list(inverse_solvers),
            format_func=lambda item: inverse_solvers[item].name,
            key="inverse_solver_key",
        )
    with control_columns[3]:
        error_metric = st.selectbox(
            "Error metric",
            options=[
                "weighted_error",
                "complex_error",
                "magnitude_error",
                "phase_error",
                "multi_objective_error",
                "rmse",
                "mse",
                "mae",
            ],
            index=0,
            key="inverse_error_metric",
        )

    inverse_measurement = processed_measurement if input_response_mode == "processed" and processed_measurement is not None else measurement
    st.caption(f"Inverse solver input: `{inverse_measurement.source_name or 'Measured S11'}`")

    if forward_model_key == "patch_antenna":
        st.markdown("### Patch Antenna Material Characterisation Mode")
        st.caption("Use this mode to estimate multilayer dielectric properties directly from the measured resonance shift and S11 shape.")

    layer_stack = render_inverse_layer_stack_editor(forward_model_key)
    model = build_forward_model(forward_model_key, geometry=geometry_profile, layer_stack=layer_stack)
    validation_messages = model.validate()
    for message in validation_messages:
        st.warning(message)

    parameter_definitions = model.parameters()
    if not parameter_definitions:
        st.warning("This forward model does not currently expose tunable inverse parameters.")
        return

    default_parameters = [
        definition.name
        for definition in parameter_definitions
        if any(token in definition.name for token in ["material", "epsilon", "conductivity", "thickness"])
    ] or [definition.name for definition in parameter_definitions]

    selected_parameters = st.multiselect(
        "Estimated parameters",
        options=[definition.name for definition in parameter_definitions],
        default=default_parameters,
        key=f"inverse_parameters_{forward_model_key}",
    )
    parameter_rows = []
    for definition in parameter_definitions:
        parameter_rows.append(
            {
                "Selected": definition.name in selected_parameters,
                "Parameter": definition.name,
                "Target": definition.target_path,
                "Lower": definition.lower_bound,
                "Upper": definition.upper_bound,
                "Initial": definition.initial_value,
                "Scale": definition.scale,
            }
        )
    st.dataframe(pd.DataFrame(parameter_rows), use_container_width=True)

    st.markdown("### Solver Settings")
    solver_options = build_inverse_solver_options(solver_key)

    uncertainty_columns = st.columns(3)
    with uncertainty_columns[0]:
        run_monte_carlo = st.checkbox("Monte Carlo uncertainty", value=True, key="inverse_run_monte_carlo")
    with uncertainty_columns[1]:
        run_bootstrap = st.checkbox("Bootstrap uncertainty", value=False, key="inverse_run_bootstrap")
    with uncertainty_columns[2]:
        uncertainty_samples = int(st.number_input("Uncertainty samples", min_value=6, value=12, step=2, key="inverse_uncertainty_samples"))

    if st.button("Run Inverse Estimation", key="inverse_run_estimation"):
        if not selected_parameters:
            st.error("Select at least one parameter to estimate before running the inverse solver.")
        else:
            try:
                result, twin, sweep_result = run_inverse_estimation(
                    measurement=inverse_measurement,
                    geometry=geometry_profile,
                    calibration_profile=st.session_state["calibration_profile"],
                    layer_stack=layer_stack,
                    forward_model_key=forward_model_key,
                    solver_name=solver_key,
                    parameter_names=selected_parameters,
                    error_metric=error_metric,
                    solver_options=solver_options,
                    run_monte_carlo=run_monte_carlo,
                    run_bootstrap=run_bootstrap,
                    uncertainty_samples=uncertainty_samples,
                )
                st.session_state["inverse_result"] = result.to_dict()
                st.session_state["inverse_digital_twin"] = twin.to_dict()
                st.session_state["inverse_sweep_result"] = sweep_result.to_dict()
                st.success("Inverse estimation complete. LitePerm updated the digital twin and stored the latest parameter sweep.")
            except Exception as error:
                st.error(f"Inverse modelling failed: {error}")

    inverse_result_payload = st.session_state.get("inverse_result")
    if inverse_result_payload is None:
        st.info("Run an inverse estimation to compare measured and predicted RF responses, inspect residuals, and estimate material properties.")
        return

    inverse_result = InverseResult.from_dict(inverse_result_payload)
    sweep_payload = st.session_state.get("inverse_sweep_result")
    sweep_result = ParameterSweepResult.from_dict(sweep_payload) if sweep_payload else None

    render_inverse_summary(inverse_result)
    st.write(
        f"Predicted resonant frequency: `{inverse_result.predicted_simulation.predicted_resonant_frequency_hz / 1e9:.4f} GHz` using `{inverse_result.solver_name}`."
    )

    predicted_measurement = inverse_result.predicted_simulation.measurement
    comparison_figure = build_measured_vs_predicted_plot(inverse_measurement, predicted_measurement)
    st.plotly_chart(comparison_figure, use_container_width=True, key="inverse_measured_vs_predicted_chart")
    render_figure_export(comparison_figure, "inverse_measured_vs_predicted")

    top_figures = st.columns(2)
    with top_figures[0]:
        st.plotly_chart(
            build_smith_comparison_plot(inverse_measurement, predicted_measurement),
            use_container_width=True,
            key="inverse_smith_comparison_chart",
        )
    with top_figures[1]:
        st.plotly_chart(
            build_residual_plot(inverse_result.residual_measurement),
            use_container_width=True,
            key="inverse_residual_chart",
        )

    secondary_figures = st.columns(2)
    with secondary_figures[0]:
        st.plotly_chart(
            build_convergence_plot(inverse_result),
            use_container_width=True,
            key="inverse_convergence_chart",
        )
    with secondary_figures[1]:
        st.plotly_chart(
            build_confidence_interval_plot(inverse_result),
            use_container_width=True,
            key="inverse_confidence_interval_chart",
        )

    if inverse_result.sensitivity_result is not None:
        sensitivity_columns = st.columns(2)
        with sensitivity_columns[0]:
            st.plotly_chart(
                build_sensitivity_heatmap(inverse_result.sensitivity_result),
                use_container_width=True,
                key="inverse_sensitivity_heatmap_chart",
            )
        with sensitivity_columns[1]:
            st.plotly_chart(
                build_tornado_plot(inverse_result.sensitivity_result),
                use_container_width=True,
                key="inverse_tornado_chart",
            )
        st.dataframe(inverse_result.sensitivity_result.to_dataframe(), use_container_width=True)

    if sweep_result is not None:
        st.plotly_chart(
            build_parameter_space_3d(sweep_result),
            use_container_width=True,
            key="inverse_parameter_space_chart",
        )
        with st.expander("Parameter sweep results"):
            st.dataframe(sweep_result.sweep_table, use_container_width=True)

    st.plotly_chart(
        build_layer_stack_viewer(layer_stack),
        use_container_width=True,
        key="inverse_layer_stack_chart",
    )

    if inverse_result.uncertainty_summary is not None:
        confidence_frame = pd.DataFrame(
            [
                {
                    "parameter": parameter,
                    "best_estimate": inverse_result.uncertainty_summary.best_estimate.get(parameter, inverse_result.best_parameters.get(parameter)),
                    "ci_low": interval[0],
                    "ci_high": interval[1],
                }
                for parameter, interval in inverse_result.uncertainty_summary.confidence_intervals.items()
            ]
        )
        with st.expander("Uncertainty summary"):
            st.dataframe(confidence_frame, use_container_width=True)
            correlation_matrix = inverse_result.uncertainty_summary.correlation_matrix
            if correlation_matrix:
                st.dataframe(
                    pd.DataFrame(
                        correlation_matrix,
                        index=list(inverse_result.uncertainty_summary.parameter_distributions),
                        columns=list(inverse_result.uncertainty_summary.parameter_distributions),
                    ),
                    use_container_width=True,
                )

    digital_twin_payload = st.session_state.get("inverse_digital_twin")
    if digital_twin_payload is not None:
        with st.expander("Digital twin snapshot"):
            st.json(digital_twin_payload)

    validation_report = generate_validation_report()
    with st.expander("Validation benchmarks"):
        st.metric("Reference cases", int(validation_report.summary_metrics["num_cases"]))
        st.dataframe(pd.DataFrame(validation_report.cases), use_container_width=True)
        st.json(validation_report.summary_metrics)

    with st.expander("Synthetic dataset preview"):
        synthetic_stacks: list[LayerStack] = []
        for multiplier in [0.85, 1.0, 1.15]:
            synthetic_stack = LayerStack.from_dict(layer_stack.to_dict())
            material_layer = synthetic_stack.get_layer("material")
            if material_layer is not None:
                material_layer.epsilon_real = max(1.0, material_layer.epsilon_real * multiplier)
                material_layer.epsilon_imag = max(0.0, material_layer.epsilon_imag * multiplier)
            synthetic_stacks.append(synthetic_stack)
        synthetic_frame = generate_synthetic_dataset(
            sensor_type=forward_model_key,
            geometry=geometry_profile,
            layer_stacks=synthetic_stacks,
            frequency_hz=inverse_measurement.frequency_hz,
        )
        st.dataframe(synthetic_frame, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="LitePerm", layout="wide")
    initialise_state()

    experiment_db = get_experiment_database()
    material_db = get_material_database()
    plugins = discover_plugins()
    runnable_plugins = get_runnable_plugins()
    forward_models = discover_forward_models()
    inverse_solvers = discover_inverse_solvers()
    reference_materials = load_reference_materials()
    reference_names = list_reference_material_names()

    st.title("LitePerm")
    st.caption("Research-grade LiteVNA dielectric spectroscopy, RF sensing, and experiment management platform")

    with st.sidebar:
        st.header("Pipeline")
        selected_plugin = st.selectbox(
            "Transformation plugin",
            options=list(runnable_plugins),
            index=list(runnable_plugins).index("stuchly") if "stuchly" in runnable_plugins else 0,
            format_func=lambda item: runnable_plugins[item].metadata().get("display_name", item.title()),
        )
        apply_calibration = st.checkbox("Apply loaded OSL calibration", value=True)
        st.markdown("### Architecture")
        st.write("Device -> Raw Measurement -> Calibration -> Transformation Plugin -> Permittivity -> Visualisation -> Database")
        st.markdown("[Developer guide](docs/developer_guide.md)")
        st.markdown("[Architecture diagram](docs/architecture.md)")
        st.markdown("API launch: `uvicorn liteperm.api.app:create_api_app --factory`")

    tabs = st.tabs(
        [
            "Raw Measurement",
            "Live Measurement",
            "Calibration",
            "Sensor Geometry",
            "Material Properties",
            "Inverse Modelling",
            "Advanced Modelling",
            "Research Mode",
            "Experiment Explorer",
            "Material Database",
        ]
    )
    (
        raw_tab,
        live_tab,
        calibration_tab,
        geometry_tab,
        material_tab,
        inverse_tab,
        modelling_tab,
        research_tab,
        explorer_tab,
        materials_db_tab,
    ) = tabs

    with raw_tab:
        st.subheader("Import S11 data")
        uploader_column, example_column = st.columns([2, 1])
        with uploader_column:
            uploaded_file = st.file_uploader("Import Touchstone or CSV", type=["s1p", "csv"], key="dut_upload")
            if uploaded_file is not None:
                try:
                    st.session_state["measurement"] = parse_uploaded_measurement(uploaded_file)
                    st.session_state["processed_measurement"] = None
                    st.session_state["last_spectrum"] = None
                    reset_inverse_state()
                except Exception as error:
                    st.error(f"Failed to import measurement: {error}")
        with example_column:
            example_name = st.selectbox("Load example data", options=["None", "sample_touchstone.s1p", "sample_litevna.csv"])
            if st.button("Load example dataset"):
                load_example_dataset(example_name)

        measurement = st.session_state["measurement"]
        if measurement is None:
            st.warning("Import a LiteVNA S11 file to begin.")
        else:
            render_measurement_summary(measurement)
            st.write(f"Loaded source: `{measurement.source_name}`")
            plot_column_1, plot_column_2 = st.columns(2)
            with plot_column_1:
                st.plotly_chart(build_magnitude_plot(measurement), use_container_width=True, key="raw_magnitude_chart")
                st.plotly_chart(build_phase_plot(measurement), use_container_width=True, key="raw_phase_chart")
            with plot_column_2:
                smith_chart = build_smith_chart(measurement)
                st.plotly_chart(smith_chart, use_container_width=True, key="raw_smith_chart")
                render_figure_export(smith_chart, "raw_smith_chart")
            with st.expander("Measurement table"):
                st.dataframe(measurement.to_dataframe(), use_container_width=True)

    with live_tab:
        st.subheader("Live Measurement")
        device_candidates = discover_device_candidates()
        device_kind = st.selectbox(
            "Device backend",
            options=["litevna", "future_device"],
            index=0 if st.session_state["device_kind"] == "litevna" else 1,
            format_func=lambda item: "LiteVNA USB Serial" if item == "litevna" else "Simulated Future Device",
        )

        detected_ports = [candidate.port for candidate in device_candidates if candidate.port]
        default_port = "SIMULATED" if device_kind == "future_device" else (detected_ports[0] if detected_ports else "")
        selected_port = st.selectbox("Detected device port", options=detected_ports or [default_port], key="live_detected_port")
        manual_port = st.text_input("Manual COM port override", value=st.session_state["device_port"] if device_kind == "litevna" else "SIMULATED")
        port_to_use = manual_port.strip() or selected_port

        control_columns = st.columns(4)
        with control_columns[0]:
            if st.button("Connect Device"):
                try:
                    message = connect_selected_device(device_kind, port_to_use)
                    st.success(message)
                except Exception as error:
                    st.error(f"Connection failed: {error}")
        with control_columns[1]:
            if st.button("Test Connection"):
                device = st.session_state.get("device")
                if device is None:
                    st.info("Connect a device first.")
                else:
                    st.success("Device responded correctly.") if device.test_connection() else st.error("Device did not respond.")
        with control_columns[2]:
            if st.button("Disconnect"):
                disconnect_device()
                st.info("Device disconnected.")
        with control_columns[3]:
            device = st.session_state.get("device")
            if device is not None:
                st.metric("Connected", device.get_device_info().name)
            else:
                st.metric("Connected", "No")

        device = st.session_state.get("device")
        if device is not None:
            st.json(device.get_device_info().to_dict())

        sweep_columns = st.columns(5)
        with sweep_columns[0]:
            start_frequency_hz = st.number_input("Start Frequency (Hz)", value=1e8, step=1e6, format="%.0f")
        with sweep_columns[1]:
            stop_frequency_hz = st.number_input("Stop Frequency (Hz)", value=6e9, step=1e6, format="%.0f")
        with sweep_columns[2]:
            points = int(st.number_input("Number of Points", value=401, step=10))
        with sweep_columns[3]:
            output_power = int(st.slider("Output Power", min_value=1, max_value=3, value=2))
        with sweep_columns[4]:
            sweep_speed = st.selectbox("Sweep Speed", ["slow", "normal", "fast", "demo"], index=1)

        live_config = SweepConfig(
            start_frequency_hz=float(start_frequency_hz),
            stop_frequency_hz=float(stop_frequency_hz),
            points=points,
            output_power=output_power,
            sweep_speed=sweep_speed,
            average_count=4 if sweep_speed != "fast" else 1,
        )

        live_controls = st.columns(3)
        with live_controls[0]:
            if st.button("Start Sweep"):
                st.session_state["live_running"] = True
        with live_controls[1]:
            if st.button("Stop Sweep"):
                st.session_state["live_running"] = False
        with live_controls[2]:
            if st.button("Save Sweep") and st.session_state.get("live_last_result") is not None:
                st.session_state["measurement"] = st.session_state["live_last_result"].raw_measurement
                st.session_state["processed_measurement"] = st.session_state["live_last_result"].processed_measurement
                st.session_state["last_spectrum"] = st.session_state["live_last_result"].spectrum
                reset_inverse_state()
                st.success("Live sweep copied into the current analysis workspace.")

        live_placeholder = st.empty()
        if st.session_state["live_running"]:
            if device is None:
                st.error("Connect a device before starting a live sweep.")
                st.session_state["live_running"] = False
            else:
                pipeline = AcquisitionPipeline(device)
                for _ in range(3):
                    if not st.session_state["live_running"]:
                        break
                    try:
                        result = pipeline.run(
                            config=live_config,
                            geometry=st.session_state["geometry_profile"],
                            plugin_name=selected_plugin,
                            calibration_profile=st.session_state["calibration_profile"],
                            open_measurement=st.session_state["open_measurement"],
                            short_measurement=st.session_state["short_measurement"],
                            load_measurement=st.session_state["load_measurement"],
                        )
                        render_live_capture_results(result, live_placeholder)
                        time.sleep(0.25)
                    except Exception as error:
                        st.error(f"Live sweep failed: {error}")
                        st.session_state["live_running"] = False
                        break

        if st.session_state.get("live_last_result") is not None:
            with st.expander("Latest live measurement summary"):
                st.json(st.session_state["live_last_result"].to_dict())

    with calibration_tab:
        st.subheader("Open / Short / Load calibration")
        uploaders = st.columns(3)
        calibration_keys = [
            ("open_measurement", "Open standard", "open_upload"),
            ("short_measurement", "Short standard", "short_upload"),
            ("load_measurement", "Load standard", "load_upload"),
        ]
        for column, (state_key, label, upload_key) in zip(uploaders, calibration_keys, strict=True):
            with column:
                uploaded_standard = st.file_uploader(label, type=["s1p", "csv"], key=upload_key)
                if uploaded_standard is not None:
                    try:
                        st.session_state[state_key] = parse_uploaded_measurement(uploaded_standard)
                        st.success(f"{label} loaded")
                    except Exception as error:
                        st.error(f"{label} import failed: {error}")

        saved_profiles = list_saved_calibration_profiles()
        if saved_profiles:
            selected_saved_calibration = st.selectbox(
                "Load saved calibration profile",
                options=["None"] + [entry["path"] for entry in saved_profiles],
                format_func=lambda item: "None" if item == "None" else Path(item).stem,
            )
            if st.button("Load selected calibration profile") and selected_saved_calibration != "None":
                st.session_state["calibration_profile"] = load_calibration_profile(selected_saved_calibration)
                st.success("Calibration profile loaded from library.")

        calibration_profile = calibration_editor(reference_names, st.session_state["calibration_profile"])
        st.session_state["calibration_profile"] = calibration_profile

        action_columns = st.columns(2)
        with action_columns[0]:
            if st.button("Save calibration profile to library"):
                saved_path = save_calibration_profile_to_library(calibration_profile)
                st.success(f"Saved to `{saved_path}`")
        with action_columns[1]:
            st.download_button(
                "Download calibration YAML",
                data=calibration_profile_to_yaml(calibration_profile),
                file_name="calibration_profile.yaml",
                mime="application/x-yaml",
            )

        with st.expander("Reference material library"):
            st.dataframe(pd.DataFrame(reference_materials).T, use_container_width=True)

    with geometry_tab:
        st.subheader("Sensor geometry")
        saved_geometries = list_saved_geometry_profiles()
        if saved_geometries:
            selected_saved_geometry = st.selectbox(
                "Load saved geometry profile",
                options=["None"] + [entry["path"] for entry in saved_geometries],
                format_func=lambda item: "None" if item == "None" else Path(item).stem,
            )
            if st.button("Load selected geometry profile") and selected_saved_geometry != "None":
                st.session_state["geometry_profile"] = load_geometry_profile(selected_saved_geometry)
                st.success("Geometry profile loaded from library.")

        updated_geometry = geometry_editor(st.session_state["geometry_profile"])
        st.session_state["geometry_profile"] = updated_geometry

        sensor_model = build_sensor_model(
            updated_geometry,
            calibration=st.session_state["calibration_profile"],
            frequency_range_hz=(
                float(st.session_state["measurement"].frequency_hz.min()),
                float(st.session_state["measurement"].frequency_hz.max()),
            )
            if st.session_state["measurement"] is not None
            else (1e6, 6.3e9),
        )
        st.json(sensor_model.summary())

        geometry_actions = st.columns(2)
        with geometry_actions[0]:
            if st.button("Save geometry profile to library"):
                saved_path = save_geometry_profile_to_library(updated_geometry)
                st.success(f"Saved to `{saved_path}`")
        with geometry_actions[1]:
            st.download_button(
                "Download geometry YAML",
                data=geometry_profile_to_yaml(updated_geometry),
                file_name="geometry_profile.yaml",
                mime="application/x-yaml",
            )

        st.code(geometry_profile_to_yaml(updated_geometry), language="yaml")

    with material_tab:
        st.subheader("Material properties")
        measurement = st.session_state["measurement"]
        if measurement is None:
            st.warning("Import or capture a measurement before computing dielectric spectra.")
        else:
            spectrum, working_measurement = compute_current_spectrum(selected_plugin, apply_calibration)
            if spectrum is None:
                st.warning("No spectrum is available.")
            else:
                st.session_state["last_spectrum"] = spectrum
                metrics = st.columns(4)
                metrics[0].metric("Mean epsilon'", f"{spectrum.epsilon_prime.mean():.3f}")
                metrics[1].metric("Mean epsilon''", f"{spectrum.epsilon_double_prime.mean():.3f}")
                metrics[2].metric("Peak loss tangent", f"{spectrum.loss_tangent.max():.3f}")
                metrics[3].metric("Peak conductivity", f"{spectrum.conductivity_s_per_m.max():.3f} S/m")
                st.write(f"Working measurement: `{working_measurement.source_name or 'Imported measurement'}`")

                epsilon_figure = build_epsilon_plot(spectrum)
                st.plotly_chart(epsilon_figure, use_container_width=True, key="material_epsilon_chart")
                lower_left, lower_right = st.columns(2)
                with lower_left:
                    st.plotly_chart(build_loss_tangent_plot(spectrum), use_container_width=True, key="material_loss_tangent_chart")
                    st.plotly_chart(build_nyquist_plot(spectrum), use_container_width=True, key="material_nyquist_chart")
                with lower_right:
                    st.plotly_chart(build_impedance_plot(spectrum), use_container_width=True, key="material_impedance_chart")
                    st.plotly_chart(build_admittance_plot(spectrum), use_container_width=True, key="material_admittance_chart")
                    render_figure_export(epsilon_figure, "dielectric_spectrum")

                st.download_button(
                    "Download dielectric spectrum CSV",
                    data=spectrum_to_csv_bytes(spectrum),
                    file_name="liteperm_spectrum.csv",
                    mime="text/csv",
                )
                with st.expander("Spectrum table"):
                    st.dataframe(spectrum.to_dataframe(), use_container_width=True)

    with inverse_tab:
        render_inverse_modelling_tab(forward_models=forward_models, inverse_solvers=inverse_solvers)

    with modelling_tab:
        st.subheader("Advanced Modelling")
        plugin_cards = st.columns(min(3, len(plugins)))
        for index, (plugin_name, plugin) in enumerate(plugins.items()):
            with plugin_cards[index % len(plugin_cards)]:
                metadata = plugin.metadata()
                st.markdown(f"### {metadata.get('display_name', plugin_name.title())}")
                st.caption(metadata.get("validation_status", "unknown").title())
                st.write(plugin.description())
                st.write(metadata.get("assumptions", ""))

        measurement = st.session_state["measurement"]
        if measurement is not None:
            comparison_rows: list[dict[str, Any]] = []
            for plugin_name in runnable_plugins:
                spectrum, _ = compute_material_spectrum(measurement, st.session_state["geometry_profile"], method=plugin_name)
                comparison_rows.append(
                    {
                        "Plugin": plugin_name,
                        "Display Name": runnable_plugins[plugin_name].metadata().get("display_name", plugin_name.title()),
                        "Validation": runnable_plugins[plugin_name].metadata().get("validation_status", "unknown"),
                        "Mean epsilon'": float(spectrum.epsilon_prime.mean()),
                        "Mean epsilon''": float(spectrum.epsilon_double_prime.mean()),
                        "Peak loss tangent": float(spectrum.loss_tangent.max()),
                    }
                )
            st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True)

        st.markdown("### Plugin Registry")
        plugin_rows = []
        for plugin_name, plugin in plugins.items():
            metadata = plugin.metadata()
            plugin_rows.append(
                {
                    "Plugin": plugin_name,
                    "Implemented": metadata.get("implemented", True),
                    "Validation": metadata.get("validation_status", "unknown"),
                    "Family": metadata.get("family", ""),
                    "Description": plugin.description(),
                }
            )
        st.dataframe(pd.DataFrame(plugin_rows), use_container_width=True)

        st.markdown("### AI Dataset Preview")
        experiment_rows = experiment_db.list_experiments()
        if experiment_rows:
            records = [experiment_db.get_experiment(row["experiment_id"]) for row in experiment_rows[:10]]
            st.dataframe(build_experiment_dataset(records), use_container_width=True)
        else:
            st.caption("Save experiments in Research Mode to build future ML datasets.")

    with research_tab:
        st.subheader("Research Mode")
        measurement = st.session_state["measurement"]
        spectrum = st.session_state["last_spectrum"]
        default_experiment_name = measurement.source_name if measurement is not None and measurement.source_name else "LitePerm Experiment"
        metadata = build_research_metadata(default_experiment_name)

        if measurement is None or spectrum is None:
            st.info("Compute or capture a measurement before saving a research experiment.")
        else:
            if st.button("Save Experiment"):
                try:
                    record = experiment_db.save_experiment(
                        metadata=metadata,
                        raw_measurement=measurement,
                        processed_measurement=st.session_state.get("processed_measurement") or measurement,
                        spectrum=spectrum,
                        calibration_profile=st.session_state["calibration_profile"],
                        geometry_profile=st.session_state["geometry_profile"],
                        inverse_result=st.session_state.get("inverse_result"),
                        digital_twin=st.session_state.get("inverse_digital_twin"),
                    )
                    st.session_state["last_saved_experiment_id"] = record.experiment_id
                    st.success(f"Experiment saved as `{record.experiment_id}`")
                except Exception as error:
                    st.error(f"Experiment save failed: {error}")

            if st.session_state.get("last_saved_experiment_id"):
                record = experiment_db.get_experiment(st.session_state["last_saved_experiment_id"])
                st.json(record.to_summary_dict())

    with explorer_tab:
        st.subheader("Experiment Explorer")
        search_columns = st.columns(4)
        with search_columns[0]:
            search_text = st.text_input("Search", value="")
        with search_columns[1]:
            sensor_filter = st.text_input("Filter by sensor type", value="")
        with search_columns[2]:
            project_filter = st.text_input("Filter by project", value="")
        with search_columns[3]:
            sort_by = st.selectbox("Sort by", ["created_at", "experiment_name", "project_name", "researcher"])

        experiment_rows = experiment_db.list_experiments(search=search_text, sensor_type=sensor_filter, project_name=project_filter, sort_by=sort_by)
        if not experiment_rows:
            st.caption("No saved experiments yet.")
        else:
            explorer_frame = pd.DataFrame(experiment_rows)
            st.dataframe(explorer_frame, use_container_width=True)
            experiment_options = explorer_frame["experiment_id"].tolist()
            selected_experiment_id = st.selectbox("Open Previous Experiment", experiment_options)
            explorer_actions = st.columns(4)
            with explorer_actions[0]:
                if st.button("Open Selected Experiment"):
                    record = experiment_db.get_experiment(selected_experiment_id)
                    st.session_state["measurement"] = record.raw_measurement
                    st.session_state["processed_measurement"] = record.processed_measurement
                    st.session_state["last_spectrum"] = record.spectrum
                    st.session_state["calibration_profile"] = record.calibration_profile
                    st.session_state["geometry_profile"] = record.geometry_profile
                    st.session_state["inverse_result"] = record.inverse_result
                    st.session_state["inverse_digital_twin"] = record.digital_twin
                    st.session_state["inverse_sweep_result"] = None
                    if record.digital_twin and record.digital_twin.get("layer_stack"):
                        st.session_state["inverse_layer_stack"] = LayerStack.from_dict(record.digital_twin["layer_stack"])
                    else:
                        st.session_state["inverse_layer_stack"] = default_layer_stack(record.geometry_profile.sensor_type)
                    st.success(f"Loaded `{record.experiment_id}` into the workspace.")
            with explorer_actions[1]:
                if st.button("Duplicate Experiment"):
                    duplicated = experiment_db.duplicate_experiment(selected_experiment_id)
                    st.success(f"Duplicated as `{duplicated.experiment_id}`")
            with explorer_actions[2]:
                archive_bytes = experiment_db.export_experiment(selected_experiment_id)
                st.download_button(
                    "Export Experiment",
                    data=archive_bytes,
                    file_name=f"{selected_experiment_id}.zip",
                    mime="application/zip",
                )
            with explorer_actions[3]:
                if st.button("Delete Experiment"):
                    experiment_db.delete_experiment(selected_experiment_id)
                    st.success(f"Deleted `{selected_experiment_id}`")
                    st.rerun()

    with materials_db_tab:
        st.subheader("Material Database")
        search = st.text_input("Search materials", value="")
        materials_frame = pd.DataFrame(material_db.list_materials(search=search))
        if not materials_frame.empty:
            st.dataframe(materials_frame, use_container_width=True)

        st.markdown("### Add Material")
        add_columns = st.columns(2)
        with add_columns[0]:
            material_name = st.text_input("Material Name", value="Custom Material")
            category = st.text_input("Category", value="user")
            epsilon_real = st.number_input("epsilon' reference", value=2.5, step=0.1)
            epsilon_imag = st.number_input("epsilon'' reference", value=0.05, step=0.01)
            conductivity = st.number_input("Conductivity (S/m)", value=0.001, step=0.001, format="%.6f")
        with add_columns[1]:
            loss_tangent = st.number_input("Loss tangent", value=0.02, step=0.01)
            source = st.text_input("Source", value="User entry")
            references = st.text_input("References", value="")
            notes = st.text_area("Notes", value="")
        if st.button("Add Material to Database"):
            material_db.add_material(
                {
                    "material_name": material_name,
                    "category": category,
                    "epsilon_real": float(epsilon_real),
                    "epsilon_imag": float(epsilon_imag),
                    "loss_tangent": float(loss_tangent),
                    "conductivity_s_per_m": float(conductivity),
                    "frequency_range_hz": [50e3, 6.3e9],
                    "source": source,
                    "references": references,
                    "notes": notes,
                }
            )
            st.success(f"Added `{material_name}`")
            st.rerun()


if __name__ == "__main__":
    main()
