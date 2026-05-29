from __future__ import annotations

import json
import time
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

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
from liteperm.inverse.common import InverseResult, LayerStack, ParameterSweepResult, residual_measurement
from liteperm.inverse.forward_models import build_forward_model, discover_forward_models
from liteperm.inverse.inverse_solvers import discover_inverse_solvers
from liteperm.inverse.optimisers.error_metrics import compute_scalar_error
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
from liteperm.permittivity import (
    PermittivityMeasurementResult,
    comparisons_to_frame,
    compare_to_reference_materials,
    identify_closest_materials,
    run_permittivity_measurement,
    validate_permittivity_measurement,
)
from liteperm.plugins.manager import discover_plugins, get_runnable_plugins
from liteperm.sensors import build_sensor_model
from liteperm.solvers import build_solver_adapter, discover_solver_adapters, solver_status_rows
from liteperm.solvers.result import SimulationResult
from liteperm.solvers.utils import cache_directory, simulation_cache_key, sweep_config_from_frequency_axis
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
WORKFLOW_PAGES = [
    "Home",
    "Connect LiteVNA",
    "Calibration Wizard",
    "Sensor Setup",
    "Measure Material",
    "Permittivity Results",
    "Research Mode",
    "Advanced Tools",
]
SENSOR_LABELS = {
    "open_ended_coax_probe": "Open Ended Coax Probe",
    "patch_antenna": "Patch Sensor",
    "microstrip_resonator": "Microstrip Resonator",
    "generic_resonator": "Custom Sensor",
}
DISPLAY_TO_SENSOR = {label: key for key, label in SENSOR_LABELS.items()}


@st.cache_resource
def get_experiment_database() -> ExperimentDatabase:
    return ExperimentDatabase()


@st.cache_resource
def get_material_database() -> MaterialDatabase:
    return MaterialDatabase()


