"""Simulated future device used for local development and UI validation."""

from __future__ import annotations

import math

import numpy as np

from liteperm.devices.device_base import DeviceBase
from liteperm.models.core import DeviceInfo, MeasurementData, SweepConfig


class FutureDevice(DeviceBase):
    def __init__(self, *, port: str | None = "SIMULATED"):
        super().__init__(port=port)
        self._capture_counter = 0
        self._sweep_config = SweepConfig(1e8, 6e9, 401, output_power=2, sweep_speed="demo", average_count=2)

    @classmethod
    def discover(cls) -> list[DeviceInfo]:
        return [
            DeviceInfo(
                name="Simulated Future Device",
                port="SIMULATED",
                firmware_version="0.0-demo",
                hardware_revision="sim",
                protocol_version="virtual-1",
                capabilities=["S11", "synthetic-live-sweep", "demo-mode"],
                is_simulated=True,
                manufacturer="LitePerm",
            )
        ]

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def test_connection(self) -> bool:
        return True

    def get_device_info(self) -> DeviceInfo:
        return self.discover()[0]

    def configure_sweep(self, config: SweepConfig) -> None:
        self._sweep_config = config

    def capture_sweep(self) -> MeasurementData:
        config = self._sweep_config
        assert config is not None
        frequency_hz = np.linspace(config.start_frequency_hz, config.stop_frequency_hz, config.points)
        phase_shift = 0.03 * self._capture_counter
        magnitude = 0.88 - 0.78 * np.exp(-((frequency_hz - 2.45e9) ** 2) / (2 * (1.1e9**2)))
        magnitude += 0.03 * np.sin(np.linspace(0, 3 * math.pi, config.points) + phase_shift)
        phase_deg = -25.0 - 115.0 * (frequency_hz - frequency_hz.min()) / max(np.ptp(frequency_hz), 1.0)
        phase_deg += 4.0 * np.sin(np.linspace(0, 4 * math.pi, config.points) + phase_shift)
        gamma = np.clip(magnitude, 0.01, 0.99) * np.exp(1j * np.deg2rad(phase_deg))
        self._capture_counter += 1
        return MeasurementData(
            frequency_hz=frequency_hz,
            s11=gamma,
            source_name="Live sweep (simulated)",
            metadata={"device": "FutureDevice", "capture_index": self._capture_counter},
        )
