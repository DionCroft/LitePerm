from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from liteperm.calibration.profiles import build_calibration_profile, calibration_profile_to_yaml
from liteperm.geometry.profiles import DEFAULT_GEOMETRIES, build_geometry_profile, geometry_profile_to_yaml
from liteperm.io.exporters import figure_to_image_bytes, spectrum_to_csv_bytes
from liteperm.io.parsers import load_measurement
from liteperm.models.core import CalibrationProfile, MeasurementData, SensorGeometryProfile
from liteperm.models.permittivity_methods import METHOD_REGISTRY
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


def initialise_state() -> None:
    defaults: dict[str, Any] = {
        "measurement": None,
        "open_measurement": None,
        "short_measurement": None,
        "load_measurement": None,
        "calibration_profile": build_calibration_profile("Default OSL"),
        "geometry_profile": build_geometry_profile("open_ended_coax_probe"),
        "last_spectrum": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def parse_uploaded_measurement(uploaded_file) -> MeasurementData:
    return load_measurement(BytesIO(uploaded_file.getvalue()), filename=uploaded_file.name)


def render_measurement_summary(measurement: MeasurementData) -> None:
    start_ghz = measurement.frequency_hz.min() / 1e9
    stop_ghz = measurement.frequency_hz.max() / 1e9
    span_ghz = stop_ghz - start_ghz

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Samples", f"{measurement.frequency_hz.size}")
    metric_2.metric("Start", f"{start_ghz:.4f} GHz")
    metric_3.metric("Stop", f"{stop_ghz:.4f} GHz")
    metric_4.metric("Span", f"{span_ghz:.4f} GHz")


def render_figure_export(figure, prefix: str) -> None:
    export_format = st.selectbox("Figure export format", ["png", "svg"], key=f"{prefix}_export_format")
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
    sensor_type = st.selectbox(
        "Sensor type",
        options=list(DEFAULT_GEOMETRIES),
        index=list(DEFAULT_GEOMETRIES).index(current_profile.sensor_type),
        format_func=lambda item: item.replace("_", " ").title(),
    )
    base_parameters = dict(DEFAULT_GEOMETRIES[sensor_type])
    base_parameters.update(current_profile.parameters if current_profile.sensor_type == sensor_type else {})

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


def render_method_reference() -> None:
    cards = st.columns(len(METHOD_REGISTRY))
    for column, method in zip(cards, METHOD_REGISTRY.values(), strict=True):
        with column:
            st.markdown(f"### {method.info.display_name}")
            st.caption(method.info.validation_status.title())
            st.write(method.info.description)
            st.write(method.info.assumptions)


def load_example_dataset(example_name: str) -> None:
    if example_name == "None":
        return
    st.session_state["measurement"] = load_measurement(EXAMPLE_ROOT / example_name)


def main() -> None:
    st.set_page_config(page_title="LitePerm", layout="wide")
    initialise_state()

    st.title("LitePerm")
    st.caption("LiteVNA-based dielectric spectroscopy and RF sensing dashboard")

    methods = list(METHOD_REGISTRY)
    reference_materials = load_reference_materials()
    reference_names = list_reference_material_names()

    with st.sidebar:
        st.header("Configuration")
        selected_method = st.selectbox(
            "Permittivity method",
            options=methods,
            index=methods.index("stuchly"),
            format_func=lambda item: METHOD_REGISTRY[item].info.display_name,
        )
        apply_calibration = st.checkbox("Apply loaded OSL calibration", value=True)
        st.info(
            "v0.1.0 includes a modular research baseline. "
            "Marsland and Komarov are experimental placeholders for future validated models."
        )
        st.markdown("[Demo workflow](examples/demo_workflow.md)")
        st.markdown("[Developer guide](docs/developer_guide.md)")

    raw_tab, calibration_tab, geometry_tab, material_tab, modelling_tab = st.tabs(
        ["Raw Measurement", "Calibration", "Sensor Geometry", "Material Properties", "Advanced Modelling"]
    )

    with raw_tab:
        st.subheader("Import S11 data")
        uploader_column, example_column = st.columns([2, 1])
        with uploader_column:
            uploaded_file = st.file_uploader("Import Touchstone or CSV", type=["s1p", "csv"], key="dut_upload")
            if uploaded_file is not None:
                try:
                    st.session_state["measurement"] = parse_uploaded_measurement(uploaded_file)
                except Exception as error:
                    st.error(f"Failed to import measurement: {error}")
        with example_column:
            example_name = st.selectbox(
                "Load example data",
                options=["None", "sample_touchstone.s1p", "sample_litevna.csv"],
                key="example_dataset_name",
            )
            if st.button("Load example dataset", key="load_example_button"):
                load_example_dataset(example_name)

        measurement = st.session_state["measurement"]
        if measurement is None:
            st.warning("Import a LiteVNA S11 file to begin.")
        else:
            render_measurement_summary(measurement)
            st.write(f"Loaded source: `{measurement.source_name}`")

            plot_column_1, plot_column_2 = st.columns(2)
            with plot_column_1:
                st.plotly_chart(build_magnitude_plot(measurement), use_container_width=True)
                st.plotly_chart(build_phase_plot(measurement), use_container_width=True)
            with plot_column_2:
                smith_chart = build_smith_chart(measurement)
                st.plotly_chart(smith_chart, use_container_width=True)
                render_figure_export(smith_chart, "raw_smith_chart")

            with st.expander("Measurement table"):
                st.dataframe(measurement.to_dataframe(), use_container_width=True)

    with calibration_tab:
        st.subheader("Open / Short / Load calibration")
        st.write("Upload one-port standards measured over the same sweep as the DUT.")

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

        calibration_profile = calibration_editor(reference_names, st.session_state["calibration_profile"])
        st.session_state["calibration_profile"] = calibration_profile

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
        updated_geometry = geometry_editor(st.session_state["geometry_profile"])
        st.session_state["geometry_profile"] = updated_geometry

        geometry_yaml = geometry_profile_to_yaml(updated_geometry)
        st.download_button(
            "Download geometry YAML",
            data=geometry_yaml,
            file_name="geometry_profile.yaml",
            mime="application/x-yaml",
        )
        st.code(geometry_yaml, language="yaml")

    with material_tab:
        st.subheader("Material properties")
        measurement = st.session_state["measurement"]
        if measurement is None:
            st.warning("Import a measurement in the Raw Measurement tab before computing dielectric spectra.")
        else:
            calibration_profile = st.session_state["calibration_profile"]
            open_measurement = st.session_state["open_measurement"]
            short_measurement = st.session_state["short_measurement"]
            load_measurement = st.session_state["load_measurement"]

            can_calibrate = all(item is not None for item in [open_measurement, short_measurement, load_measurement])
            if apply_calibration and not can_calibrate:
                st.info("Calibration is enabled, but one or more OSL standards are missing, so raw S11 will be used.")

            spectrum, working_measurement = compute_material_spectrum(
                measurement,
                st.session_state["geometry_profile"],
                method=selected_method,
                calibration_profile=calibration_profile if apply_calibration and can_calibrate else None,
                open_measurement=open_measurement if apply_calibration and can_calibrate else None,
                short_measurement=short_measurement if apply_calibration and can_calibrate else None,
                load_measurement=load_measurement if apply_calibration and can_calibrate else None,
            )
            st.session_state["last_spectrum"] = spectrum

            metrics = st.columns(4)
            metrics[0].metric("Mean epsilon'", f"{spectrum.epsilon_prime.mean():.3f}")
            metrics[1].metric("Mean epsilon''", f"{spectrum.epsilon_double_prime.mean():.3f}")
            metrics[2].metric("Peak loss tangent", f"{spectrum.loss_tangent.max():.3f}")
            metrics[3].metric("Peak conductivity", f"{spectrum.conductivity_s_per_m.max():.3f} S/m")

            st.write(f"Working measurement: `{working_measurement.source_name or 'Imported measurement'}`")
            epsilon_figure = build_epsilon_plot(spectrum)
            st.plotly_chart(epsilon_figure, use_container_width=True)

            lower_left, lower_right = st.columns(2)
            with lower_left:
                st.plotly_chart(build_loss_tangent_plot(spectrum), use_container_width=True)
                st.plotly_chart(build_nyquist_plot(spectrum), use_container_width=True)
            with lower_right:
                st.plotly_chart(build_impedance_plot(spectrum), use_container_width=True)
                st.plotly_chart(build_admittance_plot(spectrum), use_container_width=True)
                render_figure_export(epsilon_figure, "dielectric_spectrum")

            st.download_button(
                "Download dielectric spectrum CSV",
                data=spectrum_to_csv_bytes(spectrum),
                file_name="liteperm_spectrum.csv",
                mime="text/csv",
            )

            with st.expander("Spectrum table"):
                st.dataframe(spectrum.to_dataframe(), use_container_width=True)

    with modelling_tab:
        st.subheader("Advanced modelling")
        render_method_reference()

        comparison_rows: list[dict[str, Any]] = []
        measurement = st.session_state["measurement"]
        if measurement is not None:
            for method_key, method in METHOD_REGISTRY.items():
                spectrum, _ = compute_material_spectrum(
                    measurement,
                    st.session_state["geometry_profile"],
                    method=method_key,
                )
                comparison_rows.append(
                    {
                        "Method": method.info.display_name,
                        "Validation": method.info.validation_status,
                        "Mean epsilon'": float(spectrum.epsilon_prime.mean()),
                        "Mean epsilon''": float(spectrum.epsilon_double_prime.mean()),
                        "Peak loss tangent": float(spectrum.loss_tangent.max()),
                    }
                )
            st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True)

        st.markdown("### Future machine-learning interfaces")
        st.write(
            "The package already includes abstract interfaces for feature extraction, material classification, "
            "and anomaly detection so supervised and unsupervised models can be added without changing the dashboard pipeline."
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {"Pipeline": "Random Forest", "Status": "Interface ready", "Use case": "Tabular dielectric features"},
                    {"Pipeline": "SVM", "Status": "Interface ready", "Use case": "Small labelled datasets"},
                    {"Pipeline": "CNN", "Status": "Interface ready", "Use case": "Spectral-shape learning"},
                    {"Pipeline": "Anomaly Detection", "Status": "Interface ready", "Use case": "Novel material alerts"},
                ]
            ),
            use_container_width=True,
        )

        st.markdown("### Selected reference materials")
        selected_reference_rows = []
        for material_name in st.session_state["calibration_profile"].reference_materials:
            payload = get_reference_material_by_name(material_name)
            if payload:
                selected_reference_rows.append(payload)
        if selected_reference_rows:
            st.dataframe(pd.DataFrame(selected_reference_rows), use_container_width=True)
        else:
            st.caption("No reference materials selected in the current calibration profile.")


if __name__ == "__main__":
    main()
