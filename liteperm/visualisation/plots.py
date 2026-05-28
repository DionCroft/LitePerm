"""Interactive and static plotting utilities."""

from __future__ import annotations

import matplotlib
import numpy as np
import plotly.graph_objects as go

from liteperm.models.core import MaterialSpectrum, MeasurementData


matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _frequency_axis(frequency_hz: np.ndarray) -> np.ndarray:
    return np.asarray(frequency_hz, dtype=float) / 1e9


def _base_figure(title: str, y_axis_title: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        template="plotly_dark",
        title=title,
        xaxis_title="Frequency (GHz)",
        yaxis_title=y_axis_title,
        legend_title="Trace",
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure


def build_magnitude_plot(measurement: MeasurementData) -> go.Figure:
    figure = _base_figure("S11 Magnitude", "Magnitude (dB)")
    figure.add_trace(
        go.Scatter(x=_frequency_axis(measurement.frequency_hz), y=measurement.magnitude_db, mode="lines", name="|S11| (dB)")
    )
    return figure


def build_phase_plot(measurement: MeasurementData) -> go.Figure:
    figure = _base_figure("S11 Phase", "Phase (deg)")
    figure.add_trace(
        go.Scatter(x=_frequency_axis(measurement.frequency_hz), y=measurement.phase_deg, mode="lines", name="Phase")
    )
    return figure


def build_smith_chart(measurement: MeasurementData) -> go.Figure:
    theta = np.linspace(0, 2 * np.pi, 361)
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(x=np.cos(theta), y=np.sin(theta), mode="lines", name="Unit Circle", line=dict(color="#4db6ff", dash="dot"))
    )
    figure.add_trace(
        go.Scatter(x=measurement.s11.real, y=measurement.s11.imag, mode="lines+markers", name="S11", line=dict(color="#5cd2c6"))
    )
    figure.update_layout(
        template="plotly_dark",
        title="Smith Chart",
        xaxis_title="Real(Γ)",
        yaxis_title="Imag(Γ)",
        xaxis=dict(scaleanchor="y"),
        yaxis=dict(constrain="domain"),
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure


def build_epsilon_plot(spectrum: MaterialSpectrum) -> go.Figure:
    figure = _base_figure(f"Dielectric Spectrum ({spectrum.method})", "Relative Permittivity")
    frequency_axis = _frequency_axis(spectrum.frequency_hz)
    figure.add_trace(go.Scatter(x=frequency_axis, y=spectrum.epsilon_prime, mode="lines", name="epsilon'"))
    figure.add_trace(go.Scatter(x=frequency_axis, y=spectrum.epsilon_double_prime, mode="lines", name="epsilon''"))
    return figure


def build_loss_tangent_plot(spectrum: MaterialSpectrum) -> go.Figure:
    figure = _base_figure("Loss Tangent and Conductivity", "Value")
    frequency_axis = _frequency_axis(spectrum.frequency_hz)
    figure.add_trace(go.Scatter(x=frequency_axis, y=spectrum.loss_tangent, mode="lines", name="Loss Tangent"))
    figure.add_trace(go.Scatter(x=frequency_axis, y=spectrum.conductivity_s_per_m, mode="lines", name="Conductivity (S/m)", yaxis="y2"))
    figure.update_layout(
        yaxis2=dict(title="Conductivity (S/m)", overlaying="y", side="right", showgrid=False),
    )
    return figure


def build_impedance_plot(spectrum: MaterialSpectrum) -> go.Figure:
    figure = _base_figure("Impedance", "Impedance (Ohm)")
    frequency_axis = _frequency_axis(spectrum.frequency_hz)
    figure.add_trace(go.Scatter(x=frequency_axis, y=spectrum.impedance.real, mode="lines", name="Re(Z)"))
    figure.add_trace(go.Scatter(x=frequency_axis, y=spectrum.impedance.imag, mode="lines", name="Im(Z)"))
    return figure


def build_admittance_plot(spectrum: MaterialSpectrum) -> go.Figure:
    figure = _base_figure("Admittance", "Admittance (S)")
    frequency_axis = _frequency_axis(spectrum.frequency_hz)
    figure.add_trace(go.Scatter(x=frequency_axis, y=spectrum.admittance.real, mode="lines", name="Re(Y)"))
    figure.add_trace(go.Scatter(x=frequency_axis, y=spectrum.admittance.imag, mode="lines", name="Im(Y)"))
    return figure


def build_nyquist_plot(spectrum: MaterialSpectrum) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=spectrum.epsilon_prime,
            y=spectrum.epsilon_double_prime,
            mode="lines+markers",
            name="Nyquist",
            line=dict(color="#5cd2c6"),
        )
    )
    figure.update_layout(
        template="plotly_dark",
        title="Permittivity Nyquist Plot",
        xaxis_title="epsilon'",
        yaxis_title="epsilon''",
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure


def build_static_spectrum_preview(spectrum: MaterialSpectrum) -> plt.Figure:
    frequency_axis = _frequency_axis(spectrum.frequency_hz)
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.plot(frequency_axis, spectrum.epsilon_prime, label="epsilon'")
    axis.plot(frequency_axis, spectrum.epsilon_double_prime, label="epsilon''")
    axis.set_title("Dielectric Spectrum Preview")
    axis.set_xlabel("Frequency (GHz)")
    axis.set_ylabel("Relative Permittivity")
    axis.grid(True, alpha=0.25)
    axis.legend()
    figure.tight_layout()
    return figure


def build_static_measurement_preview(measurement: MeasurementData) -> plt.Figure:
    frequency_axis = _frequency_axis(measurement.frequency_hz)
    figure, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    axes[0].plot(frequency_axis, measurement.magnitude_db, label="|S11| (dB)")
    axes[0].set_ylabel("Magnitude (dB)")
    axes[0].grid(True, alpha=0.25)
    axes[1].plot(frequency_axis, measurement.phase_deg, label="Phase", color="tab:orange")
    axes[1].set_xlabel("Frequency (GHz)")
    axes[1].set_ylabel("Phase (deg)")
    axes[1].grid(True, alpha=0.25)
    figure.tight_layout()
    return figure
