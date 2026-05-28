"""YAML serialisation helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import yaml


def _normalise_for_yaml(value: Any) -> Any:
    if is_dataclass(value):
        return _normalise_for_yaml(asdict(value))
    if isinstance(value, dict):
        return {str(key): _normalise_for_yaml(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise_for_yaml(item) for item in value]
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def dump_yaml(data: Any) -> str:
    return yaml.safe_dump(_normalise_for_yaml(data), sort_keys=False, allow_unicode=False)


def write_yaml(path: str | Path, data: Any) -> Path:
    target = Path(path)
    target.write_text(dump_yaml(data), encoding="utf-8")
    return target


def load_yaml(path: str | Path) -> Any:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))

