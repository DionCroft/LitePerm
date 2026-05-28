"""Filesystem paths used by LitePerm runtime services."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "liteperm"
DATABASE_ROOT = PACKAGE_ROOT / "database"
EXPERIMENT_DB_PATH = DATABASE_ROOT / "experiments.db"
MATERIAL_DB_PATH = DATABASE_ROOT / "materials.db"
PROFILES_ROOT = PROJECT_ROOT / "profiles"
CALIBRATION_LIBRARY_ROOT = PROFILES_ROOT / "calibrations"
GEOMETRY_LIBRARY_ROOT = PROFILES_ROOT / "geometries"
PROJECTS_ROOT = PROJECT_ROOT / "Projects"


def ensure_runtime_directories() -> None:
    for directory in [
        DATABASE_ROOT,
        PROFILES_ROOT,
        CALIBRATION_LIBRARY_ROOT,
        GEOMETRY_LIBRARY_ROOT,
        PROJECTS_ROOT,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

