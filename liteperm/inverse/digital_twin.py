"""Digital twin helpers for inverse-modelling workflows."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from liteperm.inverse.common import DigitalTwin, LayerStack
from liteperm.models.core import CalibrationProfile, MeasurementData, SensorGeometryProfile


def build_digital_twin(
    *,
    geometry_profile: SensorGeometryProfile,
    calibration_profile: CalibrationProfile,
    layer_stack: LayerStack,
    measurement: MeasurementData,
    inverse_result: dict | None = None,
    environment_state: dict | None = None,
) -> DigitalTwin:
    return DigitalTwin(
        twin_id=f"TWIN-{uuid.uuid4().hex[:12]}",
        sensor_name=geometry_profile.name,
        sensor_type=geometry_profile.sensor_type,
        geometry_snapshot=geometry_profile.to_dict(),
        calibration_snapshot=calibration_profile.to_dict(),
        layer_stack=layer_stack.to_dict(),
        environment_state=environment_state or {},
        latest_measurement_summary={
            "source_name": measurement.source_name,
            "frequency_min_hz": float(measurement.frequency_hz.min()),
            "frequency_max_hz": float(measurement.frequency_hz.max()),
            "sample_count": int(measurement.frequency_hz.size),
        },
        latest_inverse_result=inverse_result,
        updated_at=datetime.now(UTC).isoformat(),
    )

