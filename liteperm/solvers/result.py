"""Simulation-result model shared by full-wave solver adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from liteperm.inverse.common import ForwardSimulation, LayerStack
from liteperm.models.core import MaterialSpectrum, MeasurementData
from liteperm.transform.network import gamma_to_admittance, gamma_to_impedance
from liteperm.utils.constants import DEFAULT_Z0


@dataclass(slots=True)
class SimulationResult:
    frequency_hz: np.ndarray
    s11: np.ndarray
    s21: np.ndarray | None = None
    impedance: np.ndarray | None = None
    admittance: np.ndarray | None = None
    solver_metadata: dict[str, Any] = field(default_factory=dict)
    runtime_seconds: float | None = None
    error_messages: list[str] = field(default_factory=list)
    output_files: dict[str, str] = field(default_factory=dict)
    touchstone_export_path: str = ""
    csv_export_path: str = ""
    z0: float = DEFAULT_Z0

    def __post_init__(self) -> None:
        self.frequency_hz = np.asarray(self.frequency_hz, dtype=float)
        self.s11 = np.asarray(self.s11, dtype=complex)
        self.s21 = None if self.s21 is None else np.asarray(self.s21, dtype=complex)
        if self.frequency_hz.ndim != 1 or self.s11.ndim != 1:
            raise ValueError("Simulation frequency and S11 arrays must be one-dimensional.")
        if self.frequency_hz.size != self.s11.size:
            raise ValueError("Simulation frequency and S11 arrays must have matching lengths.")
        if self.frequency_hz.size == 0:
            raise ValueError("Simulation results cannot be empty.")

        if self.impedance is None:
            impedance = None
        else:
            impedance = np.asarray(self.impedance, dtype=complex)
        if impedance is None or impedance.size != self.s11.size:
            self.impedance = gamma_to_impedance(self.s11, z0=self.z0)
        else:
            self.impedance = impedance

        if self.admittance is None:
            admittance = None
        else:
            admittance = np.asarray(self.admittance, dtype=complex)
        if admittance is None or admittance.size != self.s11.size:
            self.admittance = gamma_to_admittance(self.s11, z0=self.z0)
        else:
            self.admittance = admittance

    @property
    def measurement(self) -> MeasurementData:
        return MeasurementData(
            frequency_hz=self.frequency_hz.copy(),
            s11=self.s11.copy(),
            z0=self.z0,
            source_name=self.solver_metadata.get("source_name", f"{self.solver_metadata.get('solver_name', 'full-wave')} simulation"),
            metadata=dict(self.solver_metadata),
        )

    @classmethod
    def from_measurement(
        cls,
        measurement: MeasurementData,
        *,
        solver_metadata: dict[str, Any] | None = None,
        runtime_seconds: float | None = None,
        error_messages: list[str] | None = None,
        output_files: dict[str, str] | None = None,
        touchstone_export_path: str = "",
        csv_export_path: str = "",
    ) -> "SimulationResult":
        return cls(
            frequency_hz=measurement.frequency_hz.copy(),
            s11=measurement.s11.copy(),
            solver_metadata=solver_metadata or {},
            runtime_seconds=runtime_seconds,
            error_messages=error_messages or [],
            output_files=output_files or {},
            touchstone_export_path=touchstone_export_path,
            csv_export_path=csv_export_path,
            z0=measurement.z0,
        )

    def to_dataframe(self) -> pd.DataFrame:
        frame = self.measurement.to_dataframe()
        frame["impedance_real_ohm"] = self.impedance.real
        frame["impedance_imag_ohm"] = self.impedance.imag
        frame["admittance_real_s"] = self.admittance.real
        frame["admittance_imag_s"] = self.admittance.imag
        if self.s21 is not None:
            frame["s21_real"] = self.s21.real
            frame["s21_imag"] = self.s21.imag
        return frame

    def to_material_spectrum(self) -> MaterialSpectrum:
        epsilon_real = float(self.solver_metadata.get("effective_epsilon_real", 1.0))
        epsilon_imag = float(self.solver_metadata.get("effective_epsilon_imag", 0.0))
        conductivity = float(self.solver_metadata.get("effective_conductivity_s_per_m", 0.0))
        loss_tangent = abs(epsilon_imag) / max(abs(epsilon_real), 1e-9)
        return MaterialSpectrum(
            frequency_hz=self.frequency_hz.copy(),
            epsilon_complex=np.full_like(self.frequency_hz, complex(epsilon_real, -abs(epsilon_imag)), dtype=complex),
            impedance=self.impedance.copy(),
            admittance=self.admittance.copy(),
            gamma=self.s11.copy(),
            conductivity_s_per_m=np.full_like(self.frequency_hz, conductivity, dtype=float),
            loss_tangent=np.full_like(self.frequency_hz, loss_tangent, dtype=float),
            method=self.solver_metadata.get("solver_name", "full_wave"),
            metadata=dict(self.solver_metadata),
        )

    def to_forward_simulation(self, *, layer_stack: LayerStack | None = None) -> ForwardSimulation:
        if layer_stack is not None:
            effective_epsilon = layer_stack.effective_epsilon()
        else:
            effective_epsilon = complex(
                float(self.solver_metadata.get("effective_epsilon_real", 1.0)),
                -abs(float(self.solver_metadata.get("effective_epsilon_imag", 0.0))),
            )
        predicted_resonant_frequency_hz = float(
            self.solver_metadata.get(
                "predicted_resonant_frequency_hz",
                self.frequency_hz[int(np.argmin(np.abs(self.s11)))],
            )
        )
        return ForwardSimulation(
            frequency_hz=self.frequency_hz.copy(),
            s11=self.s11.copy(),
            impedance=self.impedance.copy(),
            admittance=self.admittance.copy(),
            predicted_resonant_frequency_hz=predicted_resonant_frequency_hz,
            effective_permittivity_complex=np.full_like(self.frequency_hz, effective_epsilon, dtype=complex),
            electric_field_distribution=self.solver_metadata.get("electric_field_distribution", {}),
            metadata=dict(self.solver_metadata),
            z0=self.z0,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency_hz": self.frequency_hz.astype(float).tolist(),
            "s11_real": self.s11.real.astype(float).tolist(),
            "s11_imag": self.s11.imag.astype(float).tolist(),
            "s21_real": None if self.s21 is None else self.s21.real.astype(float).tolist(),
            "s21_imag": None if self.s21 is None else self.s21.imag.astype(float).tolist(),
            "impedance_real": self.impedance.real.astype(float).tolist(),
            "impedance_imag": self.impedance.imag.astype(float).tolist(),
            "admittance_real": self.admittance.real.astype(float).tolist(),
            "admittance_imag": self.admittance.imag.astype(float).tolist(),
            "solver_metadata": self.solver_metadata,
            "runtime_seconds": self.runtime_seconds,
            "error_messages": self.error_messages,
            "output_files": self.output_files,
            "touchstone_export_path": self.touchstone_export_path,
            "csv_export_path": self.csv_export_path,
            "z0": float(self.z0),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SimulationResult":
        s21_real = payload.get("s21_real")
        s21_imag = payload.get("s21_imag")
        s21 = None
        if s21_real is not None and s21_imag is not None:
            s21 = np.asarray(s21_real, dtype=float) + 1j * np.asarray(s21_imag, dtype=float)
        return cls(
            frequency_hz=np.asarray(payload.get("frequency_hz", []), dtype=float),
            s11=np.asarray(payload.get("s11_real", []), dtype=float) + 1j * np.asarray(payload.get("s11_imag", []), dtype=float),
            s21=s21,
            impedance=np.asarray(payload.get("impedance_real", []), dtype=float) + 1j * np.asarray(payload.get("impedance_imag", []), dtype=float),
            admittance=np.asarray(payload.get("admittance_real", []), dtype=float) + 1j * np.asarray(payload.get("admittance_imag", []), dtype=float),
            solver_metadata=payload.get("solver_metadata", {}),
            runtime_seconds=payload.get("runtime_seconds"),
            error_messages=payload.get("error_messages", []),
            output_files=payload.get("output_files", {}),
            touchstone_export_path=payload.get("touchstone_export_path", ""),
            csv_export_path=payload.get("csv_export_path", ""),
            z0=float(payload.get("z0", DEFAULT_Z0)),
        )
