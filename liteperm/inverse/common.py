"""Shared dataclasses and helpers for inverse electromagnetic modelling."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from liteperm.models.core import MeasurementData
from liteperm.transform.network import gamma_to_admittance, gamma_to_impedance
from liteperm.utils.constants import DEFAULT_Z0


@dataclass(slots=True)
class LayerDefinition:
    name: str
    material_name: str
    thickness_m: float
    epsilon_real: float
    epsilon_imag: float = 0.0
    conductivity_s_per_m: float = 0.0
    loss_tangent: float = 0.0
    role: str = "material"
    mutable: bool = True

    @property
    def epsilon_complex(self) -> complex:
        return complex(self.epsilon_real, -abs(self.epsilon_imag))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "material_name": self.material_name,
            "thickness_m": float(self.thickness_m),
            "epsilon_real": float(self.epsilon_real),
            "epsilon_imag": float(self.epsilon_imag),
            "conductivity_s_per_m": float(self.conductivity_s_per_m),
            "loss_tangent": float(self.loss_tangent),
            "role": self.role,
            "mutable": bool(self.mutable),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LayerDefinition":
        return cls(
            name=payload.get("name", "layer"),
            material_name=payload.get("material_name", payload.get("name", "material")),
            thickness_m=float(payload.get("thickness_m", 0.0)),
            epsilon_real=float(payload.get("epsilon_real", 1.0)),
            epsilon_imag=float(payload.get("epsilon_imag", 0.0)),
            conductivity_s_per_m=float(payload.get("conductivity_s_per_m", 0.0)),
            loss_tangent=float(payload.get("loss_tangent", 0.0)),
            role=payload.get("role", "material"),
            mutable=bool(payload.get("mutable", True)),
        )


@dataclass(slots=True)
class LayerStack:
    layers: list[LayerDefinition] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def total_thickness_m(self) -> float:
        return float(sum(max(layer.thickness_m, 0.0) for layer in self.layers))

    def effective_epsilon(self, *, decay_length_m: float | None = None) -> complex:
        if not self.layers:
            return complex(1.0, 0.0)
        weights = []
        cumulative_depth = 0.0
        decay_length_m = decay_length_m or max(self.total_thickness_m(), 1e-6)
        for layer in self.layers:
            local_weight = max(layer.thickness_m, 1e-6) * np.exp(-cumulative_depth / max(decay_length_m, 1e-9))
            if layer.role in {"ground", "metal"}:
                local_weight *= 0.05
            weights.append(local_weight)
            cumulative_depth += max(layer.thickness_m, 0.0)
        weights_array = np.asarray(weights, dtype=float)
        weights_array /= max(weights_array.sum(), 1e-12)
        epsilon_values = np.asarray([layer.epsilon_complex for layer in self.layers], dtype=complex)
        return complex(np.sum(weights_array * epsilon_values))

    def get_layer(self, role: str) -> LayerDefinition | None:
        return next((layer for layer in self.layers if layer.role == role), None)

    def to_dict(self) -> dict[str, Any]:
        return {"layers": [layer.to_dict() for layer in self.layers], "metadata": self.metadata}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LayerStack":
        return cls(
            layers=[LayerDefinition.from_dict(item) for item in payload.get("layers", [])],
            metadata=payload.get("metadata", {}),
        )


@dataclass(frozen=True, slots=True)
class ParameterDefinition:
    name: str
    target_path: str
    lower_bound: float
    upper_bound: float
    initial_value: float
    description: str = ""
    scale: str = "linear"
    fixed: bool = False


@dataclass(slots=True)
class ForwardSimulation:
    frequency_hz: np.ndarray
    s11: np.ndarray
    impedance: np.ndarray
    admittance: np.ndarray
    predicted_resonant_frequency_hz: float
    effective_permittivity_complex: np.ndarray
    electric_field_distribution: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    z0: float = DEFAULT_Z0

    def __post_init__(self) -> None:
        self.frequency_hz = np.asarray(self.frequency_hz, dtype=float)
        self.s11 = np.asarray(self.s11, dtype=complex)
        self.impedance = np.asarray(self.impedance, dtype=complex)
        self.admittance = np.asarray(self.admittance, dtype=complex)
        self.effective_permittivity_complex = np.asarray(self.effective_permittivity_complex, dtype=complex)

    @property
    def measurement(self) -> MeasurementData:
        return MeasurementData(
            frequency_hz=self.frequency_hz.copy(),
            s11=self.s11.copy(),
            z0=self.z0,
            source_name="Forward Simulation",
            metadata=self.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency_hz": self.frequency_hz.astype(float).tolist(),
            "s11_real": self.s11.real.astype(float).tolist(),
            "s11_imag": self.s11.imag.astype(float).tolist(),
            "impedance_real": self.impedance.real.astype(float).tolist(),
            "impedance_imag": self.impedance.imag.astype(float).tolist(),
            "admittance_real": self.admittance.real.astype(float).tolist(),
            "admittance_imag": self.admittance.imag.astype(float).tolist(),
            "predicted_resonant_frequency_hz": float(self.predicted_resonant_frequency_hz),
            "effective_permittivity_real": self.effective_permittivity_complex.real.astype(float).tolist(),
            "effective_permittivity_imag": self.effective_permittivity_complex.imag.astype(float).tolist(),
            "electric_field_distribution": self.electric_field_distribution,
            "metadata": self.metadata,
            "z0": float(self.z0),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ForwardSimulation":
        return cls(
            frequency_hz=np.asarray(payload.get("frequency_hz", []), dtype=float),
            s11=np.asarray(payload.get("s11_real", []), dtype=float) + 1j * np.asarray(payload.get("s11_imag", []), dtype=float),
            impedance=np.asarray(payload.get("impedance_real", []), dtype=float)
            + 1j * np.asarray(payload.get("impedance_imag", []), dtype=float),
            admittance=np.asarray(payload.get("admittance_real", []), dtype=float)
            + 1j * np.asarray(payload.get("admittance_imag", []), dtype=float),
            predicted_resonant_frequency_hz=float(payload.get("predicted_resonant_frequency_hz", 0.0)),
            effective_permittivity_complex=np.asarray(payload.get("effective_permittivity_real", []), dtype=float)
            + 1j * np.asarray(payload.get("effective_permittivity_imag", []), dtype=float),
            electric_field_distribution=payload.get("electric_field_distribution", {}),
            metadata=payload.get("metadata", {}),
            z0=float(payload.get("z0", DEFAULT_Z0)),
        )


@dataclass(slots=True)
class InverseProblem:
    measured_measurement: MeasurementData
    forward_model_name: str
    parameter_definitions: list[ParameterDefinition]
    error_metric: str = "weighted_error"
    solver_options: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def bounds(self) -> list[tuple[float, float]]:
        return [(parameter.lower_bound, parameter.upper_bound) for parameter in self.parameter_definitions if not parameter.fixed]

    def initial_vector(self) -> np.ndarray:
        return np.asarray([parameter.initial_value for parameter in self.parameter_definitions if not parameter.fixed], dtype=float)

    def parameter_names(self) -> list[str]:
        return [parameter.name for parameter in self.parameter_definitions if not parameter.fixed]


@dataclass(slots=True)
class UncertaintySummary:
    best_estimate: dict[str, float]
    confidence_intervals: dict[str, tuple[float, float]]
    parameter_distributions: dict[str, list[float]]
    correlation_matrix: list[list[float]]
    method: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "best_estimate": self.best_estimate,
            "confidence_intervals": {key: [float(value[0]), float(value[1])] for key, value in self.confidence_intervals.items()},
            "parameter_distributions": self.parameter_distributions,
            "correlation_matrix": self.correlation_matrix,
            "method": self.method,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "UncertaintySummary":
        return cls(
            best_estimate={key: float(value) for key, value in payload.get("best_estimate", {}).items()},
            confidence_intervals={
                key: (float(value[0]), float(value[1]))
                for key, value in payload.get("confidence_intervals", {}).items()
            },
            parameter_distributions={
                key: [float(item) for item in values]
                for key, values in payload.get("parameter_distributions", {}).items()
            },
            correlation_matrix=[[float(item) for item in row] for row in payload.get("correlation_matrix", [])],
            method=payload.get("method", "unknown"),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class SensitivityResult:
    baseline_error: float
    ranking: list[dict[str, float]]
    heatmap: dict[str, list[float]]
    tornado: dict[str, list[float]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.ranking)

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_error": float(self.baseline_error),
            "ranking": self.ranking,
            "heatmap": self.heatmap,
            "tornado": self.tornado,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SensitivityResult":
        return cls(
            baseline_error=float(payload.get("baseline_error", 0.0)),
            ranking=payload.get("ranking", []),
            heatmap={
                key: [float(item) for item in values]
                for key, values in payload.get("heatmap", {}).items()
            },
            tornado={
                key: [float(item) for item in values]
                for key, values in payload.get("tornado", {}).items()
            },
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class ParameterSweepResult:
    sweep_table: pd.DataFrame
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"sweep_table": self.sweep_table.to_dict(orient="records"), "metadata": self.metadata}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ParameterSweepResult":
        return cls(
            sweep_table=pd.DataFrame(payload.get("sweep_table", [])),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class ValidationReport:
    benchmark_name: str
    cases: list[dict[str, Any]]
    summary_metrics: dict[str, float]
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_name": self.benchmark_name,
            "cases": self.cases,
            "summary_metrics": self.summary_metrics,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ValidationReport":
        return cls(
            benchmark_name=payload.get("benchmark_name", "Validation Report"),
            cases=payload.get("cases", []),
            summary_metrics={key: float(value) for key, value in payload.get("summary_metrics", {}).items()},
            generated_at=payload.get("generated_at", datetime.now(UTC).isoformat()),
        )


@dataclass(slots=True)
class InverseResult:
    solver_name: str
    error_metric: str
    best_parameters: dict[str, float]
    objective_value: float
    predicted_simulation: ForwardSimulation
    residual_measurement: MeasurementData
    objective_history: list[float] = field(default_factory=list)
    parameter_history: list[dict[str, float]] = field(default_factory=list)
    convergence_trace: list[dict[str, float]] = field(default_factory=list)
    uncertainty_summary: UncertaintySummary | None = None
    sensitivity_result: SensitivityResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "solver_name": self.solver_name,
            "error_metric": self.error_metric,
            "best_parameters": self.best_parameters,
            "objective_value": float(self.objective_value),
            "predicted_simulation": self.predicted_simulation.to_dict(),
            "residual_measurement": self.residual_measurement.to_dict(),
            "objective_history": self.objective_history,
            "parameter_history": self.parameter_history,
            "convergence_trace": self.convergence_trace,
            "uncertainty_summary": self.uncertainty_summary.to_dict() if self.uncertainty_summary else None,
            "sensitivity_result": self.sensitivity_result.to_dict() if self.sensitivity_result else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InverseResult":
        uncertainty_summary_payload = payload.get("uncertainty_summary")
        sensitivity_result_payload = payload.get("sensitivity_result")
        return cls(
            solver_name=payload.get("solver_name", "Unknown Solver"),
            error_metric=payload.get("error_metric", "weighted_error"),
            best_parameters={key: float(value) for key, value in payload.get("best_parameters", {}).items()},
            objective_value=float(payload.get("objective_value", 0.0)),
            predicted_simulation=ForwardSimulation.from_dict(payload.get("predicted_simulation", {})),
            residual_measurement=MeasurementData.from_dict(payload.get("residual_measurement", {})),
            objective_history=[float(item) for item in payload.get("objective_history", [])],
            parameter_history=payload.get("parameter_history", []),
            convergence_trace=payload.get("convergence_trace", []),
            uncertainty_summary=UncertaintySummary.from_dict(uncertainty_summary_payload) if uncertainty_summary_payload else None,
            sensitivity_result=SensitivityResult.from_dict(sensitivity_result_payload) if sensitivity_result_payload else None,
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class DigitalTwin:
    twin_id: str
    sensor_name: str
    sensor_type: str
    geometry_snapshot: dict[str, Any]
    calibration_snapshot: dict[str, Any]
    layer_stack: dict[str, Any]
    environment_state: dict[str, Any]
    latest_measurement_summary: dict[str, Any]
    latest_inverse_result: dict[str, Any] | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "sensor_name": self.sensor_name,
            "sensor_type": self.sensor_type,
            "geometry_snapshot": self.geometry_snapshot,
            "calibration_snapshot": self.calibration_snapshot,
            "layer_stack": self.layer_stack,
            "environment_state": self.environment_state,
            "latest_measurement_summary": self.latest_measurement_summary,
            "latest_inverse_result": self.latest_inverse_result,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DigitalTwin":
        return cls(
            twin_id=payload.get("twin_id", ""),
            sensor_name=payload.get("sensor_name", ""),
            sensor_type=payload.get("sensor_type", ""),
            geometry_snapshot=payload.get("geometry_snapshot", {}),
            calibration_snapshot=payload.get("calibration_snapshot", {}),
            layer_stack=payload.get("layer_stack", {}),
            environment_state=payload.get("environment_state", {}),
            latest_measurement_summary=payload.get("latest_measurement_summary", {}),
            latest_inverse_result=payload.get("latest_inverse_result"),
            updated_at=payload.get("updated_at", datetime.now(UTC).isoformat()),
            metadata=payload.get("metadata", {}),
        )


def simulation_to_measurement(simulation: ForwardSimulation, *, source_name: str = "Predicted S11") -> MeasurementData:
    return MeasurementData(
        frequency_hz=simulation.frequency_hz.copy(),
        s11=simulation.s11.copy(),
        z0=simulation.z0,
        source_name=source_name,
        metadata=dict(simulation.metadata),
    )


def residual_measurement(measured: MeasurementData, predicted: MeasurementData) -> MeasurementData:
    return MeasurementData(
        frequency_hz=measured.frequency_hz.copy(),
        s11=measured.s11 - predicted.s11,
        z0=measured.z0,
        source_name="Residual S11",
        metadata={"measured_source": measured.source_name, "predicted_source": predicted.source_name},
    )


def clone_with_parameter_updates(model: Any, parameter_updates: dict[str, float]) -> Any:
    cloned = copy.deepcopy(model)
    for path, value in parameter_updates.items():
        set_nested_value(cloned, path, value)
    return cloned


def set_nested_value(target: Any, path: str, value: float) -> None:
    current = target
    parts = path.split(".")
    for part in parts[:-1]:
        if part.isdigit():
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            current = getattr(current, part)
    final = parts[-1]
    if final.isdigit():
        current[int(final)] = value
    elif isinstance(current, dict):
        current[final] = value
    else:
        setattr(current, final, value)


def parameter_mapping(definitions: list[ParameterDefinition], vector: np.ndarray) -> dict[str, float]:
    values = {}
    index = 0
    for definition in definitions:
        if definition.fixed:
            values[definition.target_path] = float(definition.initial_value)
            continue
        values[definition.target_path] = float(vector[index])
        index += 1
    return values


def inverse_result_to_spectrum(result: InverseResult):
    predicted = result.predicted_simulation.measurement
    gamma = predicted.s11
    impedance = gamma_to_impedance(gamma, z0=predicted.z0)
    admittance = gamma_to_admittance(gamma, z0=predicted.z0)
    return predicted, impedance, admittance
