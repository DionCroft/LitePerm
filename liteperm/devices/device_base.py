"""Common device interface for LitePerm acquisition backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from liteperm.models.core import DeviceInfo, MeasurementData, SweepConfig


class DeviceConnectionError(RuntimeError):
    """Raised when a device cannot be reached or does not respond as expected."""


class DeviceBase(ABC):
    def __init__(self, *, port: str | None = None):
        self.port = port
        self._connected = False
        self._sweep_config: SweepConfig | None = None

    @classmethod
    @abstractmethod
    def discover(cls) -> list[DeviceInfo]:
        """Return device candidates visible to the current host."""

    @abstractmethod
    def connect(self) -> None:
        """Open the device connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the device connection."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Return True if the connected device responds to a simple probe."""

    @abstractmethod
    def get_device_info(self) -> DeviceInfo:
        """Return current device information."""

    @abstractmethod
    def configure_sweep(self, config: SweepConfig) -> None:
        """Apply sweep parameters to the device."""

    @abstractmethod
    def capture_sweep(self) -> MeasurementData:
        """Capture one sweep worth of measurement data."""

    def start_sweep(self) -> None:
        self._connected = True

    def stop_sweep(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

