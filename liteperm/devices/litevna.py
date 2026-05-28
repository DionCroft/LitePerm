"""LiteVNA serial communication backend."""

from __future__ import annotations

import struct
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from liteperm.devices.device_base import DeviceBase, DeviceConnectionError
from liteperm.models.core import DeviceInfo, MeasurementData, SweepConfig
from liteperm.utils.constants import NUMERIC_EPSILON

try:  # pragma: no cover - optional runtime dependency
    import serial
    from serial.tools import list_ports
except Exception:  # pragma: no cover - optional runtime dependency
    serial = None
    list_ports = None


@dataclass(slots=True)
class _FifoPoint:
    fwd0: complex
    rev0: complex
    rev1: complex
    frequency_index: int


class LiteVNADevice(DeviceBase):
    READ = 0x10
    READ2 = 0x11
    READ4 = 0x12
    READ8 = 0x13
    READFIFO = 0x18
    WRITE = 0x20
    WRITE2 = 0x21
    WRITE4 = 0x22
    WRITE8 = 0x23
    INDICATE = 0x0D
    FIFO_CHUNK_POINTS = 128

    def __init__(self, *, port: str | None = None, baudrate: int = 115200, timeout: float = 1.5):
        super().__init__(port=port)
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Any = None
        self._sweep_config = SweepConfig(1e8, 6e9, 401, output_power=2, sweep_speed="normal", average_count=4)

    @classmethod
    def discover(cls) -> list[DeviceInfo]:
        if list_ports is None:  # pragma: no cover - optional runtime dependency
            return []

        discovered: list[DeviceInfo] = []
        for port_info in list_ports.comports():
            haystack = " ".join(
                str(value or "")
                for value in [port_info.device, port_info.description, port_info.manufacturer, port_info.product]
            ).lower()
            if "litevna" not in haystack and "cdc" not in haystack and "serial" not in haystack:
                continue
            discovered.append(
                DeviceInfo(
                    name="LiteVNA",
                    port=port_info.device,
                    firmware_version="unknown",
                    hardware_revision="unknown",
                    protocol_version="1",
                    frequency_min_hz=50e3,
                    frequency_max_hz=6.3e9,
                    max_points=65535,
                    capabilities=["S11", "S21", "USB serial sweep capture"],
                    manufacturer=port_info.manufacturer or "",
                    serial_number=getattr(port_info, "serial_number", "") or "",
                )
            )
        return discovered

    def connect(self) -> None:
        if serial is None:  # pragma: no cover - optional runtime dependency
            raise DeviceConnectionError("pyserial is not installed. Install dependencies from requirements.txt.")
        if not self.port:
            raise DeviceConnectionError("No COM port has been selected for LiteVNA.")
        self._serial = serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)
        self._connected = True
        if not self.test_connection():
            self.disconnect()
            raise DeviceConnectionError("Connected serial port did not respond like a LiteVNA.")

    def disconnect(self) -> None:
        if self._serial is not None:
            self._serial.close()
        self._serial = None
        self._connected = False

    def _require_connection(self) -> None:
        if not self._connected or self._serial is None:
            raise DeviceConnectionError("LiteVNA is not connected.")

    def _write(self, payload: bytes) -> None:
        self._require_connection()
        self._serial.write(payload)
        self._serial.flush()

    def _read_exact(self, size: int) -> bytes:
        self._require_connection()
        transmission_time = (size * 10) / max(float(self.baudrate), 1.0)
        deadline = time.monotonic() + max(float(self.timeout), 0.25) + transmission_time + 0.5
        chunks = bytearray()

        while len(chunks) < size and time.monotonic() < deadline:
            remaining = size - len(chunks)
            payload = self._serial.read(remaining)
            if payload:
                chunks.extend(payload)
                continue
            time.sleep(0.01)

        if len(chunks) != size:
            raise DeviceConnectionError(f"Expected {size} bytes from LiteVNA, received {len(chunks)}.")
        return bytes(chunks)

    def _read_u1(self, address: int) -> int:
        self._write(bytes([self.READ, address]))
        return self._read_exact(1)[0]

    def _read_u2(self, address: int) -> int:
        self._write(bytes([self.READ2, address]))
        return int.from_bytes(self._read_exact(2), "little")

    def _read_u8(self, address: int) -> int:
        self._write(bytes([self.READ8, address]) + b"\x00" * 8)
        return int.from_bytes(self._read_exact(8), "little")

    def _write_u1(self, address: int, value: int) -> None:
        self._write(bytes([self.WRITE, address, value & 0xFF]))

    def _write_u2(self, address: int, value: int) -> None:
        self._write(bytes([self.WRITE2, address]) + int(value).to_bytes(2, "little", signed=False))

    def _write_u8(self, address: int, value: int) -> None:
        self._write(bytes([self.WRITE8, address]) + int(value).to_bytes(8, "little", signed=False))

    def test_connection(self) -> bool:
        self._require_connection()
        self._serial.reset_input_buffer()
        self._write(bytes([self.INDICATE]))
        try:
            response = self._read_exact(1)
        except DeviceConnectionError:
            return False
        return response == b"2"

    def get_device_info(self) -> DeviceInfo:
        if not self.is_connected:
            return DeviceInfo(
                name="LiteVNA",
                port=self.port or "",
                firmware_version="disconnected",
                protocol_version="1",
                frequency_min_hz=50e3,
                frequency_max_hz=6.3e9,
                max_points=65535,
                capabilities=["S11", "S21", "USB serial sweep capture"],
            )

        firmware_major = self._read_u1(0xF3)
        firmware_minor = self._read_u1(0xF4)
        hardware_revision = self._read_u1(0xF2)
        protocol_version = self._read_u1(0xF1)
        return DeviceInfo(
            name="LiteVNA",
            port=self.port or "",
            firmware_version=f"{firmware_major}.{firmware_minor}",
            hardware_revision=str(hardware_revision),
            protocol_version=str(protocol_version),
            frequency_min_hz=50e3,
            frequency_max_hz=6.3e9,
            max_points=65535,
            capabilities=["S11", "S21", "USB serial sweep capture"],
        )

    def configure_sweep(self, config: SweepConfig) -> None:
        self._sweep_config = config
        if not self.is_connected:
            return
        self._write_u8(0x00, int(config.start_frequency_hz))
        self._write_u8(0x10, int(config.step_hz))
        self._write_u2(0x20, int(config.points))
        self._write_u2(0x22, 1)
        self._write_u1(0x26, 0)
        self._write_u1(0x40, max(1, min(int(config.average_count), 80)))
        power = max(1, min(int(config.output_power or 1), 3))
        self._write_u1(0x41, power)
        self._write_u1(0x42, power)
        channel_select = {"s11": 0x01, "s21": 0x02, "both": 0x00}.get(config.channel.lower(), 0x01)
        self._write_u1(0x44, channel_select)

    def _clear_fifo(self) -> None:
        self._write_u1(0x30, 0)

    def _read_fifo_chunk(self, count: int) -> list[_FifoPoint]:
        self._write(bytes([self.READFIFO, 0x30, count & 0xFF]))
        payload = self._read_exact(count * 32)
        points: list[_FifoPoint] = []
        for index in range(count):
            chunk = payload[index * 32 : (index + 1) * 32]
            fwd0_re, fwd0_im, rev0_re, rev0_im, rev1_re, rev1_im, freq_index = struct.unpack("<iiiiiiH", chunk[:26])
            points.append(
                _FifoPoint(
                    fwd0=complex(fwd0_re, fwd0_im),
                    rev0=complex(rev0_re, rev0_im),
                    rev1=complex(rev1_re, rev1_im),
                    frequency_index=int(freq_index),
                )
            )
        return points

    def capture_sweep(self) -> MeasurementData:
        self._require_connection()
        config = self._sweep_config or SweepConfig(1e8, 6e9, 401)
        self.configure_sweep(config)
        self._clear_fifo()

        points: list[_FifoPoint] = []
        remaining = config.points
        while remaining > 0:
            chunk = min(self.FIFO_CHUNK_POINTS, remaining)
            points.extend(self._read_fifo_chunk(chunk))
            remaining -= chunk

        gamma = np.zeros(config.points, dtype=complex)
        for point in points:
            reference = point.fwd0 if abs(point.fwd0) > NUMERIC_EPSILON else complex(NUMERIC_EPSILON, 0.0)
            if 0 <= point.frequency_index < config.points:
                gamma[point.frequency_index] = point.rev0 / reference

        frequency_hz = config.start_frequency_hz + np.arange(config.points) * config.step_hz
        return MeasurementData(
            frequency_hz=frequency_hz,
            s11=gamma,
            source_name=f"LiteVNA live sweep ({self.port})",
            metadata={"device": "LiteVNA", "port": self.port, "sweep_config": config.to_dict()},
        )
