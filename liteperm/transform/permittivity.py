"""Pipeline for converting S11 measurements into dielectric spectra."""

from __future__ import annotations

from liteperm.calibration.one_port import apply_one_port_calibration
from liteperm.models.core import CalibrationProfile, MaterialSpectrum, MeasurementData, SensorGeometryProfile
from liteperm.models.permittivity_methods import METHOD_REGISTRY
from liteperm.transform.network import gamma_to_admittance, gamma_to_impedance


def available_methods() -> list[str]:
    return list(METHOD_REGISTRY)


def compute_material_spectrum(
    measurement: MeasurementData,
    geometry: SensorGeometryProfile,
    *,
    method: str = "stuchly",
    calibration_profile: CalibrationProfile | None = None,
    open_measurement: MeasurementData | None = None,
    short_measurement: MeasurementData | None = None,
    load_measurement: MeasurementData | None = None,
) -> tuple[MaterialSpectrum, MeasurementData]:
    method_key = method.lower()
    if method_key not in METHOD_REGISTRY:
        raise KeyError(f"Unsupported permittivity method: {method}")

    working_measurement = measurement
    if calibration_profile and open_measurement and short_measurement and load_measurement:
        working_measurement, _ = apply_one_port_calibration(
            measurement,
            open_measurement,
            short_measurement,
            load_measurement,
            open_gamma=calibration_profile.open_gamma,
            short_gamma=calibration_profile.short_gamma,
            load_gamma=calibration_profile.load_gamma,
        )

    impedance = gamma_to_impedance(working_measurement.s11, z0=working_measurement.z0)
    admittance = gamma_to_admittance(working_measurement.s11, z0=working_measurement.z0)
    spectrum = METHOD_REGISTRY[method_key].estimate(
        frequency_hz=working_measurement.frequency_hz,
        gamma=working_measurement.s11,
        impedance=impedance,
        admittance=admittance,
        geometry=geometry,
    )
    return spectrum, working_measurement

