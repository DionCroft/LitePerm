"""JSON serialisation helpers for dataclasses and NumPy-backed payloads."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

import numpy as np


def _normalise(value: Any) -> Any:
    if is_dataclass(value):
        return _normalise(asdict(value))
    if isinstance(value, dict):
        return {str(key): _normalise(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def dumps_json(value: Any, *, indent: int | None = None) -> str:
    return json.dumps(_normalise(value), indent=indent, sort_keys=False)


def loads_json(value: str) -> Any:
    return json.loads(value)
