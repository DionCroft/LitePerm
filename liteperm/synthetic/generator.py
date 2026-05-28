"""Synthetic RF measurement generation utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from liteperm.inverse.common import LayerStack
from liteperm.inverse.forward_models import build_forward_model
from liteperm.models.core import MeasurementData, SensorGeometryProfile


@dataclass(slots=True)
class SyntheticNoiseConfig:
    noise_level: float = 0.01
    temperature_drift_fraction: float = 0.0
    cable_error_fraction: float = 0.0
    calibration_error_fraction: float = 0.0


def generate_synthetic_measurement(
    *,
    sensor_type: str,
    geometry: SensorGeometryProfile,
    layer_stack: LayerStack,
    frequency_hz: np.ndarray,
    noise_config: SyntheticNoiseConfig | None = None,
    seed: int = 0,
) -> tuple[MeasurementData, dict[str, object]]:
    noise_config = noise_config or SyntheticNoiseConfig()
    model = build_forward_model(sensor_type, geometry=geometry, layer_stack=layer_stack)
    simulation = model.simulate(frequency_hz)
    measurement = simulation.measurement
    rng = np.random.default_rng(seed)
    noisy_s11 = measurement.s11.copy()
    if noise_config.noise_level > 0:
        noisy_s11 += noise_config.noise_level * (rng.normal(size=noisy_s11.size) + 1j * rng.normal(size=noisy_s11.size))
    if noise_config.temperature_drift_fraction:
        noisy_s11 *= 1 + noise_config.temperature_drift_fraction * np.linspace(-0.5, 0.5, noisy_s11.size)
    if noise_config.cable_error_fraction:
        noisy_s11 *= np.exp(1j * noise_config.cable_error_fraction * np.linspace(0, np.pi / 4, noisy_s11.size))
    if noise_config.calibration_error_fraction:
        noisy_s11 += noise_config.calibration_error_fraction * 0.05
    return (
        MeasurementData(
            frequency_hz=measurement.frequency_hz,
            s11=noisy_s11,
            z0=measurement.z0,
            source_name="Synthetic Measurement",
            metadata={"synthetic": True, "noise_config": asdict(noise_config)},
        ),
        {"forward_model": model.metadata(), "reference_simulation": simulation.to_dict()},
    )


def generate_synthetic_dataset(
    *,
    sensor_type: str,
    geometry: SensorGeometryProfile,
    layer_stacks: list[LayerStack],
    frequency_hz: np.ndarray,
    noise_config: SyntheticNoiseConfig | None = None,
) -> pd.DataFrame:
    rows = []
    for index, layer_stack in enumerate(layer_stacks):
        measurement, metadata = generate_synthetic_measurement(
            sensor_type=sensor_type,
            geometry=geometry,
            layer_stack=layer_stack,
            frequency_hz=frequency_hz,
            noise_config=noise_config,
            seed=index,
        )
        rows.append(
            {
                "sample_id": index,
                "sensor_type": sensor_type,
                "mean_magnitude_db": float(np.mean(measurement.magnitude_db)),
                "min_magnitude_db": float(np.min(measurement.magnitude_db)),
                "layer_stack": layer_stack.to_dict(),
                "metadata": metadata,
            }
        )
    return pd.DataFrame(rows)
