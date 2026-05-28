"""Static resource loading utilities."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


RESOURCE_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_LIBRARY_PATH = RESOURCE_ROOT / "reference_materials.yaml"


@lru_cache(maxsize=1)
def load_reference_materials() -> dict[str, Any]:
    payload = yaml.safe_load(REFERENCE_LIBRARY_PATH.read_text(encoding="utf-8")) or {}
    return payload.get("materials", {})


def list_reference_material_names() -> list[str]:
    materials = load_reference_materials()
    return [entry.get("display_name", key) for key, entry in materials.items()]


def get_reference_material_by_name(name: str) -> dict[str, Any] | None:
    materials = load_reference_materials()
    for key, entry in materials.items():
        if key.lower() == name.lower() or entry.get("display_name", "").lower() == name.lower():
            return {"key": key, **entry}
    return None

