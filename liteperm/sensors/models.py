"""Concrete sensor models used for research workflows."""

from __future__ import annotations

from liteperm.calibration.profiles import build_calibration_profile
from liteperm.models.core import CalibrationProfile, SensorGeometryProfile
from liteperm.sensors.base import SensorModel


class PatchAntennaSensorModel(SensorModel):
    @property
    def sensor_family(self) -> str:
        return "Patch Antenna"


class OpenEndedCoaxProbeSensorModel(SensorModel):
    @property
    def sensor_family(self) -> str:
        return "Open Ended Coaxial Probe"


class MicrostripResonatorSensorModel(SensorModel):
    @property
    def sensor_family(self) -> str:
        return "Microstrip Resonator"


class CSRRSensorModel(SensorModel):
    @property
    def sensor_family(self) -> str:
        return "CSRR Structure"


def build_sensor_model(
    geometry: SensorGeometryProfile,
    *,
    calibration: CalibrationProfile | None = None,
    frequency_range_hz: tuple[float, float] = (1e6, 6.3e9),
    measurement_method: str = "reflection",
) -> SensorModel:
    calibration = calibration or build_calibration_profile("Default OSL")
    substrate = str(
        geometry.parameters.get("substrate_material")
        or geometry.parameters.get("substrate_permittivity")
        or geometry.parameters.get("cable_permittivity")
        or "unknown"
    )

    mapping: dict[str, type[SensorModel]] = {
        "patch_antenna": PatchAntennaSensorModel,
        "open_ended_coax_probe": OpenEndedCoaxProbeSensorModel,
        "microstrip_resonator": MicrostripResonatorSensorModel,
        "csrr_structure": CSRRSensorModel,
    }
    model_class = mapping.get(geometry.sensor_type, MicrostripResonatorSensorModel)
    return model_class(
        geometry=geometry,
        substrate=substrate,
        calibration=calibration,
        frequency_range_hz=frequency_range_hz,
        measurement_method=measurement_method,
    )

