"""Testable acquisition stages for live RF sensing workflows."""

from __future__ import annotations

from liteperm.devices.device_base import DeviceBase
from liteperm.models.core import AcquisitionResult, CalibrationProfile, MeasurementData, SensorGeometryProfile, SweepConfig
from liteperm.transform.permittivity import compute_material_spectrum


class AcquisitionPipeline:
    def __init__(self, device: DeviceBase):
        self.device = device

    def capture_raw_measurement(self, config: SweepConfig) -> MeasurementData:
        self.device.configure_sweep(config)
        return self.device.capture_sweep()

    def apply_transform(
        self,
        measurement: MeasurementData,
        geometry: SensorGeometryProfile,
        *,
        plugin_name: str,
        calibration_profile: CalibrationProfile,
        open_measurement: MeasurementData | None = None,
        short_measurement: MeasurementData | None = None,
        load_measurement: MeasurementData | None = None,
    ):
        return compute_material_spectrum(
            measurement,
            geometry,
            method=plugin_name,
            calibration_profile=calibration_profile,
            open_measurement=open_measurement,
            short_measurement=short_measurement,
            load_measurement=load_measurement,
        )

    def run(
        self,
        *,
        config: SweepConfig,
        geometry: SensorGeometryProfile,
        plugin_name: str,
        calibration_profile: CalibrationProfile,
        open_measurement: MeasurementData | None = None,
        short_measurement: MeasurementData | None = None,
        load_measurement: MeasurementData | None = None,
    ) -> AcquisitionResult:
        raw_measurement = self.capture_raw_measurement(config)
        spectrum, processed_measurement = self.apply_transform(
            raw_measurement,
            geometry,
            plugin_name=plugin_name,
            calibration_profile=calibration_profile,
            open_measurement=open_measurement,
            short_measurement=short_measurement,
            load_measurement=load_measurement,
        )
        return AcquisitionResult(
            device_info=self.device.get_device_info(),
            sweep_config=config,
            raw_measurement=raw_measurement,
            processed_measurement=processed_measurement,
            spectrum=spectrum,
            calibration_profile=calibration_profile,
            geometry_profile=geometry,
            plugin_name=plugin_name,
        )

