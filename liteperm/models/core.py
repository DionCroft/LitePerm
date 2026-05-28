"""Core data models used across the LitePerm application."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from liteperm.utils.constants import DEFAULT_Z0, NUMERIC_EPSILON


@dataclass(slots=True)
class MeasurementData:
    frequency_hz: np.ndarray
    s11: np.ndarray
    z0: float = DEFAULT_Z0
    source_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.frequency_hz = np.asarray(self.frequency_hz, dtype=float)
        self.s11 = np.asarray(self.s11, dtype=complex)
        if self.frequency_hz.ndim != 1 or self.s11.ndim != 1:
            raise ValueError("Measurement arrays must be one-dimensional.")
        if self.frequency_hz.size != self.s11.size:
            raise ValueError("Frequency and S11 arrays must have the same length.")
        if self.frequency_hz.size == 0:
            raise ValueError("Measurement arrays cannot be empty.")

    @property
    def magnitude(self) -> np.ndarray:
        return np.abs(self.s11)

    @property
    def magnitude_db(self) -> np.ndarray:
        return 20.0 * np.log10(np.maximum(self.magnitude, NUMERIC_EPSILON))

    @property
    def phase_deg(self) -> np.ndarray:
        return np.rad2deg(np.angle(self.s11))

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "frequency_hz": self.frequency_hz,
                "s11_real": self.s11.real,
                "s11_imag": self.s11.imag,
                "s11_magnitude": self.magnitude,
                "s11_db": self.magnitude_db,
                "s11_phase_deg": self.phase_deg,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency_hz": self.frequency_hz.astype(float).tolist(),
            "s11_real": self.s11.real.astype(float).tolist(),
            "s11_imag": self.s11.imag.astype(float).tolist(),
            "z0": float(self.z0),
            "source_name": self.source_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MeasurementData":
        real = np.asarray(payload.get("s11_real", []), dtype=float)
        imag = np.asarray(payload.get("s11_imag", []), dtype=float)
        return cls(
            frequency_hz=np.asarray(payload.get("frequency_hz", []), dtype=float),
            s11=real + 1j * imag,
            z0=float(payload.get("z0", DEFAULT_Z0)),
            source_name=payload.get("source_name", ""),
            metadata=payload.get("metadata", {}),
        )

    def copy_with_s11(
        self,
        s11: np.ndarray,
        *,
        source_name: str | None = None,
        metadata_update: dict[str, Any] | None = None,
    ) -> "MeasurementData":
        updated_metadata = dict(self.metadata)
        if metadata_update:
            updated_metadata.update(metadata_update)
        return MeasurementData(
            frequency_hz=self.frequency_hz.copy(),
            s11=np.asarray(s11, dtype=complex),
            z0=self.z0,
            source_name=source_name or self.source_name,
            metadata=updated_metadata,
        )


@dataclass(slots=True)
class OnePortErrorTerms:
    frequency_hz: np.ndarray
    directivity: np.ndarray
    reflection_tracking: np.ndarray
    source_match: np.ndarray


@dataclass(slots=True)
class CalibrationProfile:
    name: str
    open_gamma: complex = complex(1.0, 0.0)
    short_gamma: complex = complex(-1.0, 0.0)
    load_gamma: complex = complex(0.0, 0.0)
    reference_materials: list[str] = field(default_factory=list)
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "actual_standards": {
                "open_gamma": self.open_gamma,
                "short_gamma": self.short_gamma,
                "load_gamma": self.load_gamma,
            },
            "reference_materials": self.reference_materials,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CalibrationProfile":
        standards = payload.get("actual_standards", {})
        return cls(
            name=payload.get("name", "Imported Calibration"),
            open_gamma=_complex_from_any(standards.get("open_gamma", complex(1.0, 0.0))),
            short_gamma=_complex_from_any(standards.get("short_gamma", complex(-1.0, 0.0))),
            load_gamma=_complex_from_any(standards.get("load_gamma", complex(0.0, 0.0))),
            reference_materials=payload.get("reference_materials", []),
            notes=payload.get("notes", ""),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class SensorGeometryProfile:
    name: str
    sensor_type: str
    parameters: dict[str, float | str]
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: float | str | None = None) -> float | str | None:
        return self.parameters.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sensor_type": self.sensor_type,
            "parameters": self.parameters,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SensorGeometryProfile":
        return cls(
            name=payload.get("name", "Imported Geometry"),
            sensor_type=payload.get("sensor_type", "generic_resonator"),
            parameters=payload.get("parameters", {}),
            notes=payload.get("notes", ""),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class MaterialSpectrum:
    frequency_hz: np.ndarray
    epsilon_complex: np.ndarray
    impedance: np.ndarray
    admittance: np.ndarray
    gamma: np.ndarray
    conductivity_s_per_m: np.ndarray
    loss_tangent: np.ndarray
    method: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.frequency_hz = np.asarray(self.frequency_hz, dtype=float)
        self.epsilon_complex = np.asarray(self.epsilon_complex, dtype=complex)
        self.impedance = np.asarray(self.impedance, dtype=complex)
        self.admittance = np.asarray(self.admittance, dtype=complex)
        self.gamma = np.asarray(self.gamma, dtype=complex)
        self.conductivity_s_per_m = np.asarray(self.conductivity_s_per_m, dtype=float)
        self.loss_tangent = np.asarray(self.loss_tangent, dtype=float)

    @property
    def epsilon_prime(self) -> np.ndarray:
        return self.epsilon_complex.real

    @property
    def epsilon_double_prime(self) -> np.ndarray:
        return -self.epsilon_complex.imag

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "frequency_hz": self.frequency_hz,
                "epsilon_prime": self.epsilon_prime,
                "epsilon_double_prime": self.epsilon_double_prime,
                "loss_tangent": self.loss_tangent,
                "conductivity_s_per_m": self.conductivity_s_per_m,
                "gamma_real": self.gamma.real,
                "gamma_imag": self.gamma.imag,
                "impedance_real_ohm": self.impedance.real,
                "impedance_imag_ohm": self.impedance.imag,
                "admittance_real_s": self.admittance.real,
                "admittance_imag_s": self.admittance.imag,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency_hz": self.frequency_hz.astype(float).tolist(),
            "epsilon_real": self.epsilon_complex.real.astype(float).tolist(),
            "epsilon_imag": self.epsilon_complex.imag.astype(float).tolist(),
            "impedance_real": self.impedance.real.astype(float).tolist(),
            "impedance_imag": self.impedance.imag.astype(float).tolist(),
            "admittance_real": self.admittance.real.astype(float).tolist(),
            "admittance_imag": self.admittance.imag.astype(float).tolist(),
            "gamma_real": self.gamma.real.astype(float).tolist(),
            "gamma_imag": self.gamma.imag.astype(float).tolist(),
            "conductivity_s_per_m": self.conductivity_s_per_m.astype(float).tolist(),
            "loss_tangent": self.loss_tangent.astype(float).tolist(),
            "method": self.method,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MaterialSpectrum":
        return cls(
            frequency_hz=np.asarray(payload.get("frequency_hz", []), dtype=float),
            epsilon_complex=np.asarray(payload.get("epsilon_real", []), dtype=float)
            + 1j * np.asarray(payload.get("epsilon_imag", []), dtype=float),
            impedance=np.asarray(payload.get("impedance_real", []), dtype=float)
            + 1j * np.asarray(payload.get("impedance_imag", []), dtype=float),
            admittance=np.asarray(payload.get("admittance_real", []), dtype=float)
            + 1j * np.asarray(payload.get("admittance_imag", []), dtype=float),
            gamma=np.asarray(payload.get("gamma_real", []), dtype=float)
            + 1j * np.asarray(payload.get("gamma_imag", []), dtype=float),
            conductivity_s_per_m=np.asarray(payload.get("conductivity_s_per_m", []), dtype=float),
            loss_tangent=np.asarray(payload.get("loss_tangent", []), dtype=float),
            method=payload.get("method", "Unknown"),
            metadata=payload.get("metadata", {}),
        )


@dataclass(frozen=True, slots=True)
class MethodInfo:
    key: str
    display_name: str
    description: str
    assumptions: str
    validation_status: str = "experimental"


@dataclass(slots=True)
class SweepConfig:
    start_frequency_hz: float
    stop_frequency_hz: float
    points: int = 201
    output_power: int = 0
    sweep_speed: str = "normal"
    average_count: int = 1
    channel: str = "S11"

    @property
    def step_hz(self) -> float:
        if self.points <= 1:
            return 0.0
        return (self.stop_frequency_hz - self.start_frequency_hz) / (self.points - 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_frequency_hz": float(self.start_frequency_hz),
            "stop_frequency_hz": float(self.stop_frequency_hz),
            "points": int(self.points),
            "output_power": int(self.output_power),
            "sweep_speed": self.sweep_speed,
            "average_count": int(self.average_count),
            "channel": self.channel,
        }


@dataclass(slots=True)
class DeviceInfo:
    name: str
    port: str = ""
    firmware_version: str = "unknown"
    hardware_revision: str = "unknown"
    protocol_version: str = "unknown"
    frequency_min_hz: float = 1e6
    frequency_max_hz: float = 6.3e9
    max_points: int = 65535
    capabilities: list[str] = field(default_factory=list)
    is_simulated: bool = False
    manufacturer: str = ""
    serial_number: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "port": self.port,
            "firmware_version": self.firmware_version,
            "hardware_revision": self.hardware_revision,
            "protocol_version": self.protocol_version,
            "frequency_min_hz": float(self.frequency_min_hz),
            "frequency_max_hz": float(self.frequency_max_hz),
            "max_points": int(self.max_points),
            "capabilities": self.capabilities,
            "is_simulated": self.is_simulated,
            "manufacturer": self.manufacturer,
            "serial_number": self.serial_number,
        }


@dataclass(slots=True)
class ExperimentMetadata:
    experiment_name: str
    researcher: str
    project_name: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    temperature_c: float | None = None
    humidity_percent: float | None = None
    sensor_type: str = ""
    calibration_profile_name: str = ""
    geometry_profile_name: str = ""
    frequency_range_hz: tuple[float, float] = (0.0, 0.0)
    material_under_test: str = ""
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    device_name: str = ""
    device_port: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_name": self.experiment_name,
            "researcher": self.researcher,
            "project_name": self.project_name,
            "description": self.description,
            "created_at": self.created_at,
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
            "sensor_type": self.sensor_type,
            "calibration_profile_name": self.calibration_profile_name,
            "geometry_profile_name": self.geometry_profile_name,
            "frequency_range_hz": [float(self.frequency_range_hz[0]), float(self.frequency_range_hz[1])],
            "material_under_test": self.material_under_test,
            "notes": self.notes,
            "tags": self.tags,
            "device_name": self.device_name,
            "device_port": self.device_port,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExperimentMetadata":
        frequency_range = payload.get("frequency_range_hz", [0.0, 0.0])
        return cls(
            experiment_name=payload.get("experiment_name", "Untitled Experiment"),
            researcher=payload.get("researcher", ""),
            project_name=payload.get("project_name", "Default Project"),
            description=payload.get("description", ""),
            created_at=payload.get("created_at", datetime.now(UTC).isoformat()),
            temperature_c=payload.get("temperature_c"),
            humidity_percent=payload.get("humidity_percent"),
            sensor_type=payload.get("sensor_type", ""),
            calibration_profile_name=payload.get("calibration_profile_name", ""),
            geometry_profile_name=payload.get("geometry_profile_name", ""),
            frequency_range_hz=(float(frequency_range[0]), float(frequency_range[1])),
            material_under_test=payload.get("material_under_test", ""),
            notes=payload.get("notes", ""),
            tags=payload.get("tags", []),
            device_name=payload.get("device_name", ""),
            device_port=payload.get("device_port", ""),
        )


@dataclass(slots=True)
class ExperimentRecord:
    experiment_id: str
    metadata: ExperimentMetadata
    raw_measurement: MeasurementData
    processed_measurement: MeasurementData
    spectrum: MaterialSpectrum
    calibration_profile: CalibrationProfile
    geometry_profile: SensorGeometryProfile
    project_directory: str
    plot_manifest: dict[str, str] = field(default_factory=dict)
    report_manifest: dict[str, str] = field(default_factory=dict)
    inverse_result: dict[str, Any] | None = None
    digital_twin: dict[str, Any] | None = None

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "experiment_name": self.metadata.experiment_name,
            "researcher": self.metadata.researcher,
            "project_name": self.metadata.project_name,
            "sensor_type": self.metadata.sensor_type,
            "material_under_test": self.metadata.material_under_test,
            "created_at": self.metadata.created_at,
            "tags": ", ".join(self.metadata.tags),
            "project_directory": self.project_directory,
            "has_inverse_result": self.inverse_result is not None,
            "has_digital_twin": self.digital_twin is not None,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "metadata": self.metadata.to_dict(),
            "raw_measurement": self.raw_measurement.to_dict(),
            "processed_measurement": self.processed_measurement.to_dict(),
            "spectrum": self.spectrum.to_dict(),
            "calibration_profile": self.calibration_profile.to_dict(),
            "geometry_profile": self.geometry_profile.to_dict(),
            "project_directory": self.project_directory,
            "plot_manifest": self.plot_manifest,
            "report_manifest": self.report_manifest,
            "inverse_result": self.inverse_result,
            "digital_twin": self.digital_twin,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExperimentRecord":
        return cls(
            experiment_id=payload["experiment_id"],
            metadata=ExperimentMetadata.from_dict(payload.get("metadata", {})),
            raw_measurement=MeasurementData.from_dict(payload.get("raw_measurement", {})),
            processed_measurement=MeasurementData.from_dict(payload.get("processed_measurement", {})),
            spectrum=MaterialSpectrum.from_dict(payload.get("spectrum", {})),
            calibration_profile=CalibrationProfile.from_dict(payload.get("calibration_profile", {})),
            geometry_profile=SensorGeometryProfile.from_dict(payload.get("geometry_profile", {})),
            project_directory=payload.get("project_directory", ""),
            plot_manifest=payload.get("plot_manifest", {}),
            report_manifest=payload.get("report_manifest", {}),
            inverse_result=payload.get("inverse_result"),
            digital_twin=payload.get("digital_twin"),
        )


@dataclass(slots=True)
class AcquisitionResult:
    device_info: DeviceInfo
    sweep_config: SweepConfig
    raw_measurement: MeasurementData
    processed_measurement: MeasurementData
    spectrum: MaterialSpectrum
    calibration_profile: CalibrationProfile
    geometry_profile: SensorGeometryProfile
    plugin_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_info": self.device_info.to_dict(),
            "sweep_config": self.sweep_config.to_dict(),
            "raw_measurement": self.raw_measurement.to_dict(),
            "processed_measurement": self.processed_measurement.to_dict(),
            "spectrum": self.spectrum.to_dict(),
            "calibration_profile": self.calibration_profile.to_dict(),
            "geometry_profile": self.geometry_profile.to_dict(),
            "plugin_name": self.plugin_name,
        }


def _complex_from_any(value: Any) -> complex:
    if isinstance(value, complex):
        return value
    if isinstance(value, dict):
        return complex(float(value.get("real", 0.0)), float(value.get("imag", 0.0)))
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return complex(float(value[0]), float(value[1]))
    return complex(value)
