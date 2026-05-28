"""Device integration helpers."""

from liteperm.devices.device_base import DeviceBase, DeviceConnectionError
from liteperm.devices.future_device import FutureDevice
from liteperm.devices.litevna import LiteVNADevice


def discover_device_candidates():
    devices = LiteVNADevice.discover()
    devices.extend(FutureDevice.discover())
    return devices


def create_device(device_kind: str, *, port: str = "") -> DeviceBase:
    key = device_kind.lower()
    if key == "litevna":
        return LiteVNADevice(port=port or None)
    if key == "future_device":
        return FutureDevice(port=port or "SIMULATED")
    raise KeyError(f"Unsupported device kind: {device_kind}")


__all__ = ["DeviceBase", "DeviceConnectionError", "FutureDevice", "LiteVNADevice", "create_device", "discover_device_candidates"]