def initialise_state() -> None:
    defaults: dict[str, Any] = {
        "user_mode": "Basic",
        "workflow_page": "Home",
        "measurement": None,
        "processed_measurement": None,
        "permittivity_result": None,
        "last_validation_result": None,
        "last_reference_comparisons": None,
        "last_material_matches": None,
        "open_measurement": None,
        "short_measurement": None,
        "load_measurement": None,
        "reference_measurement_1": None,
        "reference_measurement_2": None,
        "reference_material_1": "Water",
        "reference_material_2": "Methanol",
        "calibration_wizard_step": 0,
        "calibration_profile": build_calibration_profile("Default OSL"),
        "geometry_profile": build_geometry_profile("open_ended_coax_probe"),
        "selected_permittivity_method": "stuchly",
        "selected_reference_material": "Water",
        "last_spectrum": None,
        "device": None,
        "device_kind": "litevna",
        "device_port": "",
        "measurement_start_frequency_hz": 1e8,
        "measurement_stop_frequency_hz": 6e9,
        "measurement_points": 401,
        "measurement_output_power": 2,
        "measurement_sweep_speed": "normal",
        "live_running": False,
        "live_last_result": None,
        "live_render_nonce": 0,
        "last_saved_experiment_id": "",
        "inverse_layer_stack": default_layer_stack("open_ended_coax_probe"),
        "inverse_result": None,
        "inverse_digital_twin": None,
        "inverse_sweep_result": None,
        "full_wave_layer_stack": default_layer_stack("open_ended_coax_probe"),
        "full_wave_result": None,
        "full_wave_job": None,
        "docs_demo_marker": "",
        "docs_inverse_demo_marker": "",
        "docs_full_wave_demo_marker": "",
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


def reset_permittivity_state() -> None:
    st.session_state["permittivity_result"] = None
    st.session_state["last_validation_result"] = None
    st.session_state["last_reference_comparisons"] = None
    st.session_state["last_material_matches"] = None
    st.session_state["last_spectrum"] = None
    st.session_state["processed_measurement"] = None


def reset_full_wave_state(*, preserve_layer_stack: bool = True) -> None:
    st.session_state["full_wave_result"] = None
    st.session_state["full_wave_job"] = None
    if not preserve_layer_stack:
        st.session_state["full_wave_layer_stack"] = default_layer_stack(st.session_state["geometry_profile"].sensor_type)


def _query_param_value(name: str, default: str = "") -> str:
    value = st.query_params.get(name, default)
    if isinstance(value, list):
        return str(value[0]) if value else default
    return str(value)


def render_measurement_summary(measurement: MeasurementData) -> None:
    start_ghz = measurement.frequency_hz.min() / 1e9
    stop_ghz = measurement.frequency_hz.max() / 1e9
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Samples", f"{measurement.frequency_hz.size}")
    metric_2.metric("Start", f"{start_ghz:.4f} GHz")
    metric_3.metric("Stop", f"{stop_ghz:.4f} GHz")
    metric_4.metric("Span", f"{stop_ghz - start_ghz:.4f} GHz")


def workflow_sensor_label(sensor_type: str) -> str:
    return SENSOR_LABELS.get(sensor_type, sensor_type.replace("_", " ").title())


def active_sweep_config() -> SweepConfig:
    return SweepConfig(
        start_frequency_hz=float(st.session_state["measurement_start_frequency_hz"]),
        stop_frequency_hz=float(st.session_state["measurement_stop_frequency_hz"]),
        points=int(st.session_state["measurement_points"]),
        output_power=int(st.session_state["measurement_output_power"]),
        sweep_speed=str(st.session_state["measurement_sweep_speed"]),
        average_count=4 if st.session_state["measurement_sweep_speed"] != "fast" else 1,
        channel="S11",
    )


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


def apply_documentation_demo_state(selected_plugin: str) -> None:
    demo = _query_param_value("demo", "").strip().lower()
    if not demo:
        return

    if st.session_state.get("docs_demo_marker") != demo:
        if demo == "sample_touchstone":
            st.session_state["measurement"] = load_measurement(EXAMPLE_ROOT / "sample_touchstone.s1p")
            st.session_state["geometry_profile"] = build_geometry_profile("open_ended_coax_probe")
        elif demo == "sample_csv":
            st.session_state["measurement"] = load_measurement(EXAMPLE_ROOT / "sample_litevna.csv")
            st.session_state["geometry_profile"] = build_geometry_profile("open_ended_coax_probe")
        elif demo == "synthetic_patch":
            geometry_profile = build_geometry_profile("patch_antenna")
            truth_stack = default_layer_stack("patch_antenna")
            material_layer = truth_stack.get_layer("material")
            if material_layer is not None:
                material_layer.material_name = "Water Demo"
                material_layer.epsilon_real = 18.5
                material_layer.epsilon_imag = 3.2
                material_layer.conductivity_s_per_m = 0.35
                material_layer.loss_tangent = 0.17
                material_layer.thickness_m = 1.2e-3
            measurement = build_forward_model("patch_antenna", geometry=geometry_profile, layer_stack=truth_stack).simulate(
                pd.Series(range(241), dtype=float).to_numpy() * 5e6 + 1.8e9
            ).measurement
            measurement.source_name = "Synthetic Patch Demo"
            st.session_state["measurement"] = measurement
            st.session_state["geometry_profile"] = geometry_profile
            inverse_guess = default_layer_stack("patch_antenna")
            inverse_material_layer = inverse_guess.get_layer("material")
            if inverse_material_layer is not None:
                inverse_material_layer.epsilon_real = 7.5
                inverse_material_layer.epsilon_imag = 0.9
                inverse_material_layer.conductivity_s_per_m = 0.08
            st.session_state["inverse_layer_stack"] = inverse_guess
            st.session_state["full_wave_layer_stack"] = default_layer_stack("patch_antenna")
        else:
            return

        st.session_state["processed_measurement"] = None
        st.session_state["last_spectrum"] = None
        reset_permittivity_state()
        reset_inverse_state(preserve_layer_stack=demo == "synthetic_patch")
        reset_full_wave_state(preserve_layer_stack=demo == "synthetic_patch")
        if demo != "synthetic_patch":
            st.session_state["inverse_layer_stack"] = default_layer_stack(st.session_state["geometry_profile"].sensor_type)
            st.session_state["full_wave_layer_stack"] = default_layer_stack(st.session_state["geometry_profile"].sensor_type)
        st.session_state["docs_demo_marker"] = demo
        st.session_state["docs_inverse_demo_marker"] = ""
        st.session_state["docs_full_wave_demo_marker"] = ""

    measurement = st.session_state.get("measurement")
    if measurement is None:
        return

    spectrum, working_measurement = compute_material_spectrum(
        measurement,
        st.session_state["geometry_profile"],
        method=selected_plugin,
    )
    st.session_state["processed_measurement"] = working_measurement
    st.session_state["last_spectrum"] = spectrum

    if _query_param_value("docs_full_wave", "0") == "1":
        full_wave_marker = f"{demo}:{selected_plugin}"
        if st.session_state.get("docs_full_wave_demo_marker") != full_wave_marker:
            simulation = build_forward_model(
                "full_wave",
                geometry=st.session_state["geometry_profile"],
                layer_stack=st.session_state["full_wave_layer_stack"],
                metadata_overrides={"simulation_backend": "analytical"},
            ).simulate(measurement.frequency_hz)
            full_wave_result = SimulationResult.from_measurement(
                simulation.measurement,
                solver_metadata=simulation.metadata | {
                    "solver_name": "openems",
                    "execution_mode": "documentation_demo",
                    "source_name": "Documentation Full-Wave Demo",
                },
                runtime_seconds=0.18,
            )
            st.session_state["full_wave_result"] = full_wave_result.to_dict()
            st.session_state["docs_full_wave_demo_marker"] = full_wave_marker

    if demo == "synthetic_patch" and _query_param_value("docs_inverse", "0") == "1":
        inverse_marker = f"{demo}:{selected_plugin}"
        if st.session_state.get("docs_inverse_demo_marker") != inverse_marker:
            result, twin, sweep_result = run_inverse_estimation(
                measurement=measurement,
                geometry=st.session_state["geometry_profile"],
                calibration_profile=st.session_state["calibration_profile"],
                layer_stack=st.session_state["inverse_layer_stack"],
                forward_model_key="patch_antenna",
                solver_name="least_squares",
                parameter_names=["material_epsilon_real", "material_epsilon_imag", "material_conductivity_s_per_m"],
                error_metric="weighted_error",
                solver_options={},
                run_monte_carlo=False,
                run_bootstrap=False,
            )
            st.session_state["inverse_result"] = result.to_dict()
            st.session_state["inverse_digital_twin"] = twin.to_dict()
            st.session_state["inverse_sweep_result"] = sweep_result.to_dict()
            st.session_state["docs_inverse_demo_marker"] = inverse_marker


def load_example_dataset(example_name: str) -> None:
    if example_name == "None":
        return
    st.session_state["measurement"] = load_measurement(EXAMPLE_ROOT / example_name)
    reset_permittivity_state()
    reset_inverse_state()
    reset_full_wave_state()


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
    reset_full_wave_state()
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


def ensure_layer_stack_state(state_key: str, sensor_type: str) -> None:
    current_stack = st.session_state.get(state_key)
    if current_stack is None or current_stack.metadata.get("sensor_type") != sensor_type:
        st.session_state[state_key] = default_layer_stack(sensor_type)


def render_layer_stack_editor(*, state_key: str, sensor_type: str, key_prefix: str):
    ensure_layer_stack_state(state_key, sensor_type)
    layer_stack = st.session_state[state_key]
    editor_frame = layer_stack_to_frame(layer_stack)
    edited_frame = st.data_editor(
        editor_frame,
        num_rows="dynamic",
        use_container_width=True,
        key=f"{key_prefix}_layer_stack_editor_{sensor_type}",
    )
    updated_stack = layer_stack_from_frame(pd.DataFrame(edited_frame))
    updated_stack.metadata["sensor_type"] = sensor_type
    st.session_state[state_key] = updated_stack
    return updated_stack


def render_inverse_layer_stack_editor(sensor_type: str):
    return render_layer_stack_editor(state_key="inverse_layer_stack", sensor_type=sensor_type, key_prefix="inverse")


def render_full_wave_layer_stack_editor(sensor_type: str):
    return render_layer_stack_editor(state_key="full_wave_layer_stack", sensor_type=sensor_type, key_prefix="full_wave")


def build_phase_comparison_plot(measured: MeasurementData, predicted: MeasurementData):
    figure = build_phase_plot(measured)
    figure.data = []
    frequency_measured = measured.frequency_hz / 1e9
    frequency_predicted = predicted.frequency_hz / 1e9
    figure.add_scatter(x=frequency_measured, y=measured.phase_deg, mode="lines", name="Measured phase")
    figure.add_scatter(x=frequency_predicted, y=predicted.phase_deg, mode="lines", name="Simulated phase")
    figure.update_layout(title="Measured vs Simulated Phase")
    return figure


def apply_documentation_tab_selection() -> None:
    target_tab = _query_param_value("docs_tab", "").strip()
    if not target_tab:
        return
    components.html(
        f"""
        <script>
        const targetTab = {json.dumps(target_tab)};
        let attempts = 0;
        const activateTab = () => {{
            const root = window.parent.document;
            const tabs = Array.from(root.querySelectorAll('button[role="tab"]'));
            const match = tabs.find((tab) => (tab.innerText || '').trim() === targetTab);
            if (match) {{
                if (match.getAttribute('aria-selected') !== 'true') {{
                    match.click();
                }}
                clearInterval(timer);
            }}
            attempts += 1;
            if (attempts > 60) {{
                clearInterval(timer);
            }}
        }};
        const timer = setInterval(activateTab, 250);
        activateTab();
        </script>
        """,
        height=0,
        width=0,
    )


def build_full_wave_forward_options(*, key_prefix: str) -> dict[str, Any]:
    solver_adapters = discover_solver_adapters()
    backend_columns = st.columns(4)
    with backend_columns[0]:
        simulation_backend = st.selectbox(
            "Simulation backend",
            options=["analytical", "openems", "cached", "surrogate"],
            format_func=lambda item: {
                "analytical": "Analytical baseline",
                "openems": "openEMS simulation",
                "cached": "Cached simulation result",
                "surrogate": "Future surrogate model",
            }[item],
            key=f"{key_prefix}_simulation_backend",
        )
    with backend_columns[1]:
        solver_name = st.selectbox(
            "Solver adapter",
            options=list(solver_adapters),
            index=list(solver_adapters).index("openems") if "openems" in solver_adapters else 0,
            format_func=lambda item: item.upper() if item in {"hfss", "cst"} else item.title(),
            key=f"{key_prefix}_solver_name",
            disabled=simulation_backend == "analytical",
        )
    with backend_columns[2]:
        project_name = st.text_input("Simulation project", value="LitePerm Research", key=f"{key_prefix}_project_name")
    with backend_columns[3]:
        force_rerun = st.checkbox("Force rerun", value=False, key=f"{key_prefix}_force_rerun", disabled=simulation_backend != "openems")

    detail_columns = st.columns(3)
    with detail_columns[0]:
        mesh_quality = st.selectbox("Mesh quality", options=["coarse", "medium", "fine"], index=1, key=f"{key_prefix}_mesh_quality")
    with detail_columns[1]:
        output_power = int(st.slider("Excitation power", min_value=0, max_value=3, value=0, key=f"{key_prefix}_output_power"))
    with detail_columns[2]:
        allow_fallback = st.checkbox(
            "Allow analytical fallback",
            value=False,
            key=f"{key_prefix}_allow_fallback",
            disabled=simulation_backend == "analytical",
        )

    cells_per_wavelength = {"coarse": 12, "medium": 20, "fine": 30}[mesh_quality]
    return {
        "simulation_backend": simulation_backend,
        "solver_name": solver_name,
        "project_name": project_name,
        "force_rerun": force_rerun,
        "allow_analytical_fallback": allow_fallback,
        "mesh_settings": {"quality": mesh_quality, "cells_per_wavelength": cells_per_wavelength},
        "boundary_conditions": {"x": "PML", "y": "PML", "z": "PML"},
        "excitation_settings": {"output_power": output_power},
    }


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


def render_full_wave_simulation_tab() -> None:
    st.subheader("Full-Wave Simulation")

    solver_frame = pd.DataFrame(solver_status_rows())
    st.markdown("### Solver Status")
    st.dataframe(solver_frame, use_container_width=True)

    geometry_profile = st.session_state["geometry_profile"]
    measurement = st.session_state.get("measurement")
    processed_measurement = st.session_state.get("processed_measurement")
    sensor_type = geometry_profile.sensor_type or "generic_resonator"
    sweep_defaults = (
        float(measurement.frequency_hz.min()),
        float(measurement.frequency_hz.max()),
        int(measurement.frequency_hz.size),
    ) if measurement is not None else (1e8, 3e9, 401)

    st.markdown("### Simulation Setup")
    setup_columns = st.columns(4)
    with setup_columns[0]:
        solver_name = st.selectbox(
            "Solver",
            options=list(discover_solver_adapters()),
            index=list(discover_solver_adapters()).index("openems") if "openems" in discover_solver_adapters() else 0,
            format_func=lambda item: item.upper() if item in {"hfss", "cst"} else item.title(),
            key="full_wave_solver_name",
        )
    with setup_columns[1]:
        start_frequency_hz = float(st.number_input("Start Frequency (Hz)", value=sweep_defaults[0], step=1e6, format="%.0f", key="full_wave_start_hz"))
    with setup_columns[2]:
        stop_frequency_hz = float(st.number_input("Stop Frequency (Hz)", value=sweep_defaults[1], step=1e6, format="%.0f", key="full_wave_stop_hz"))
    with setup_columns[3]:
        points = int(st.number_input("Number of Points", value=sweep_defaults[2], step=10, key="full_wave_points"))

    option_columns = st.columns(4)
    with option_columns[0]:
        project_name = st.text_input("Project name", value="LitePerm Research", key="full_wave_project_name")
    with option_columns[1]:
        mesh_quality = st.selectbox("Mesh quality", ["coarse", "medium", "fine"], index=1, key="full_wave_mesh_quality")
    with option_columns[2]:
        use_cache = st.checkbox("Reuse cache", value=True, key="full_wave_use_cache")
    with option_columns[3]:
        force_rerun = st.checkbox("Force rerun", value=False, key="full_wave_force_rerun")

    selected_adapter = build_solver_adapter(solver_name)
    environment = selected_adapter.validate_environment()
    status_message = f"{solver_name} status: `{environment.get('status', 'unknown')}`"
    if environment.get("available"):
        st.success(status_message)
    else:
        st.warning(status_message)
    for message in environment.get("messages", []):
        st.caption(message)
    if environment.get("setup_guide"):
        st.caption(f"Setup guide: `{environment['setup_guide']}`")

    st.markdown("### Material Stack")
    layer_stack = render_full_wave_layer_stack_editor(sensor_type)

    sweep_config = SweepConfig(
        start_frequency_hz=start_frequency_hz,
        stop_frequency_hz=stop_frequency_hz,
        points=points,
        output_power=0,
        sweep_speed="simulation",
        average_count=1,
        channel="S11",
    )
    mesh_settings = {
        "quality": mesh_quality,
        "cells_per_wavelength": {"coarse": 12, "medium": 20, "fine": 30}[mesh_quality],
    }
    excitation_settings = {"output_power": 0}
    cache_key = simulation_cache_key(
        solver_name=solver_name,
        sensor_type=sensor_type,
        geometry_profile=geometry_profile,
        material_stack=layer_stack,
        sweep_config=sweep_config,
        mesh_settings=mesh_settings,
        boundary_conditions={"x": "PML", "y": "PML", "z": "PML"},
        excitation_settings=excitation_settings,
    )
    simulation_output_dir = cache_directory(project_name, cache_key)
    st.caption(f"Simulation cache directory: `{simulation_output_dir}`")

    if st.button("Run Full-Wave Simulation", key="full_wave_run_button"):
        try:
            job = selected_adapter.build_job(
                geometry_profile,
                layer_stack,
                sweep_config,
                simulation_output_dir,
                mesh_settings=mesh_settings,
                boundary_conditions={"x": "PML", "y": "PML", "z": "PML"},
                excitation_settings=excitation_settings,
                cache_key=cache_key,
                metadata={"project_name": project_name, "workflow": "full_wave_tab"},
            )
            result_file = simulation_output_dir / "simulation_result.json"
            touchstone_file = simulation_output_dir / "simulated_response.s1p"
            if use_cache and not force_rerun and (result_file.exists() or touchstone_file.exists()):
                result = selected_adapter.parse_results(job)
                st.info(f"Loaded cached simulation `{cache_key}`.")
            else:
                result = selected_adapter.run(job)
                st.success(f"Simulation completed with `{solver_name}`.")
            st.session_state["full_wave_job"] = job.to_dict()
            st.session_state["full_wave_result"] = result.to_dict()
        except Exception as error:
            st.error(f"Full-wave simulation failed: {error}")

    result_payload = st.session_state.get("full_wave_result")
    if result_payload is None:
        st.info("Run a full-wave simulation to visualise simulated S11, inspect the solver exports, and compare measured versus simulated responses.")
        return

    result = SimulationResult.from_dict(result_payload)
    simulation_measurement = result.measurement
    simulation_spectrum = result.to_material_spectrum()

    st.markdown("### Results")
    result_metrics = st.columns(4)
    result_metrics[0].metric("Solver", result.solver_metadata.get("solver_name", solver_name))
    result_metrics[1].metric("Points", f"{result.frequency_hz.size}")
    result_metrics[2].metric("Runtime", f"{result.runtime_seconds:.2f} s" if result.runtime_seconds is not None else "n/a")
    result_metrics[3].metric("Cache Key", result.solver_metadata.get("cache_key", cache_key))

    result_columns = st.columns(2)
    with result_columns[0]:
        st.plotly_chart(build_magnitude_plot(simulation_measurement), use_container_width=True, key="full_wave_magnitude_chart")
        st.plotly_chart(build_phase_plot(simulation_measurement), use_container_width=True, key="full_wave_phase_chart")
    with result_columns[1]:
        st.plotly_chart(build_smith_chart(simulation_measurement), use_container_width=True, key="full_wave_smith_chart")
        st.plotly_chart(build_impedance_plot(simulation_spectrum), use_container_width=True, key="full_wave_impedance_chart")

    st.plotly_chart(build_admittance_plot(simulation_spectrum), use_container_width=True, key="full_wave_admittance_chart")

    export_columns = st.columns(2)
    touchstone_path = Path(result.touchstone_export_path) if result.touchstone_export_path else None
    csv_path = Path(result.csv_export_path) if result.csv_export_path else None
    with export_columns[0]:
        if touchstone_path is not None and touchstone_path.exists():
            st.download_button(
                "Download Touchstone",
                data=touchstone_path.read_bytes(),
                file_name=touchstone_path.name,
                mime="text/plain",
                key="full_wave_touchstone_download",
            )
    with export_columns[1]:
        if csv_path is not None and csv_path.exists():
            st.download_button(
                "Download CSV",
                data=csv_path.read_bytes(),
                file_name=csv_path.name,
                mime="text/csv",
                key="full_wave_csv_download",
            )

    st.markdown("### Comparison Mode")
    comparison_options = st.columns(2)
    with comparison_options[0]:
        comparison_input_mode = st.selectbox(
            "Reference measurement",
            options=["processed", "raw"],
            index=0 if processed_measurement is not None else 1,
            format_func=lambda item: "Processed / calibrated S11" if item == "processed" else "Raw measured S11",
            key="full_wave_comparison_input",
        )
    with comparison_options[1]:
        comparison_metric = st.selectbox(
            "Comparison metric",
            options=["rmse", "mse", "mae", "weighted_error", "complex_error"],
            index=0,
            key="full_wave_comparison_metric",
        )

    reference_measurement = processed_measurement if comparison_input_mode == "processed" and processed_measurement is not None else measurement
    if reference_measurement is None:
        st.info("Import or capture a measured response to compare it against the simulated full-wave result.")
    elif reference_measurement.frequency_hz.size != simulation_measurement.frequency_hz.size:
        st.warning("Measured and simulated responses currently use different frequency grids, so direct residual comparison is disabled.")
    else:
        residual = residual_measurement(reference_measurement, simulation_measurement)
        comparison_error = compute_scalar_error(reference_measurement, simulation_measurement, metric=comparison_metric)
        st.metric(comparison_metric.upper(), f"{comparison_error:.4f}")

        overlay_columns = st.columns(2)
        with overlay_columns[0]:
            st.plotly_chart(
                build_measured_vs_predicted_plot(reference_measurement, simulation_measurement),
                use_container_width=True,
                key="full_wave_measured_vs_simulated_magnitude_chart",
            )
            st.plotly_chart(
                build_phase_comparison_plot(reference_measurement, simulation_measurement),
                use_container_width=True,
                key="full_wave_measured_vs_simulated_phase_chart",
            )
        with overlay_columns[1]:
            st.plotly_chart(
                build_smith_comparison_plot(reference_measurement, simulation_measurement),
                use_container_width=True,
                key="full_wave_smith_comparison_chart",
            )
            st.plotly_chart(
                build_residual_plot(residual),
                use_container_width=True,
                key="full_wave_residual_chart",
            )

    with st.expander("Simulation metadata"):
        st.json(result.solver_metadata)
    with st.expander("Simulation table"):
        st.dataframe(result.to_dataframe(), use_container_width=True)


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
    forward_model_registry = list(forward_models)
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
            options=forward_model_registry,
            index=forward_model_registry.index(default_forward_model),
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

    full_wave_options: dict[str, Any] | None = None
    layer_stack_sensor_type = geometry_profile.sensor_type if forward_model_key == "full_wave" else forward_model_key
    if forward_model_key == "full_wave":
        st.markdown("### Full-Wave Forward Model")
        st.caption("Use the analytical baseline by default, then switch to cached or solver-backed simulations when you need higher-fidelity forward responses.")
        full_wave_options = build_full_wave_forward_options(key_prefix="inverse_full_wave")
        if full_wave_options["simulation_backend"] == "cached":
            st.caption("Cached mode reuses previously exported solver results from the simulation cache.")
    elif forward_model_key == "patch_antenna":
        st.markdown("### Patch Antenna Material Characterisation Mode")
        st.caption("Use this mode to estimate multilayer dielectric properties directly from the measured resonance shift and S11 shape.")

    layer_stack = render_inverse_layer_stack_editor(layer_stack_sensor_type)
    model_kwargs: dict[str, Any] = {"geometry": geometry_profile, "layer_stack": layer_stack}
    if full_wave_options:
        model_kwargs["metadata_overrides"] = full_wave_options
    model = build_forward_model(forward_model_key, **model_kwargs)
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
                    forward_model_options=full_wave_options,
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


def reference_material_payloads(material_db: MaterialDatabase) -> list[dict[str, Any]]:
    payloads = material_db.list_material_payloads()
    return payloads or list(load_reference_materials().values())


def current_permittivity_result() -> PermittivityMeasurementResult | None:
    payload = st.session_state.get("permittivity_result")
    if not payload:
        return None
    return PermittivityMeasurementResult.from_dict(payload)


def calibration_measurements_ready() -> bool:
    return all(
        st.session_state.get(key) is not None
        for key in ["open_measurement", "short_measurement", "load_measurement"]
    )


def set_workspace_measurement(measurement: MeasurementData) -> None:
    st.session_state["measurement"] = measurement
    st.session_state["processed_measurement"] = None
    reset_permittivity_state()
    reset_inverse_state()
    reset_full_wave_state()


def capture_device_measurement(label: str, role: str) -> MeasurementData:
    device = st.session_state.get("device")
    if device is None:
        raise RuntimeError("No LiteVNA device is connected.")

    config = active_sweep_config()
    device.configure_sweep(config)
    measurement = device.capture_sweep()
    info = device.get_device_info()
    measurement.source_name = f"{label} - {info.name}"
    measurement.metadata.update(
        {
            "measurement_role": role,
            "device_name": info.name,
            "device_port": device.port,
            "workflow": "phase5",
        }
    )
    return measurement


def build_reference_overlay_plot(
    spectrum_result: PermittivityMeasurementResult,
    reference_material: dict[str, Any],
) -> go.Figure:
    frequency_ghz = spectrum_result.spectrum.frequency_hz / 1e9
    figure = go.Figure()
    figure.add_scatter(x=frequency_ghz, y=spectrum_result.spectrum.epsilon_prime, mode="lines", name="Measured epsilon'")
    figure.add_scatter(
        x=frequency_ghz,
        y=spectrum_result.spectrum.epsilon_double_prime,
        mode="lines",
        name="Measured epsilon''",
    )
    epsilon_real = float(reference_material.get("epsilon_real", 0.0) or 0.0)
    epsilon_imag = float(reference_material.get("epsilon_imag", 0.0) or 0.0)
    display_name = str(reference_material.get("display_name") or reference_material.get("material_name") or "Reference")
    figure.add_scatter(
        x=frequency_ghz,
        y=[epsilon_real] * len(frequency_ghz),
        mode="lines",
        name=f"{display_name} epsilon'",
        line=dict(dash="dash"),
    )
    figure.add_scatter(
        x=frequency_ghz,
        y=[epsilon_imag] * len(frequency_ghz),
        mode="lines",
        name=f"{display_name} epsilon''",
        line=dict(dash="dot"),
    )
    figure.update_layout(
        template="plotly_dark",
        title="Measured vs Reference Permittivity",
        xaxis_title="Frequency (GHz)",
        yaxis_title="Relative Permittivity",
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure


def render_workflow_header() -> None:
    calibration_state = "Ready" if calibration_measurements_ready() else "Pending"
    measurement_state = "Loaded" if st.session_state.get("measurement") is not None else "Waiting"
    result_state = "Available" if st.session_state.get("permittivity_result") else "Waiting"
    device = st.session_state.get("device")
    device_state = device.get_device_info().name if device is not None else "Not Connected"

    status_columns = st.columns(4)
    status_columns[0].metric("Device", device_state)
    status_columns[1].metric("Calibration", calibration_state)
    status_columns[2].metric("Measurement", measurement_state)
    status_columns[3].metric("Permittivity Result", result_state)


def render_home_page() -> None:
    st.markdown("## Open-Source Permittivity Measurement Platform")
    st.write(
        "LitePerm is designed to behave like a scientific instrument for complex permittivity measurement with LiteVNA hardware."
    )
    st.write("Connect LiteVNA -> Select Sensor -> Run Calibration -> Measure Material -> Calculate epsilon' and epsilon''")
    render_workflow_header()

    action_columns = st.columns([1, 1, 2])
    with action_columns[0]:
        if st.button("Start Measurement", key="home_start_measurement"):
            st.session_state["workflow_page"] = "Connect LiteVNA"
            st.rerun()
    with action_columns[1]:
        if st.button("Open Results", key="home_open_results"):
            st.session_state["workflow_page"] = "Permittivity Results"
            st.rerun()

    st.markdown("### Instrument Workflow")
    workflow_columns = st.columns(len(WORKFLOW_PAGES) - 1)
    for index, page_name in enumerate(WORKFLOW_PAGES[1:]):
        with workflow_columns[index]:
            st.caption(f"{index + 1}. {page_name}")

    st.markdown("### User Modes")
    basic_column, advanced_column = st.columns(2)
    with basic_column:
        st.markdown("#### Basic Mode")
        st.write("For researchers, students, technicians, and industrial users who only need calibrated permittivity results.")
        st.write("Shows frequency, epsilon', epsilon'', loss tangent, conductivity, confidence, and material comparison.")
    with advanced_column:
        st.markdown("#### Advanced Mode")
        st.write("For RF engineers and developers who want S11, phase, Smith charts, inverse modelling, and full-wave solver tools.")
        st.write("All existing RF and modelling features remain available under Advanced Tools.")


def render_connect_litevna_page() -> None:
    st.subheader("Connect LiteVNA")
    st.write("LiteVNA is the primary device backend for LitePerm. Connect it here, confirm communication, and define the sweep used throughout the measurement workflow.")

    device_candidates = discover_device_candidates()
    detected_ports = [candidate.port for candidate in device_candidates if candidate.port]
    current_kind = st.session_state.get("device_kind", "litevna")
    backend_options = ["litevna", "future_device"]
    selected_kind = st.selectbox(
        "Device backend",
        options=backend_options,
        index=backend_options.index(current_kind) if current_kind in backend_options else 0,
        format_func=lambda item: "LiteVNA USB Serial" if item == "litevna" else "Simulated Future Device",
        key="connect_device_kind",
    )
    default_port = "SIMULATED" if selected_kind == "future_device" else (st.session_state.get("device_port") or (detected_ports[0] if detected_ports else ""))
    selected_port = st.selectbox(
        "Detected device port",
        options=detected_ports or [default_port or ""],
        key="connect_detected_port",
    )
    manual_port = st.text_input(
        "Manual COM port override",
        value=st.session_state["device_port"] if selected_kind == "litevna" else "SIMULATED",
        key="connect_manual_port",
    )
    port_to_use = manual_port.strip() or selected_port

    control_columns = st.columns(4)
    with control_columns[0]:
        if st.button("Detect Device", key="connect_detect_device"):
            st.rerun()
    with control_columns[1]:
        if st.button("Connect", key="connect_device_button"):
            try:
                message = connect_selected_device(selected_kind, port_to_use)
                st.success(message)
            except Exception as error:
                st.error(f"Connection failed: {error}")
    with control_columns[2]:
        if st.button("Test Connection", key="connect_test_device"):
            device = st.session_state.get("device")
            if device is None:
                st.info("Connect a LiteVNA first.")
            else:
                st.success("Device responded correctly.") if device.test_connection() else st.error("Device did not respond.")
    with control_columns[3]:
        if st.button("Disconnect", key="connect_disconnect_device"):
            disconnect_device()
            st.info("Device disconnected.")

    device = st.session_state.get("device")
    if device is None:
        st.error("Device Status: Not Connected")
    else:
        st.success("Device Status: Connected")
        st.json(device.get_device_info().to_dict())

    st.markdown("### Sweep Configuration")
    sweep_columns = st.columns(5)
    with sweep_columns[0]:
        st.session_state["measurement_start_frequency_hz"] = float(
            st.number_input(
                "Start Frequency (Hz)",
                value=float(st.session_state["measurement_start_frequency_hz"]),
                step=1e6,
                format="%.0f",
                key="connect_start_frequency_hz",
            )
        )
    with sweep_columns[1]:
        st.session_state["measurement_stop_frequency_hz"] = float(
            st.number_input(
                "Stop Frequency (Hz)",
                value=float(st.session_state["measurement_stop_frequency_hz"]),
                step=1e6,
                format="%.0f",
                key="connect_stop_frequency_hz",
            )
        )
    with sweep_columns[2]:
        st.session_state["measurement_points"] = int(
            st.number_input(
                "Number of Points",
                value=int(st.session_state["measurement_points"]),
                step=10,
                key="connect_measurement_points",
            )
        )
    with sweep_columns[3]:
        st.session_state["measurement_output_power"] = int(
            st.slider(
                "Output Power",
                min_value=1,
                max_value=3,
                value=int(st.session_state["measurement_output_power"]),
                key="connect_output_power",
            )
        )
    with sweep_columns[4]:
        st.session_state["measurement_sweep_speed"] = st.selectbox(
            "Sweep Speed",
            ["slow", "normal", "fast", "demo"],
            index=["slow", "normal", "fast", "demo"].index(st.session_state["measurement_sweep_speed"]),
            key="connect_sweep_speed",
        )

    active_config = active_sweep_config()
    st.caption(
        f"Configured sweep: {active_config.start_frequency_hz / 1e9:.3f} to {active_config.stop_frequency_hz / 1e9:.3f} GHz, "
        f"{active_config.points} points, power level {active_config.output_power}, speed `{active_config.sweep_speed}`."
    )


def render_calibration_measurement_section(
    label: str,
    session_key: str,
    uploader_key: str,
    *,
    role: str,
) -> None:
    st.markdown(f"### {label}")
    measurement = st.session_state.get(session_key)
    control_columns = st.columns([2, 1, 1])
    with control_columns[0]:
        uploaded_file = st.file_uploader(
            f"Import {label} measurement",
            type=["s1p", "csv"],
            key=uploader_key,
        )
        if uploaded_file is not None:
            try:
                st.session_state[session_key] = parse_uploaded_measurement(uploaded_file)
                measurement = st.session_state[session_key]
                st.success(f"{label} loaded from file.")
            except Exception as error:
                st.error(f"Failed to import {label}: {error}")
    with control_columns[1]:
        if st.button(f"Capture {label}", key=f"capture_{session_key}"):
            try:
                st.session_state[session_key] = capture_device_measurement(label, role)
                measurement = st.session_state[session_key]
                st.success(f"{label} captured from the connected device.")
            except Exception as error:
                st.error(f"{label} capture failed: {error}")
    with control_columns[2]:
        if st.button(f"Clear {label}", key=f"clear_{session_key}"):
            st.session_state[session_key] = None
            measurement = None
            st.info(f"{label} cleared.")

    if measurement is not None:
        st.caption(f"Loaded source: `{measurement.source_name or label}`")
        render_measurement_summary(measurement)


def render_calibration_wizard_page(reference_names: list[str]) -> None:
    st.subheader("Calibration Wizard")
    st.write("Run the guided open-short-load workflow, capture reference materials, and save the calibration profile that will be used during permittivity measurement.")

    steps = [
        ("Open", "open_measurement"),
        ("Short", "short_measurement"),
        ("Load", "load_measurement"),
        ("Reference Material 1", "reference_measurement_1"),
        ("Reference Material 2", "reference_measurement_2"),
        ("Save Calibration", "save"),
    ]
    completed_steps = sum(1 for _, key in steps[:-1] if st.session_state.get(key) is not None)
    st.progress(completed_steps / (len(steps) - 1))
    step_columns = st.columns(len(steps))
    for index, (label, key) in enumerate(steps):
        status = "Complete" if (key == "save" and calibration_measurements_ready()) or (key != "save" and st.session_state.get(key) is not None) else "Pending"
        step_columns[index].metric(label, status)

    profile_columns = st.columns(3)
    with profile_columns[0]:
        calibration_name = st.text_input(
            "Calibration profile name",
            value=st.session_state["calibration_profile"].name,
            key="wizard_calibration_name",
        )
    reference_options = ["None"] + reference_names
    with profile_columns[1]:
        reference_1 = st.selectbox(
            "Reference Material 1",
            options=reference_options,
            index=reference_options.index(st.session_state["reference_material_1"]) if st.session_state["reference_material_1"] in reference_options else 0,
            key="wizard_reference_material_1",
        )
    with profile_columns[2]:
        reference_2 = st.selectbox(
            "Reference Material 2",
            options=reference_options,
            index=reference_options.index(st.session_state["reference_material_2"]) if st.session_state["reference_material_2"] in reference_options else 0,
            key="wizard_reference_material_2",
        )
    notes = st.text_area(
        "Calibration notes",
        value=st.session_state["calibration_profile"].notes,
        key="wizard_calibration_notes",
    )

    render_calibration_measurement_section("Open", "open_measurement", "wizard_open_upload", role="open")
    render_calibration_measurement_section("Short", "short_measurement", "wizard_short_upload", role="short")
    render_calibration_measurement_section("Load", "load_measurement", "wizard_load_upload", role="load")
    render_calibration_measurement_section("Reference Material 1", "reference_measurement_1", "wizard_reference_1_upload", role="reference_1")
    render_calibration_measurement_section("Reference Material 2", "reference_measurement_2", "wizard_reference_2_upload", role="reference_2")

    open_measurement = st.session_state.get("open_measurement")
    short_measurement = st.session_state.get("short_measurement")
    load_measurement = st.session_state.get("load_measurement")
    metadata: dict[str, str] = {}
    if open_measurement is not None:
        metadata["open_source"] = open_measurement.source_name
    if short_measurement is not None:
        metadata["short_source"] = short_measurement.source_name
    if load_measurement is not None:
        metadata["load_source"] = load_measurement.source_name
    if st.session_state.get("reference_measurement_1") is not None:
        metadata["reference_1_source"] = st.session_state["reference_measurement_1"].source_name
    if st.session_state.get("reference_measurement_2") is not None:
        metadata["reference_2_source"] = st.session_state["reference_measurement_2"].source_name

    st.session_state["calibration_profile"] = build_calibration_profile(
        calibration_name,
        reference_materials=[name for name in [reference_1, reference_2] if name != "None"],
        notes=notes,
        metadata=metadata,
    )

    action_columns = st.columns(3)
    with action_columns[0]:
        if st.button("Save Calibration", key="wizard_save_calibration"):
            if not calibration_measurements_ready():
                st.error("Capture or import the Open, Short, and Load standards before saving the calibration.")
            else:
                saved_path = save_calibration_profile_to_library(st.session_state["calibration_profile"])
                st.success(f"Calibration saved to `{saved_path}`")
    with action_columns[1]:
        st.download_button(
            "Download Calibration YAML",
            data=calibration_profile_to_yaml(st.session_state["calibration_profile"]),
            file_name="calibration_profile.yaml",
            mime="application/x-yaml",
            key="wizard_download_calibration_yaml",
        )
    with action_columns[2]:
        if st.button("Continue to Sensor Setup", key="wizard_continue_sensor_setup"):
            st.session_state["workflow_page"] = "Sensor Setup"
            st.rerun()

    st.code(calibration_profile_to_yaml(st.session_state["calibration_profile"]), language="yaml")


def render_sensor_setup_page() -> None:
    st.subheader("Sensor Setup")
    st.write("Select the probe or sensor used for permittivity measurement, then adjust the geometry profile used by the transformation and modelling engines.")

    sensor_labels = list(DISPLAY_TO_SENSOR)
    current_sensor = st.session_state["geometry_profile"].sensor_type
    current_label = workflow_sensor_label(current_sensor)
    selected_label = st.radio(
        "Sensor family",
        sensor_labels,
        index=sensor_labels.index(current_label) if current_label in sensor_labels else 0,
        horizontal=True,
        key="sensor_setup_sensor_label",
    )
    selected_sensor_type = DISPLAY_TO_SENSOR[selected_label]
    if st.session_state["geometry_profile"].sensor_type != selected_sensor_type:
        st.session_state["geometry_profile"] = build_geometry_profile(
            selected_sensor_type,
            name=selected_label,
        )
        st.session_state["inverse_layer_stack"] = default_layer_stack(selected_sensor_type)
        st.session_state["full_wave_layer_stack"] = default_layer_stack(selected_sensor_type)
        reset_full_wave_state(preserve_layer_stack=True)
        reset_inverse_state(preserve_layer_stack=True)

    saved_geometries = list_saved_geometry_profiles()
    load_columns = st.columns(2)
    with load_columns[0]:
        selected_saved_geometry = st.selectbox(
            "Load saved sensor profile",
            options=["None"] + [entry["path"] for entry in saved_geometries],
            format_func=lambda item: "None" if item == "None" else Path(item).stem,
            key="sensor_setup_saved_geometry",
        )
    with load_columns[1]:
        if st.button("Load Sensor Profile", key="sensor_setup_load_button") and selected_saved_geometry != "None":
            st.session_state["geometry_profile"] = load_geometry_profile(selected_saved_geometry)
            st.success("Sensor profile loaded from library.")

    updated_geometry = geometry_editor(st.session_state["geometry_profile"])
    st.session_state["geometry_profile"] = updated_geometry

    method_options = list(get_runnable_plugins())
    if st.session_state["selected_permittivity_method"] not in method_options and method_options:
        st.session_state["selected_permittivity_method"] = method_options[0]
    if method_options:
        st.session_state["selected_permittivity_method"] = st.selectbox(
            "Permittivity transformation model",
            options=method_options,
            index=method_options.index(st.session_state["selected_permittivity_method"]),
            format_func=lambda item: get_runnable_plugins()[item].metadata().get("display_name", item.title()),
            key="sensor_setup_permittivity_method",
        )

    sensor_model = build_sensor_model(
        updated_geometry,
        calibration=st.session_state["calibration_profile"],
        frequency_range_hz=(
            float(st.session_state["measurement_start_frequency_hz"]),
            float(st.session_state["measurement_stop_frequency_hz"]),
        ),
    )

    st.markdown("### Sensor Summary")
    st.json(sensor_model.summary())

    geometry_actions = st.columns(3)
    with geometry_actions[0]:
        if st.button("Save Sensor Profile", key="sensor_setup_save_geometry"):
            saved_path = save_geometry_profile_to_library(updated_geometry)
            st.success(f"Saved to `{saved_path}`")
    with geometry_actions[1]:
        st.download_button(
            "Download Sensor YAML",
            data=geometry_profile_to_yaml(updated_geometry),
            file_name="geometry_profile.yaml",
            mime="application/x-yaml",
            key="sensor_setup_download_geometry",
        )
    with geometry_actions[2]:
        if st.button("Continue to Measure Material", key="sensor_setup_continue_measurement"):
            st.session_state["workflow_page"] = "Measure Material"
            st.rerun()


def render_measure_material_page(
    material_db: MaterialDatabase,
    runnable_plugins: dict[str, Any],
) -> None:
    st.subheader("Measure Material")
    st.write("Capture a sweep from LiteVNA or import a saved file, then let LitePerm calculate complex permittivity as the primary result.")

    measurement_columns = st.columns([2, 1, 1])
    with measurement_columns[0]:
        uploaded_file = st.file_uploader("Import Touchstone or CSV", type=["s1p", "csv"], key="measure_material_upload")
        if uploaded_file is not None:
            try:
                set_workspace_measurement(parse_uploaded_measurement(uploaded_file))
                st.success("Measurement imported.")
            except Exception as error:
                st.error(f"Failed to import measurement: {error}")
    with measurement_columns[1]:
        example_name = st.selectbox(
            "Example dataset",
            options=["None", "sample_touchstone.s1p", "sample_litevna.csv"],
            key="measure_material_example_name",
        )
        if st.button("Load Example", key="measure_material_load_example"):
            load_example_dataset(example_name)
    with measurement_columns[2]:
        if st.button("Capture From LiteVNA", key="measure_material_capture_device"):
            try:
                measurement = capture_device_measurement("Material Under Test", "dut")
                set_workspace_measurement(measurement)
                st.success("Measurement captured from LiteVNA.")
            except Exception as error:
                st.error(f"Capture failed: {error}")

    measurement = st.session_state.get("measurement")
    if measurement is None:
        st.info("No material measurement is loaded yet.")
    else:
        render_measurement_summary(measurement)
        st.caption(f"Measurement source: `{measurement.source_name}`")
        if st.session_state["user_mode"] == "Advanced":
            preview_columns = st.columns(2)
            with preview_columns[0]:
                st.plotly_chart(build_magnitude_plot(measurement), use_container_width=True, key="measure_material_raw_magnitude")
            with preview_columns[1]:
                st.plotly_chart(build_phase_plot(measurement), use_container_width=True, key="measure_material_raw_phase")

    material_under_test = st.text_input("Material under test", value="Unknown material", key="measure_material_name")
    selected_method = st.session_state["selected_permittivity_method"]
    if selected_method not in runnable_plugins and runnable_plugins:
        selected_method = list(runnable_plugins)[0]
        st.session_state["selected_permittivity_method"] = selected_method

    st.caption(
        f"Active method: `{selected_method}` using `{workflow_sensor_label(st.session_state['geometry_profile'].sensor_type)}` "
        f"with calibration profile `{st.session_state['calibration_profile'].name}`."
    )

    if st.button("Calculate Permittivity", key="measure_material_calculate"):
        if measurement is None:
            st.error("Import or capture a material measurement before calculating permittivity.")
        else:
            try:
                reference_payloads = reference_material_payloads(material_db)
                calibration_profile = st.session_state["calibration_profile"] if calibration_measurements_ready() else None
                result = run_permittivity_measurement(
                    measurement,
                    st.session_state["geometry_profile"],
                    method=selected_method,
                    calibration_profile=calibration_profile,
                    open_measurement=st.session_state.get("open_measurement"),
                    short_measurement=st.session_state.get("short_measurement"),
                    load_measurement=st.session_state.get("load_measurement"),
                    reference_materials=reference_payloads,
                )
                result.metadata["material_under_test"] = material_under_test
                st.session_state["permittivity_result"] = result.to_dict()
                st.session_state["processed_measurement"] = result.processed_measurement
                st.session_state["last_spectrum"] = result.spectrum
                st.session_state["last_validation_result"] = result.validation.to_dict()
                st.session_state["last_reference_comparisons"] = result.reference_comparisons
                st.session_state["last_material_matches"] = result.identified_materials
                if result.identified_materials:
                    top_name = result.identified_materials[0].get("display_name") or result.identified_materials[0].get("material_name")
                    st.session_state["selected_reference_material"] = str(top_name)
                st.session_state["workflow_page"] = "Permittivity Results"
                st.success("Permittivity calculation complete.")
                st.rerun()
            except Exception as error:
                st.error(f"Permittivity calculation failed: {error}")


def restore_experiment_result(record, material_db: MaterialDatabase) -> None:
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
    st.session_state["full_wave_layer_stack"] = default_layer_stack(record.geometry_profile.sensor_type)

    reference_payloads = reference_material_payloads(material_db)
    validation = validate_permittivity_measurement(
        record.spectrum,
        record.processed_measurement,
        calibration_profile=record.calibration_profile,
        reference_materials=reference_payloads,
    )
    comparisons = compare_to_reference_materials(record.spectrum, reference_payloads)
    matches = identify_closest_materials(record.spectrum, reference_payloads)
    result = PermittivityMeasurementResult(
        spectrum=record.spectrum,
        processed_measurement=record.processed_measurement,
        validation=validation,
        reference_comparisons=comparisons,
        identified_materials=matches,
        confidence_estimate=validation.confidence_label,
        metadata={"material_under_test": record.metadata.material_under_test, "method": "restored_experiment"},
    )
    st.session_state["permittivity_result"] = result.to_dict()
    st.session_state["last_validation_result"] = validation.to_dict()
    st.session_state["last_reference_comparisons"] = comparisons
    st.session_state["last_material_matches"] = matches


def render_permittivity_results_page(material_db: MaterialDatabase) -> None:
    st.subheader("Permittivity Results")
    result = current_permittivity_result()
    if result is None:
        st.info("Run a material measurement first to see epsilon', epsilon'', conductivity, loss tangent, and the validation summary.")
        return

    spectrum = result.spectrum
    metrics = st.columns(5)
    metrics[0].metric("Mean epsilon'", f"{spectrum.epsilon_prime.mean():.3f}")
    metrics[1].metric("Mean epsilon''", f"{spectrum.epsilon_double_prime.mean():.3f}")
    metrics[2].metric("Peak Loss Tangent", f"{spectrum.loss_tangent.max():.3f}")
    metrics[3].metric("Peak Conductivity", f"{spectrum.conductivity_s_per_m.max():.3f} S/m")
    metrics[4].metric("Confidence", f"{result.validation.confidence_label} ({result.validation.confidence_score:.0f}/120)")

    st.plotly_chart(build_epsilon_plot(spectrum), use_container_width=True, key="phase5_results_epsilon")
    result_columns = st.columns(2)
    with result_columns[0]:
        st.plotly_chart(build_loss_tangent_plot(spectrum), use_container_width=True, key="phase5_results_loss_tangent")
    with result_columns[1]:
        st.plotly_chart(build_nyquist_plot(spectrum), use_container_width=True, key="phase5_results_nyquist")

    st.markdown("### Measurement Validation")
    st.write(result.validation.summary)
    st.dataframe(result.validation.to_dataframe(), use_container_width=True)

    st.markdown("### Material Comparison")
    materials = reference_material_payloads(material_db)
    material_names = [str(item.get("display_name") or item.get("material_name")) for item in materials]
    selected_reference = st.selectbox(
        "Compare against reference material",
        options=material_names,
        index=material_names.index(st.session_state["selected_reference_material"]) if st.session_state.get("selected_reference_material") in material_names else 0,
        key="results_reference_material_select",
    )
    st.session_state["selected_reference_material"] = selected_reference
    selected_payload = next(
        (
            item
            for item in materials
            if str(item.get("display_name") or item.get("material_name")) == selected_reference
        ),
        materials[0],
    )
    comparison_plot = build_reference_overlay_plot(result, selected_payload)
    st.plotly_chart(comparison_plot, use_container_width=True, key="phase5_results_reference_overlay")

    comparison_frame = comparisons_to_frame(result.reference_comparisons)
    if not comparison_frame.empty:
        filtered = comparison_frame[comparison_frame["display_name"] == selected_reference]
        if not filtered.empty:
            top_row = filtered.iloc[0].to_dict()
            comparison_metrics = st.columns(4)
            comparison_metrics[0].metric("Similarity Score", f"{float(top_row['similarity_score']):.1f}")
            comparison_metrics[1].metric("Delta epsilon'", f"{float(top_row['delta_epsilon_real']):.3f}")
            comparison_metrics[2].metric("Delta epsilon''", f"{float(top_row['delta_epsilon_imag']):.3f}")
            comparison_metrics[3].metric("Delta Conductivity", f"{float(top_row['delta_conductivity_s_per_m']):.4f} S/m")
        st.dataframe(comparison_frame, use_container_width=True)

    st.markdown("### Closest Material Matches")
    match_frame = pd.DataFrame(result.identified_materials)
    if not match_frame.empty:
        st.dataframe(match_frame, use_container_width=True)

    st.download_button(
        "Download Permittivity CSV",
        data=spectrum_to_csv_bytes(spectrum),
        file_name="liteperm_permittivity_results.csv",
        mime="text/csv",
        key="phase5_results_download_csv",
    )
    render_figure_export(comparison_plot, "permittivity_reference_comparison")

    if st.session_state["user_mode"] == "Advanced":
        advanced_columns = st.columns(2)
        with advanced_columns[0]:
            st.plotly_chart(build_impedance_plot(spectrum), use_container_width=True, key="phase5_results_impedance")
        with advanced_columns[1]:
            st.plotly_chart(build_admittance_plot(spectrum), use_container_width=True, key="phase5_results_admittance")


def render_research_mode_page(experiment_db: ExperimentDatabase, material_db: MaterialDatabase) -> None:
    st.subheader("Research Mode")
    measurement = st.session_state.get("measurement")
    result = current_permittivity_result()
    default_experiment_name = measurement.source_name if measurement is not None and measurement.source_name else "LitePerm Experiment"
    metadata = build_research_metadata(default_experiment_name)

    if measurement is None or result is None:
        st.info("Load a material measurement and calculate permittivity before saving a research experiment.")
    else:
        if st.button("Save Experiment", key="phase5_save_experiment"):
            try:
                record = experiment_db.save_experiment(
                    metadata=metadata,
                    raw_measurement=measurement,
                    processed_measurement=result.processed_measurement,
                    spectrum=result.spectrum,
                    calibration_profile=st.session_state["calibration_profile"],
                    geometry_profile=st.session_state["geometry_profile"],
                    inverse_result=st.session_state.get("inverse_result"),
                    digital_twin=st.session_state.get("inverse_digital_twin"),
                )
                st.session_state["last_saved_experiment_id"] = record.experiment_id
                st.success(f"Experiment saved as `{record.experiment_id}`")
            except Exception as error:
                st.error(f"Experiment save failed: {error}")

    st.markdown("### Experiment Explorer")
    search_columns = st.columns(4)
    with search_columns[0]:
        search_text = st.text_input("Search", value="", key="phase5_explorer_search")
    with search_columns[1]:
        sensor_filter = st.text_input("Filter by sensor type", value="", key="phase5_explorer_sensor")
    with search_columns[2]:
        project_filter = st.text_input("Filter by project", value="", key="phase5_explorer_project")
    with search_columns[3]:
        sort_by = st.selectbox("Sort by", ["created_at", "experiment_name", "project_name", "researcher"], key="phase5_explorer_sort")

    experiment_rows = experiment_db.list_experiments(search=search_text, sensor_type=sensor_filter, project_name=project_filter, sort_by=sort_by)
    if not experiment_rows:
        st.caption("No experiments saved yet.")
        return

    explorer_frame = pd.DataFrame(experiment_rows)
    st.dataframe(explorer_frame, use_container_width=True)
    selected_experiment_id = st.selectbox(
        "Selected experiment",
        options=explorer_frame["experiment_id"].tolist(),
        key="phase5_selected_experiment",
    )
    explorer_actions = st.columns(4)
    with explorer_actions[0]:
        if st.button("Open Selected Experiment", key="phase5_open_experiment"):
            record = experiment_db.get_experiment(selected_experiment_id)
            restore_experiment_result(record, material_db)
            st.session_state["workflow_page"] = "Permittivity Results"
            st.success(f"Loaded `{record.experiment_id}` into the measurement workspace.")
            st.rerun()
    with explorer_actions[1]:
        if st.button("Duplicate Experiment", key="phase5_duplicate_experiment"):
            duplicated = experiment_db.duplicate_experiment(selected_experiment_id)
            st.success(f"Duplicated as `{duplicated.experiment_id}`")
    with explorer_actions[2]:
        archive_bytes = experiment_db.export_experiment(selected_experiment_id)
        st.download_button(
            "Export Experiment",
            data=archive_bytes,
            file_name=f"{selected_experiment_id}.zip",
            mime="application/zip",
            key="phase5_export_experiment",
        )
    with explorer_actions[3]:
        if st.button("Delete Experiment", key="phase5_delete_experiment"):
            experiment_db.delete_experiment(selected_experiment_id)
            st.success(f"Deleted `{selected_experiment_id}`")
            st.rerun()


def render_advanced_rf_response_page() -> None:
    st.markdown("### RF Response and Network View")
    measurement = st.session_state.get("measurement")
    spectrum = st.session_state.get("last_spectrum")
    if measurement is None:
        st.info("Capture or import a measurement first.")
        return

    render_measurement_summary(measurement)
    figure_columns = st.columns(2)
    with figure_columns[0]:
        st.plotly_chart(build_magnitude_plot(measurement), use_container_width=True, key="advanced_rf_magnitude")
        st.plotly_chart(build_phase_plot(measurement), use_container_width=True, key="advanced_rf_phase")
    with figure_columns[1]:
        smith_chart = build_smith_chart(measurement)
        st.plotly_chart(smith_chart, use_container_width=True, key="advanced_rf_smith")
        render_figure_export(smith_chart, "advanced_rf_smith")

    if spectrum is not None:
        extra_columns = st.columns(2)
        with extra_columns[0]:
            st.plotly_chart(build_impedance_plot(spectrum), use_container_width=True, key="advanced_rf_impedance")
            st.plotly_chart(build_admittance_plot(spectrum), use_container_width=True, key="advanced_rf_admittance")
        with extra_columns[1]:
            st.plotly_chart(build_epsilon_plot(spectrum), use_container_width=True, key="advanced_rf_epsilon")
            st.plotly_chart(build_loss_tangent_plot(spectrum), use_container_width=True, key="advanced_rf_loss")


def render_advanced_live_capture_page(selected_plugin: str) -> None:
    st.markdown("### Live Capture")
    st.caption("Use this page for repeated live sweeps, RF preview, and fast transfer into the measurement workspace.")
    render_connect_litevna_page()

    live_controls = st.columns(3)
    with live_controls[0]:
        if st.button("Start Sweep", key="advanced_live_start"):
            st.session_state["live_running"] = True
    with live_controls[1]:
        if st.button("Stop Sweep", key="advanced_live_stop"):
            st.session_state["live_running"] = False
    with live_controls[2]:
        if st.button("Save Sweep", key="advanced_live_save") and st.session_state.get("live_last_result") is not None:
            set_workspace_measurement(st.session_state["live_last_result"].raw_measurement)
            st.session_state["processed_measurement"] = st.session_state["live_last_result"].processed_measurement
            st.session_state["last_spectrum"] = st.session_state["live_last_result"].spectrum
            st.success("Live sweep copied into the current analysis workspace.")

    device = st.session_state.get("device")
    live_placeholder = st.empty()
    if st.session_state.get("live_running"):
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
                        config=active_sweep_config(),
                        geometry=st.session_state["geometry_profile"],
                        plugin_name=selected_plugin,
                        calibration_profile=st.session_state["calibration_profile"],
                        open_measurement=st.session_state.get("open_measurement"),
                        short_measurement=st.session_state.get("short_measurement"),
                        load_measurement=st.session_state.get("load_measurement"),
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


def render_advanced_profiles_page(reference_names: list[str]) -> None:
    st.markdown("### Calibration and Sensor Profiles")
    profile_tabs = st.tabs(["Calibration Profiles", "Sensor Profiles"])

    with profile_tabs[0]:
        saved_profiles = list_saved_calibration_profiles()
        selected_saved_profile = st.selectbox(
            "Load saved calibration profile",
            options=["None"] + [entry["path"] for entry in saved_profiles],
            format_func=lambda item: "None" if item == "None" else Path(item).stem,
            key="advanced_saved_calibration_profile",
        )
        if st.button("Load Selected Calibration Profile", key="advanced_load_calibration") and selected_saved_profile != "None":
            st.session_state["calibration_profile"] = load_calibration_profile(selected_saved_profile)
            st.success("Calibration profile loaded from library.")

        updated_profile = calibration_editor(reference_names, st.session_state["calibration_profile"])
        st.session_state["calibration_profile"] = updated_profile
        calibration_actions = st.columns(2)
        with calibration_actions[0]:
            if st.button("Save Calibration Profile", key="advanced_save_calibration"):
                saved_path = save_calibration_profile_to_library(updated_profile)
                st.success(f"Saved to `{saved_path}`")
        with calibration_actions[1]:
            st.download_button(
                "Download Calibration YAML",
                data=calibration_profile_to_yaml(updated_profile),
                file_name="calibration_profile.yaml",
                mime="application/x-yaml",
                key="advanced_download_calibration_yaml",
            )

    with profile_tabs[1]:
        saved_geometries = list_saved_geometry_profiles()
        selected_saved_geometry = st.selectbox(
            "Load saved geometry profile",
            options=["None"] + [entry["path"] for entry in saved_geometries],
            format_func=lambda item: "None" if item == "None" else Path(item).stem,
            key="advanced_saved_geometry_profile",
        )
        if st.button("Load Selected Geometry Profile", key="advanced_load_geometry") and selected_saved_geometry != "None":
            st.session_state["geometry_profile"] = load_geometry_profile(selected_saved_geometry)
            st.success("Geometry profile loaded from library.")

        updated_geometry = geometry_editor(st.session_state["geometry_profile"])
        st.session_state["geometry_profile"] = updated_geometry
        geometry_actions = st.columns(2)
        with geometry_actions[0]:
            if st.button("Save Geometry Profile", key="advanced_save_geometry"):
                saved_path = save_geometry_profile_to_library(updated_geometry)
                st.success(f"Saved to `{saved_path}`")
        with geometry_actions[1]:
            st.download_button(
                "Download Geometry YAML",
                data=geometry_profile_to_yaml(updated_geometry),
                file_name="geometry_profile.yaml",
                mime="application/x-yaml",
                key="advanced_download_geometry_yaml",
            )


def render_material_database_manager(material_db: MaterialDatabase, *, key_prefix: str) -> None:
    search = st.text_input("Search materials", value="", key=f"{key_prefix}_materials_search")
    materials_frame = pd.DataFrame(material_db.list_materials(search=search))
    if not materials_frame.empty:
        st.dataframe(materials_frame, use_container_width=True)

    st.markdown("#### Add Material")
    add_columns = st.columns(2)
    with add_columns[0]:
        material_name = st.text_input("Material Name", value="Custom Material", key=f"{key_prefix}_material_name")
        category = st.text_input("Category", value="user", key=f"{key_prefix}_material_category")
        epsilon_real = st.number_input("epsilon' reference", value=2.5, step=0.1, key=f"{key_prefix}_material_epsilon_real")
        epsilon_imag = st.number_input("epsilon'' reference", value=0.05, step=0.01, key=f"{key_prefix}_material_epsilon_imag")
        conductivity = st.number_input(
            "Conductivity (S/m)",
            value=0.001,
            step=0.001,
            format="%.6f",
            key=f"{key_prefix}_material_conductivity",
        )
    with add_columns[1]:
        loss_tangent = st.number_input("Loss tangent", value=0.02, step=0.01, key=f"{key_prefix}_material_loss_tangent")
        source = st.text_input("Source", value="User entry", key=f"{key_prefix}_material_source")
        references = st.text_input("References", value="", key=f"{key_prefix}_material_references")
        notes = st.text_area("Notes", value="", key=f"{key_prefix}_material_notes")

    if st.button("Add Material to Database", key=f"{key_prefix}_add_material"):
        material_db.add_material(
            {
                "material_name": material_name,
                "display_name": material_name,
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


def render_advanced_models_page(
    plugins: dict[str, Any],
    runnable_plugins: dict[str, Any],
    experiment_db: ExperimentDatabase,
) -> None:
    st.markdown("### Modelling Registry")
    plugin_cards = st.columns(max(1, min(3, len(plugins))))
    for index, (plugin_name, plugin) in enumerate(plugins.items()):
        with plugin_cards[index % len(plugin_cards)]:
            metadata = plugin.metadata()
            st.markdown(f"#### {metadata.get('display_name', plugin_name.title())}")
            st.caption(metadata.get("validation_status", "unknown").title())
            st.write(plugin.description())

    measurement = st.session_state.get("measurement")
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

    experiment_rows = experiment_db.list_experiments()
    if experiment_rows:
        records = [experiment_db.get_experiment(row["experiment_id"]) for row in experiment_rows[:10]]
        with st.expander("AI dataset preview"):
            st.dataframe(build_experiment_dataset(records), use_container_width=True)


def render_advanced_tools_page(
    *,
    selected_plugin: str,
    reference_names: list[str],
    forward_models: dict[str, type],
    inverse_solvers: dict[str, type],
    plugins: dict[str, Any],
    runnable_plugins: dict[str, Any],
    experiment_db: ExperimentDatabase,
    material_db: MaterialDatabase,
) -> None:
    st.subheader("Advanced Tools")
    if st.session_state["user_mode"] != "Advanced":
        st.info("Switch to Advanced Mode in the sidebar to access RF views, live capture, inverse modelling, and full-wave simulation.")
        return

    advanced_tabs = st.tabs(
        [
            "RF Response",
            "Live Capture",
            "Profiles",
            "Plugin Models",
            "Full-Wave",
            "Inverse",
            "Materials",
        ]
    )
    with advanced_tabs[0]:
        render_advanced_rf_response_page()
    with advanced_tabs[1]:
        render_advanced_live_capture_page(selected_plugin)
    with advanced_tabs[2]:
        render_advanced_profiles_page(reference_names)
    with advanced_tabs[3]:
        render_advanced_models_page(plugins, runnable_plugins, experiment_db)
    with advanced_tabs[4]:
        render_full_wave_simulation_tab()
    with advanced_tabs[5]:
        render_inverse_modelling_tab(forward_models=forward_models, inverse_solvers=inverse_solvers)
    with advanced_tabs[6]:
        render_material_database_manager(material_db, key_prefix="advanced")


def main() -> None:
    st.set_page_config(page_title="LitePerm", layout="wide")
    initialise_state()

    experiment_db = get_experiment_database()
    material_db = get_material_database()
    plugins = discover_plugins()
    runnable_plugins = get_runnable_plugins()
    forward_models = discover_forward_models(include_full_wave=True)
    inverse_solvers = discover_inverse_solvers()
    reference_names = list_reference_material_names()

    st.title("LitePerm")
    st.caption("Open-source permittivity measurement platform for LiteVNA-based dielectric spectroscopy and material characterisation")

    if not runnable_plugins:
        st.error("No permittivity transformation plugins are available.")
        return

    selected_plugin = st.session_state["selected_permittivity_method"]
    if selected_plugin not in runnable_plugins:
        selected_plugin = "stuchly" if "stuchly" in runnable_plugins else list(runnable_plugins)[0]
        st.session_state["selected_permittivity_method"] = selected_plugin

    apply_documentation_demo_state(selected_plugin)

    with st.sidebar:
        st.header("LitePerm Workflow")
        st.session_state["user_mode"] = st.radio(
            "User Mode",
            ["Basic", "Advanced"],
            index=0 if st.session_state["user_mode"] == "Basic" else 1,
            key="sidebar_user_mode",
        )
        st.session_state["workflow_page"] = st.radio(
            "Navigation",
            WORKFLOW_PAGES,
            index=WORKFLOW_PAGES.index(st.session_state["workflow_page"]) if st.session_state["workflow_page"] in WORKFLOW_PAGES else 0,
            key="sidebar_workflow_page",
        )
        st.session_state["selected_permittivity_method"] = st.selectbox(
            "Permittivity model",
            options=list(runnable_plugins),
            index=list(runnable_plugins).index(selected_plugin),
            format_func=lambda item: runnable_plugins[item].metadata().get("display_name", item.title()),
            key="sidebar_permittivity_method",
        )
        device = st.session_state.get("device")
        st.markdown("### Instrument Status")
        st.write(f"Device: `{device.get_device_info().name if device is not None else 'Not Connected'}`")
        st.write(f"Sensor: `{workflow_sensor_label(st.session_state['geometry_profile'].sensor_type)}`")
        st.write(f"Calibration: `{'Ready' if calibration_measurements_ready() else 'Pending'}`")
        st.write(f"Result: `{'Available' if st.session_state.get('permittivity_result') else 'Waiting'}`")
        st.markdown("### Objective")
        st.write("Connect LiteVNA -> Calibrate -> Measure Material -> Calculate epsilon' and epsilon'' -> Save Experiment")
        st.caption("Advanced RF analysis, inverse modelling, and full-wave simulation remain available under Advanced Tools.")

    render_workflow_header()

    current_page = st.session_state["workflow_page"]
    if current_page == "Home":
        render_home_page()
    elif current_page == "Connect LiteVNA":
        render_connect_litevna_page()
    elif current_page == "Calibration Wizard":
        render_calibration_wizard_page(reference_names)
    elif current_page == "Sensor Setup":
        render_sensor_setup_page()
    elif current_page == "Measure Material":
        render_measure_material_page(material_db, runnable_plugins)
    elif current_page == "Permittivity Results":
        render_permittivity_results_page(material_db)
    elif current_page == "Research Mode":
        render_research_mode_page(experiment_db, material_db)
    elif current_page == "Advanced Tools":
        render_advanced_tools_page(
            selected_plugin=st.session_state["selected_permittivity_method"],
            reference_names=reference_names,
            forward_models=forward_models,
            inverse_solvers=inverse_solvers,
            plugins=plugins,
            runnable_plugins=runnable_plugins,
            experiment_db=experiment_db,
            material_db=material_db,
        )


if __name__ == "__main__":
    main()
