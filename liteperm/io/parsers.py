"""Measurement importers for Touchstone and CSV-based LiteVNA exports."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd

from liteperm.models.core import MeasurementData
from liteperm.utils.constants import DEFAULT_Z0, NUMERIC_EPSILON


_FREQUENCY_MULTIPLIERS = {
    "hz": 1.0,
    "khz": 1e3,
    "mhz": 1e6,
    "ghz": 1e9,
}


def _normalise_column_name(column_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", column_name.strip().lower()).strip("_")


def _read_text(source: str | Path | BinaryIO) -> str:
    if hasattr(source, "read"):
        payload = source.read()
        if isinstance(payload, bytes):
            return payload.decode("utf-8")
        return str(payload)
    return Path(source).read_text(encoding="utf-8")


def _source_name(source: str | Path | BinaryIO, filename: str | None = None) -> str:
    if filename:
        return filename
    if hasattr(source, "name"):
        return Path(str(source.name)).name
    return Path(str(source)).name


def parse_touchstone(source: str | Path | BinaryIO, *, filename: str | None = None) -> MeasurementData:
    text = _read_text(source)
    source_name = _source_name(source, filename)

    freq_multiplier = 1.0
    data_format = "ri"
    z0 = DEFAULT_Z0
    frequency: list[float] = []
    s11_values: list[complex] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("!"):
            continue
        if line.startswith("#"):
            tokens = line[1:].strip().lower().split()
            if tokens:
                freq_multiplier = _FREQUENCY_MULTIPLIERS.get(tokens[0], 1.0)
            if len(tokens) >= 3:
                data_format = tokens[2]
            if "r" in tokens:
                r_index = tokens.index("r")
                if r_index + 1 < len(tokens):
                    z0 = float(tokens[r_index + 1])
            continue

        fields = line.split()
        if len(fields) < 3:
            continue
        freq_value = float(fields[0]) * freq_multiplier
        value_one = float(fields[1])
        value_two = float(fields[2])

        if data_format == "ri":
            gamma = complex(value_one, value_two)
        elif data_format == "ma":
            gamma = value_one * np.exp(1j * np.deg2rad(value_two))
        elif data_format == "db":
            magnitude = 10 ** (value_one / 20.0)
            gamma = magnitude * np.exp(1j * np.deg2rad(value_two))
        else:
            raise ValueError(f"Unsupported Touchstone data format: {data_format}")

        frequency.append(freq_value)
        s11_values.append(gamma)

    if not frequency:
        raise ValueError("No Touchstone S11 data points were found.")

    return MeasurementData(
        frequency_hz=np.asarray(frequency, dtype=float),
        s11=np.asarray(s11_values, dtype=complex),
        z0=z0,
        source_name=source_name,
        metadata={"format": "touchstone"},
    )


def _guess_frequency_multiplier(column_name: str) -> float:
    tokens = set(column_name.split("_"))
    for suffix in ("ghz", "mhz", "khz", "hz"):
        if suffix in tokens or column_name.endswith(suffix):
            return _FREQUENCY_MULTIPLIERS[suffix]
    return 1.0


def _find_column(columns: list[str], *patterns: str) -> str | None:
    for column in columns:
        if all(pattern in column for pattern in patterns):
            return column
    return None


def parse_csv(source: str | Path | BinaryIO, *, filename: str | None = None) -> MeasurementData:
    if hasattr(source, "seek"):
        source.seek(0)
    frame = pd.read_csv(source if hasattr(source, "read") else Path(source))
    if frame.empty:
        raise ValueError("CSV import produced an empty table.")

    normalised_columns = {_normalise_column_name(column): column for column in frame.columns}
    frame = frame.rename(columns={original: normalised for normalised, original in normalised_columns.items()})

    frequency_column = next((column for column in frame.columns if "freq" in column), None)
    if frequency_column is None:
        raise ValueError("Could not find a frequency column in the CSV file.")

    frequency_multiplier = _guess_frequency_multiplier(frequency_column)
    frequency_hz = frame[frequency_column].astype(float).to_numpy() * frequency_multiplier

    real_column = _find_column(list(frame.columns), "s11", "real") or _find_column(list(frame.columns), "real")
    imag_column = _find_column(list(frame.columns), "s11", "imag") or _find_column(list(frame.columns), "imag")
    magnitude_column = (
        _find_column(list(frame.columns), "s11", "magnitude")
        or _find_column(list(frame.columns), "s11", "mag")
        or _find_column(list(frame.columns), "magnitude")
    )
    db_column = _find_column(list(frame.columns), "s11", "db") or _find_column(list(frame.columns), "db")
    phase_column = _find_column(list(frame.columns), "s11", "phase") or _find_column(list(frame.columns), "phase")

    if real_column and imag_column:
        s11 = frame[real_column].astype(float).to_numpy() + 1j * frame[imag_column].astype(float).to_numpy()
    elif (magnitude_column or db_column) and phase_column:
        if magnitude_column:
            magnitude = frame[magnitude_column].astype(float).to_numpy()
        else:
            magnitude = 10 ** (frame[db_column].astype(float).to_numpy() / 20.0)
        phase_deg = frame[phase_column].astype(float).to_numpy()
        s11 = magnitude * np.exp(1j * np.deg2rad(phase_deg))
    else:
        raise ValueError(
            "CSV import requires either real/imaginary columns or magnitude/phase columns for S11."
        )

    if np.any(np.abs(s11) > 1.5 + NUMERIC_EPSILON):
        raise ValueError("CSV S11 values appear invalid; ensure the export contains reflection coefficient data.")

    return MeasurementData(
        frequency_hz=frequency_hz,
        s11=s11,
        z0=DEFAULT_Z0,
        source_name=_source_name(source, filename),
        metadata={"format": "csv"},
    )


def load_measurement(source: str | Path | BinaryIO, *, filename: str | None = None) -> MeasurementData:
    name = _source_name(source, filename).lower()
    if name.endswith(".s1p"):
        if hasattr(source, "seek"):
            source.seek(0)
        return parse_touchstone(source, filename=filename)
    if name.endswith(".csv"):
        if hasattr(source, "seek"):
            source.seek(0)
        return parse_csv(source, filename=filename)
    raise ValueError("Unsupported file type. Please provide a .s1p or .csv measurement export.")
