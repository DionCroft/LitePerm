from liteperm.devices.future_device import FutureDevice
from liteperm.devices.litevna import LiteVNADevice
from liteperm.models.core import SweepConfig


def test_future_device_capture_returns_measurement():
    device = FutureDevice()
    device.connect()
    device.configure_sweep(SweepConfig(1e8, 2e9, 101))
    measurement = device.capture_sweep()
    device.disconnect()

    assert measurement.frequency_hz.size == 101
    assert measurement.source_name.startswith("Live sweep")


class _PartialReadSerial:
    def __init__(self, payload_chunks):
        self._payload_chunks = list(payload_chunks)

    def read(self, _size):
        if not self._payload_chunks:
            return b""
        return self._payload_chunks.pop(0)


def test_litevna_read_exact_accumulates_partial_reads():
    device = LiteVNADevice(port="COM1", timeout=0.2)
    device._connected = True
    device._serial = _PartialReadSerial([b"abc", b"de", b"f"])

    payload = device._read_exact(6)

    assert payload == b"abcdef"
