"""Export helpers for dielectric spectra, profiles, and figures."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

import pandas as pd

from liteperm.models.core import MaterialSpectrum
from liteperm.utils.yaml_io import dump_yaml


def spectrum_to_csv_bytes(spectrum: MaterialSpectrum) -> bytes:
    return spectrum.to_dataframe().to_csv(index=False).encode("utf-8")


def object_to_yaml_bytes(payload: Any) -> bytes:
    if is_dataclass(payload):
        return dump_yaml(asdict(payload)).encode("utf-8")
    return dump_yaml(payload).encode("utf-8")


def dataframe_to_csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def figure_to_image_bytes(figure: Any, *, format: str = "png") -> bytes:
    return figure.to_image(format=format, scale=2)

