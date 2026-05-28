"""Plotly visualisations for inverse-modelling workflows."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from liteperm.inverse.common import InverseResult, LayerStack, ParameterSweepResult, SensitivityResult
from liteperm.models.core import MeasurementData


def _frequency_axis(frequency_hz: np.ndarray) -> np.ndarray:
    return np.asarray(frequency_hz, dtype=float) / 1e9


def build_measured_vs_predicted_plot(measured: MeasurementData, predicted: MeasurementData) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=_frequency_axis(measured.frequency_hz), y=measured.magnitude_db, mode="lines", name="Measured |S11|"))
    figure.add_trace(go.Scatter(x=_frequency_axis(predicted.frequency_hz), y=predicted.magnitude_db, mode="lines", name="Predicted |S11|"))
    figure.update_layout(template="plotly_dark", title="Measured vs Predicted S11", xaxis_title="Frequency (GHz)", yaxis_title="Magnitude (dB)")
    return figure


def build_smith_comparison_plot(measured: MeasurementData, predicted: MeasurementData) -> go.Figure:
    theta = np.linspace(0, 2 * np.pi, 361)
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=np.cos(theta), y=np.sin(theta), mode="lines", name="Unit Circle", line=dict(dash="dot")))
    figure.add_trace(go.Scatter(x=measured.s11.real, y=measured.s11.imag, mode="lines+markers", name="Measured"))
    figure.add_trace(go.Scatter(x=predicted.s11.real, y=predicted.s11.imag, mode="lines+markers", name="Predicted"))
    figure.update_layout(template="plotly_dark", title="Smith Chart Comparison", xaxis_title="Real(Gamma)", yaxis_title="Imag(Gamma)", xaxis=dict(scaleanchor="y"))
    return figure


def build_residual_plot(residual: MeasurementData) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=_frequency_axis(residual.frequency_hz), y=residual.magnitude_db, mode="lines", name="Residual magnitude"))
    figure.update_layout(template="plotly_dark", title="Residual Error Plot", xaxis_title="Frequency (GHz)", yaxis_title="Residual (dB-equivalent)")
    return figure


def build_convergence_plot(result: InverseResult) -> go.Figure:
    frame = pd.DataFrame(result.convergence_trace)
    figure = go.Figure()
    if not frame.empty:
        figure.add_trace(go.Scatter(x=frame["step"], y=frame["objective"], mode="lines+markers", name="Objective"))
    figure.update_layout(template="plotly_dark", title="Parameter Convergence Plot", xaxis_title="Iteration", yaxis_title="Objective")
    return figure


def build_confidence_interval_plot(result: InverseResult) -> go.Figure:
    figure = go.Figure()
    if result.uncertainty_summary is None:
        figure.update_layout(template="plotly_dark", title="Confidence Interval Plot", annotations=[dict(text="No uncertainty summary available", showarrow=False)])
        return figure
    for index, (parameter, interval) in enumerate(result.uncertainty_summary.confidence_intervals.items()):
        estimate = result.best_parameters.get(parameter, np.mean(interval))
        figure.add_trace(
            go.Scatter(
                x=[interval[0], interval[1]],
                y=[index, index],
                mode="lines+markers",
                name=parameter,
                marker=dict(size=[8, 8]),
                text=[f"{parameter} low", f"{parameter} high"],
            )
        )
        figure.add_trace(go.Scatter(x=[estimate], y=[index], mode="markers", name=f"{parameter} estimate"))
    figure.update_layout(template="plotly_dark", title="Confidence Interval Plot", xaxis_title="Parameter Value", yaxis_title="Parameter")
    return figure


def build_sensitivity_heatmap(result: SensitivityResult) -> go.Figure:
    parameters = list(result.heatmap)
    z_values = [result.heatmap[name] for name in parameters]
    figure = go.Figure(data=go.Heatmap(z=z_values, y=parameters, x=list(range(len(z_values[0])) if z_values else []), colorscale="Viridis"))
    figure.update_layout(template="plotly_dark", title="Sensitivity Heatmap", xaxis_title="Perturbation Step", yaxis_title="Parameter")
    return figure


def build_tornado_plot(result: SensitivityResult) -> go.Figure:
    frame = result.to_dataframe()
    figure = go.Figure()
    if not frame.empty:
        figure.add_trace(go.Bar(x=frame["influence"], y=frame["parameter"], orientation="h"))
    figure.update_layout(template="plotly_dark", title="Tornado Plot", xaxis_title="Influence", yaxis_title="Parameter")
    return figure


def build_parameter_space_3d(result: ParameterSweepResult) -> go.Figure:
    frame = result.sweep_table
    if frame.shape[1] < 3:
        return go.Figure(layout=dict(template="plotly_dark", title="3D Parameter Space Explorer"))
    parameter_columns = [column for column in frame.columns if column not in {"objective", "predicted_resonant_frequency_hz", "effective_epsilon_real"}]
    x_column = parameter_columns[0]
    y_column = parameter_columns[1] if len(parameter_columns) > 1 else parameter_columns[0]
    figure = go.Figure(
        data=go.Scatter3d(
            x=frame[x_column],
            y=frame[y_column],
            z=frame["objective"],
            mode="markers",
            marker=dict(size=4, color=frame["objective"], colorscale="Viridis"),
        )
    )
    figure.update_layout(template="plotly_dark", title="3D Parameter Space Explorer", scene=dict(xaxis_title=x_column, yaxis_title=y_column, zaxis_title="Objective"))
    return figure


def build_layer_stack_viewer(layer_stack: LayerStack) -> go.Figure:
    figure = go.Figure()
    cumulative = 0.0
    for layer in layer_stack.layers:
        figure.add_trace(
            go.Bar(
                x=[layer.thickness_m * 1e3],
                y=[layer.name],
                orientation="h",
                base=[cumulative * 1e3],
                name=layer.material_name,
                text=[f"epsilon'={layer.epsilon_real:.2f}"],
            )
        )
        cumulative += layer.thickness_m
    figure.update_layout(template="plotly_dark", barmode="stack", title="Interactive Layer Stack Viewer", xaxis_title="Thickness (mm)", yaxis_title="Layer")
    return figure

